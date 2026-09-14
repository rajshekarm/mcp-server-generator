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
`http://127.0.0.1:8001/mcp`. When the generated server is deployed, pass its
externally reachable endpoint through `--mcp-url`, for example
`https://mcp.example.com/insurance/mcp`.

The generated server supports the `API_BASE_URL`, `MCP_HOST`, `MCP_PORT`, and
`MCP_PATH` environment variables. The value given to `--mcp-url` describes the
client-facing endpoint; it does not deploy the server or change those runtime
settings.
