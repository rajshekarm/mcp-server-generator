import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { McpServer, ServerLogs } from "./types";

const POLL_INTERVAL = 4000;

function App() {
  const [servers, setServers] = useState<McpServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [logs, setLogs] = useState<ServerLogs | null>(null);

  const loadServers = useCallback(async (showSpinner = false) => {
    if (showSpinner) setLoading(true);
    try {
      setServers(await api.listServers());
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load MCP servers");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadServers(true);
    const timer = window.setInterval(() => void loadServers(), POLL_INTERVAL);
    return () => window.clearInterval(timer);
  }, [loadServers]);

  const counts = useMemo(() => {
    const running = servers.filter((item) => ["running", "external"].includes(item.runtime.status)).length;
    return { running, stopped: servers.length - running };
  }, [servers]);

  async function changeState(server: McpServer) {
    const id = server.server.id;
    const isRunning = server.runtime.status === "running";
    setBusyId(id);
    setError(null);
    try {
      const updated = isRunning ? await api.stopServer(id) : await api.startServer(id);
      setServers((items) => items.map((item) => (item.server.id === id ? updated : item)));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The operation failed");
      await loadServers();
    } finally {
      setBusyId(null);
    }
  }

  async function showLogs(id: string) {
    try {
      setLogs(await api.getLogs(id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load server logs");
    }
  }

  return (
    <main className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">Local control plane</p>
          <h1>MCP Server Console</h1>
          <p className="subtitle">Monitor and control every server created by your generator.</p>
        </div>
        <button className="refresh-button" onClick={() => void loadServers(true)} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh"}
        </button>
      </header>

      <section className="summary" aria-label="Server summary">
        <Summary label="Generated" value={servers.length} />
        <Summary label="Running" value={counts.running} tone="green" />
        <Summary label="Not running" value={counts.stopped} tone="amber" />
      </section>

      {error && <div className="error-banner" role="alert">{error}</div>}

      <section className="server-grid" aria-live="polite">
        {!loading && servers.length === 0 && (
          <div className="empty-state">
            <h2>No generated servers yet</h2>
            <p>Create one through the generator API, then refresh this page.</p>
          </div>
        )}
        {servers.map((server) => (
          <ServerCard
            key={server.server.id}
            server={server}
            busy={busyId === server.server.id}
            onToggle={() => void changeState(server)}
            onLogs={() => void showLogs(server.server.id)}
          />
        ))}
      </section>

      {logs && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setLogs(null)}>
          <section className="log-modal" role="dialog" aria-modal="true" aria-label="Server logs" onMouseDown={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <p className="eyebrow">Latest output</p>
                <h2>{logs.server_id}</h2>
              </div>
              <button className="icon-button" onClick={() => setLogs(null)} aria-label="Close logs">×</button>
            </div>
            <pre>{logs.content || "No log output yet."}</pre>
          </section>
        </div>
      )}
    </main>
  );
}

function Summary({ label, value, tone = "blue" }: { label: string; value: number; tone?: string }) {
  return (
    <article className={`summary-card ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function ServerCard({ server, busy, onToggle, onLogs }: {
  server: McpServer;
  busy: boolean;
  onToggle: () => void;
  onLogs: () => void;
}) {
  const running = server.runtime.status === "running";
  const external = server.runtime.status === "external";
  const failed = server.runtime.status === "failed";
  return (
    <article className="server-card">
      <div className="card-heading">
        <div>
          <div className="title-row">
            <h2>{server.server.title}</h2>
            <span className={`status-pill ${server.runtime.status}`}>
              <i />{server.runtime.status}
            </span>
          </div>
          <p>{server.server.description}</p>
        </div>
      </div>

      <dl className="details">
        <div><dt>MCP endpoint</dt><dd>{server.connection.url}</dd></div>
        <div><dt>REST API</dt><dd>{server.generation.api_base_url || "Not recorded"}</dd></div>
        <div><dt>Tools</dt><dd>{server.capabilities.tool_count}</dd></div>
        <div><dt>Process</dt><dd>{server.runtime.pid ? `PID ${server.runtime.pid}` : "—"}</dd></div>
      </dl>

      {failed && server.runtime.last_error && (
        <p className="inline-error">{server.runtime.last_error.split("\n").at(-1)}</p>
      )}

      <div className="card-actions">
        <button className={running ? "stop-button" : "start-button"} onClick={onToggle} disabled={busy || external}>
          {busy ? "Working…" : running ? "Stop server" : external ? "Started externally" : "Start server"}
        </button>
        <button className="logs-button" onClick={onLogs}>View logs</button>
      </div>
    </article>
  );
}

export default App;
