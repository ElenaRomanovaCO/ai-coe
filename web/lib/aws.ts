import "server-only";

import { LambdaClient, InvokeCommand } from "@aws-sdk/client-lambda";
import { AssumeRoleWithWebIdentityCommand, STSClient } from "@aws-sdk/client-sts";

// IAM-signed Lambda invocation from Next.js server actions/routes, authenticated
// via Vercel <-> AWS OIDC federation (no static AWS keys). The frontend's role
// (aicoe-vercel-oidc-role) may only invoke the orchestrator endpoint Lambda.

const REGION = process.env.AWS_REGION ?? "us-east-1";

function getOidcToken(): string {
  // Vercel injects this at runtime for OIDC-enabled projects.
  const token = process.env.VERCEL_OIDC_TOKEN;
  if (!token) {
    throw new Error("VERCEL_OIDC_TOKEN is not available — enable Vercel OIDC for this project.");
  }
  return token;
}

async function assumeRoleCredentials() {
  const roleArn = process.env.AICOE_VERCEL_ROLE_ARN;
  if (!roleArn) {
    throw new Error("AICOE_VERCEL_ROLE_ARN is not set.");
  }
  const sts = new STSClient({ region: REGION });
  const res = await sts.send(
    new AssumeRoleWithWebIdentityCommand({
      RoleArn: roleArn,
      RoleSessionName: "aicoe-web",
      WebIdentityToken: getOidcToken(),
      DurationSeconds: 900,
    }),
  );
  const c = res.Credentials;
  if (!c?.AccessKeyId || !c.SecretAccessKey || !c.SessionToken) {
    throw new Error("AssumeRoleWithWebIdentity returned no credentials.");
  }
  return {
    accessKeyId: c.AccessKeyId,
    secretAccessKey: c.SecretAccessKey,
    sessionToken: c.SessionToken,
  };
}

export async function invokeLambda<T = unknown>(
  functionName: string,
  payload: unknown,
): Promise<T> {
  const credentials = await assumeRoleCredentials();
  const lambda = new LambdaClient({ region: REGION, credentials });
  const res = await lambda.send(
    new InvokeCommand({
      FunctionName: functionName,
      Payload: new TextEncoder().encode(JSON.stringify(payload)),
    }),
  );
  const text = res.Payload ? new TextDecoder().decode(res.Payload) : "";
  return (text ? JSON.parse(text) : null) as T;
}

export function orchestratorFunctionName(): string {
  return process.env.AICOE_ORCHESTRATOR_FN ?? "aicoe-fargate-orchestrator-endpoint-lambda";
}
