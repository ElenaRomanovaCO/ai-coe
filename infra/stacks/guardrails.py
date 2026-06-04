"""Guardrails stack: a Bedrock guardrail with PII anonymization + prompt-attack
detection, attached to the orchestrator in task 02.
"""

from __future__ import annotations

from aws_cdk import CfnOutput, Stack
from aws_cdk import aws_bedrock as bedrock
from constructs import Construct

_PII_ANONYMIZE = ["US_SOCIAL_SECURITY_NUMBER", "EMAIL", "PHONE"]


class GuardrailsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        guardrail = bedrock.CfnGuardrail(
            self,
            "Guardrail",
            name="aicoe-guardrail",
            blocked_input_messaging="This request can't be processed.",
            blocked_outputs_messaging="This response was blocked.",
            sensitive_information_policy_config=bedrock.CfnGuardrail.SensitiveInformationPolicyConfigProperty(
                pii_entities_config=[
                    bedrock.CfnGuardrail.PiiEntityConfigProperty(type=t, action="ANONYMIZE")
                    for t in _PII_ANONYMIZE
                ]
            ),
            content_policy_config=bedrock.CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        type="PROMPT_ATTACK",
                        input_strength="HIGH",
                        # PROMPT_ATTACK only filters input; output strength must be NONE.
                        output_strength="NONE",
                    )
                ]
            ),
        )

        self.guardrail = guardrail
        CfnOutput(self, "GuardrailId", value=guardrail.attr_guardrail_id)
        CfnOutput(self, "GuardrailArn", value=guardrail.attr_guardrail_arn)
