import "server-only";

import { AwsClient } from "aws4fetch";
import { LambdaClient, InvokeCommand } from "@aws-sdk/client-lambda";

// IAM-signed AWS calls from Next.js server actions/routes. On AWS Amplify Hosting
// (Gen 2), the SSR compute role (aicoe-amplify-ssr-role) is attached at runtime, so
// credentials resolve from the standard env vars with no static keys and no
// AssumeRole step. That role may only invoke the orchestrator Function URL.

const REGION = process.env.AWS_REGION ?? "us-east-1";

/** SigV4 client bound to the SSR role's runtime credentials, signing for Lambda. */
function awsClient(): AwsClient {
  return new AwsClient({
    accessKeyId: process.env.AWS_ACCESS_KEY_ID ?? "",
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY ?? "",
    sessionToken: process.env.AWS_SESSION_TOKEN,
    region: REGION,
    service: "lambda", // Function URL invocations are signed against the lambda service
  });
}

/** Base Function URL of the streaming orchestrator (AGENT-01). */
export function orchestratorUrl(): string {
  const url = process.env.AICOE_ORCHESTRATOR_URL;
  if (!url) {
    throw new Error("AICOE_ORCHESTRATOR_URL is not set (orchestrator Function URL).");
  }
  return url.replace(/\/+$/, "");
}

/**
 * POST a ChatRequest to the orchestrator's streaming Function URL and return the
 * raw streaming Response. The body is a ReadableStream of SSE bytes
 * (event: token|tool|citation|done|error) that the caller pipes to the browser.
 */
export async function streamChat(payload: unknown): Promise<Response> {
  const client = awsClient();
  return client.fetch(`${orchestratorUrl()}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// --- Legacy buffered invoke (kept for any non-streaming caller) -------------
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

export function moduleAgentsFunctionName(): string {
  return process.env.AICOE_MODULE_AGENTS_FN ?? "aicoe-module-agents-lambda";
}

/**
 * Buffered invoke of a Layer-2 module agent via the module-agents Lambda.
 * Sends the router's {agent_id, args} contract and returns the parsed result.
 * Read-only/CRUD module flows go straight here — no orchestrator in the loop.
 */
export async function invokeModule<T = unknown>(
  agentId: string,
  args: Record<string, unknown>,
): Promise<T> {
  return invokeLambda<T>(moduleAgentsFunctionName(), { agent_id: agentId, args });
}
