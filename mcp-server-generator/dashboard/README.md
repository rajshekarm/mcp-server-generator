# MCP Server Dashboard

This is a simple local dashboard for viewing and managing the MCP servers
created by the MCP Server Generator.

## Features

- View all generated MCP servers in one place.
- See whether each server is running, stopped, failed, or started externally.
- Start and stop individual MCP servers.
- View the MCP URL, REST API URL, tool count, and process ID.
- Read server logs when startup fails or when troubleshooting is needed.
- Refresh server status automatically.

The dashboard only stops servers that it started. A server started manually is
shown as `external` and is left untouched.

## Run the dashboard

First, start the generator API from the `mcp-server-generator` directory:

```powershell
python run.py
```

Then open another terminal and start the dashboard:

```powershell
cd dashboard
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173` in your browser.

By default, the dashboard connects to the generator API at
`http://127.0.0.1:9000`.
