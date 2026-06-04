#!/usr/bin/env python3
"""Create the S3 Vectors bucket + index out-of-band (idempotent).

S3 Vectors has no stable CloudFormation/CDK support yet, so this runs as a
deploy step (see deploy-dev workflow / README runbook). Names must match
``infra/stacks/config.py``.

    uv run python infra/scripts/create_vector_index.py --profile aicoe-dev
"""

from __future__ import annotations

import argparse
import sys

# Keep in sync with infra/stacks/config.py
VECTOR_BUCKET_NAME = "aicoe-content-vectors"
VECTOR_INDEX_NAME = "aicoe-content"
DIMENSIONS = 1024
REGION = "us-east-1"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=None)
    parser.add_argument("--region", default=REGION)
    args = parser.parse_args()

    import boto3
    from botocore.exceptions import ClientError

    session = boto3.Session(profile_name=args.profile, region_name=args.region)
    client = session.client("s3vectors")

    try:
        client.create_vector_bucket(vectorBucketName=VECTOR_BUCKET_NAME)
        print(f"created vector bucket {VECTOR_BUCKET_NAME}")
    except ClientError as exc:
        if exc.response["Error"]["Code"] in ("ConflictException", "BucketAlreadyExists"):
            print(f"vector bucket {VECTOR_BUCKET_NAME} already exists")
        else:
            raise

    try:
        client.create_index(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            dataType="float32",
            dimension=DIMENSIONS,
            distanceMetric="cosine",
        )
        print(f"created index {VECTOR_INDEX_NAME} ({DIMENSIONS} dims)")
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConflictException":
            print(f"index {VECTOR_INDEX_NAME} already exists")
        else:
            raise

    return 0


if __name__ == "__main__":
    sys.exit(main())
