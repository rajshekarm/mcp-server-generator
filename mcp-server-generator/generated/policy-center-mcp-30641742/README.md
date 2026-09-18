# policy-center-mcp

Generated from an OpenAPI 3 REST API. FastMCP exposes each of the
5 OpenAPI operations as an MCP tool.

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

After the server is started, MCP clients can connect to `http://127.0.0.1:8001/mcp`.

The generated default REST API base URL is `http://127.0.0.1:8111`. Override it when
needed:

```powershell
$env:API_BASE_URL = "https://another-api.example.com"
python server.py
```

You can also configure `MCP_HOST`, `MCP_PORT`, and `MCP_PATH`.
