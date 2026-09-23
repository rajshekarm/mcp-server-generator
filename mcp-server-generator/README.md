# MCP Server Generator POC

An installable command-line package that generates a ready-to-run FastMCP
server from a REST API's OpenAPI 3 document. Authentication is intentionally
outside the scope of this POC.

The supplied URL can be either an OpenAPI JSON URL or a REST API base URL. For
a base URL, the generator checks these conventional locations:

- `/openapi.json`
- `/swagger.json`
- `/v3/api-docs`

## Install for development

From this package directory:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

This installs the `mcp-generator` command.

## Generate a server

With the sample REST API running on port 8000:

```powershell
mcp-generator `
  --url http://127.0.0.1:8000 `
  --name "Insurance MCP" `
  --mcp-url http://127.0.0.1:8001/mcp `
  --output generated/insurance_mcp
```

You can also run the package directly:

```powershell
python -m mcp_generator `
  --url http://127.0.0.1:8000/openapi.json `
  --output generated/insurance_mcp
```

## Generated project

The output is a separate runnable project:

```text
generated/insurance_mcp/
|-- server.py
|-- server.json
|-- openapi.json
|-- requirements.txt
`-- README.md
```

Run it with:

```powershell
cd generated/insurance_mcp
pip install -r requirements.txt
python server.py
```

The command returns the MCP endpoint URL for clients to consume. Its default is
`http://127.0.0.1:8001/mcp`. The URL's host, port, and path also become the
generated server's runtime defaults. For example, `--mcp-url
http://127.0.0.1:8004/custom-mcp` generates a server that listens on host
`127.0.0.1`, port `8004`, and path `/custom-mcp` by default.

The generated server supports the `API_BASE_URL`, `MCP_HOST`, `MCP_PORT`, and
`MCP_PATH` environment variables. These variables can override the defaults
derived from `--mcp-url` when the server starts. Generating the files does not
deploy or start the server.

## Generator HTTP API

Start the generator API:

```powershell
mcp-generator-api
```

For local development, you can run it without installing the package:

```powershell
python run.py
```

The required dependencies (`fastapi`, `httpx`, and `uvicorn`) must still be
available in the active Python environment.

It listens on `http://127.0.0.1:9000` by default. Generate a server with:

```http
POST http://127.0.0.1:9000/mcp-servers
Content-Type: application/json

{
  "api_url": "http://127.0.0.1:8000",
  "name": "insurance-mcp",
  "title": "Insurance MCP",
  "description": "Provides MCP tools for the Insurance REST API",
  "version": "1.0.0",
  "mcp_url": "http://127.0.0.1:8001/mcp"
}
```

The API returns client-neutral server identity, Streamable HTTP connection
information, generated tool count, generation status, and artifact locations.
The generated status means the files exist; it does not mean the MCP server has
been deployed or started.

Interactive API documentation is available at `http://127.0.0.1:9000/docs`.
Set `MCP_GENERATOR_OUTPUT_ROOT` to change where generated projects are stored.

## Manage generated servers

The generator API also acts as a local process manager:

```http
GET  http://127.0.0.1:9000/mcp-servers
GET  http://127.0.0.1:9000/mcp-servers/{server_id}
POST http://127.0.0.1:9000/mcp-servers/{server_id}/start
POST http://127.0.0.1:9000/mcp-servers/{server_id}/stop
GET  http://127.0.0.1:9000/mcp-servers/{server_id}/logs
```

Each generated project has a `server.json` manifest. Older generated projects
are discovered and receive a manifest automatically. Processes started through
the API are stopped when the generator shuts down. A process already using a
server's port is reported as `external` and is never terminated by the
generator.

## React dashboard

Keep the generator API running, then open a second terminal:

```powershell
cd dashboard
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173`. The dashboard lists generated servers, refreshes
their state automatically, starts and stops API-managed servers, and displays
their latest logs. Set `VITE_API_BASE_URL` before starting Vite if the generator
API is not running at `http://127.0.0.1:9000`.

## Start all generated MCP servers

After assigning a unique default port in each generated `server.py`, start
every server under `generated/` with:

```shell
python mcp-server-generator/scripts/start_generated_servers.py
```

The script discovers `generated/*/server.py`, checks for duplicate ports,
starts every server with the active Python interpreter, and displays its MCP
URL. Press Ctrl+C to stop all generated servers together.
