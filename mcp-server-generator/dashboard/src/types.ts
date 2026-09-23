export type RuntimeStatus = "generated" | "starting" | "running" | "external" | "stopping" | "stopped" | "failed";

export interface McpServer {
  server: {
    id: string;
    name: string;
    title: string;
    description: string;
    version: string;
  };
  connection: {
    transport: "streamable-http";
    url: string;
  };
  capabilities: {
    tools: boolean;
    tool_count: number;
  };
  generation: {
    output_directory: string;
    openapi_source: string | null;
    api_base_url: string;
  };
  runtime: {
    status: RuntimeStatus;
    pid: number | null;
    started_at: string | null;
    exit_code: number | null;
    last_error: string | null;
  };
}

export interface ServerLogs {
  server_id: string;
  path: string;
  content: string;
}
