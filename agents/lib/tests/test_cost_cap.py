import boto3
import pytest
from moto import mock_aws

from agents.lib.cost_cap import OpusCapExceeded, OpusCostCap

BUCKET = "aicoe-vault-test"
TODAY = "2026-06-03"


def _cap(s3):
    s3.create_bucket(Bucket=BUCKET)
    return OpusCostCap(BUCKET, cap_usd=5.0, s3=s3, today=TODAY)


@mock_aws
def test_empty_file_first_call_works():
    s3 = boto3.client("s3", region_name="us-east-1")
    cap = _cap(s3)
    # No opus.json yet — pre_check treats spend as zero and passes.
    cap.pre_check(0.10)
    assert cap.remaining_usd() == 5.0


@mock_aws
def test_accumulates_across_calls():
    s3 = boto3.client("s3", region_name="us-east-1")
    cap = _cap(s3)
    cap.add_usage(tokens=1000, cost_usd=1.0)
    usage = cap.add_usage(tokens=1000, cost_usd=1.0)
    assert usage.tokens_consumed == 2000
    assert round(usage.cost_usd, 2) == 2.0
    assert round(cap.remaining_usd(), 2) == 3.0


@mock_aws
def test_over_cap_raises():
    s3 = boto3.client("s3", region_name="us-east-1")
    cap = _cap(s3)
    cap.add_usage(tokens=100_000, cost_usd=4.99)
    with pytest.raises(OpusCapExceeded):
        cap.pre_check(0.10)  # 4.99 + 0.10 > 5.00


@mock_aws
def test_cap_hit_marker_persisted():
    s3 = boto3.client("s3", region_name="us-east-1")
    cap = _cap(s3)
    usage = cap.add_usage(tokens=100_000, cost_usd=5.50)
    assert usage.cap_hit_at is not None
