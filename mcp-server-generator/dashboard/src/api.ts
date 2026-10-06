import type { McpServer, ServerLogs } from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:9000").replace(/\/$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  listServers: () => request<McpServer[]>("/mcp-servers"),
  startServer: (id: string) =>
    request<McpServer>(`/mcp-servers/${encodeURIComponent(id)}/start`, { method: "POST" }),
  stopServer: (id: string) =>
    request<McpServer>(`/mcp-servers/${encodeURIComponent(id)}/stop`, { method: "POST" }),
  getLogs: (id: string) =>
    request<ServerLogs>(`/mcp-servers/${encodeURIComponent(id)}/logs`),
};
