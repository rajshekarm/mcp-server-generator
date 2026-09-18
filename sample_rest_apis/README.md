# Sample REST APIs

These FastAPI applications provide varied OpenAPI documents for testing the MCP
server generator. PolicyCenter, ClaimCenter, and BillingCenter share the
customer IDs `CUS-1001` and `CUS-1002` and policy IDs `POL-1001` and `POL-1002`
to support connected insurance scenarios.

Run the commands from the repository root in separate terminals:

```powershell
python -m uvicorn sample_rest_apis.general.inventory_api:app --port 8101
python -m uvicorn sample_rest_apis.general.support_api:app --port 8102
python -m uvicorn sample_rest_apis.general.shipping_api:app --port 8103
python -m uvicorn sample_rest_apis.policy_center.app:app --port 8111
python -m uvicorn sample_rest_apis.claim_center.app:app --port 8112
python -m uvicorn sample_rest_apis.billing_center.app:app --port 8113
```

Start PolicyCenter, ClaimCenter, and BillingCenter together with the
cross-platform Python launcher:

```shell
python sample_rest_apis/scripts/start_centers.py
```

The launcher uses the active Python interpreter, displays the documentation URL
for each center, and keeps all three processes attached to the terminal. Press
Ctrl+C to stop them together. To listen on another interface:

```shell
python sample_rest_apis/scripts/start_centers.py --host 0.0.0.0
```

Their OpenAPI documents are available at:

```text
http://127.0.0.1:8101/openapi.json
http://127.0.0.1:8102/openapi.json
http://127.0.0.1:8103/openapi.json
http://127.0.0.1:8111/openapi.json
http://127.0.0.1:8112/openapi.json
http://127.0.0.1:8113/openapi.json
```

Interactive documentation is available at `/docs` on each port.

Start the generator service from the repository root with:

```powershell
python mcp-server-generator/run.py
```

With the generator service running on port 9000, use
`requests/generator_requests.http` to generate an MCP project for each API.
