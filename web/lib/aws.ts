import "server-only";

import { LambdaClient, InvokeCommand } from "@aws-sdk/client-lambda";

// IAM-signed Lambda invocation from Next.js server actions/routes. On AWS Amplify
// Hosting (Gen 2), the SSR compute Lambda already runs with the attached
// aicoe-amplify-ssr-role, so the SDK's default credential provider resolves the
// role automatically — no static keys and no AssumeRole step. That role may only
// invoke the orchestrator endpoint Lambda.

const REGION = process.env.AWS_REGION ?? "us-east-1";

export async function invokeLambda<T = unknown>(
  functionName: string,
  payload: unknown,
): Promise<T> {
  const lambda = new LambdaClient({ region: REGION });
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
