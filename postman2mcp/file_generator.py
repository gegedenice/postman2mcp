# my_mcp_tool/file_generator.py
import os
import json

def generate_project_files(project_dir, postman_collection, openapi_spec, postman_api_key, ngrok_authtoken):
    # Create fastapi_proxy directory inside project_dir
    fastapi_proxy_dir = os.path.join(project_dir, "fastapi_proxy")
    os.makedirs(fastapi_proxy_dir, exist_ok=True)
    
    base_url = "http://localhost:8000"
    
    # Save Postman collection
    with open(os.path.join(fastapi_proxy_dir, "postman_collection.json"), "w") as f:
        json.dump(postman_collection, f, indent=4)

    # Save OpenAPI spec
    with open(os.path.join(fastapi_proxy_dir, "openapi.json"), "w") as f:
        json.dump(openapi_spec, f, indent=4)
        
            
    ai_plugin_content = {
        "schema_version": "v1",
        "name_for_human": "Generic FastAPI",
        "name_for_model": "generic_api",
        "description_for_human": "Interact with a generic API via MCP.",
        "description_for_model": "Plugin for querying a generic API using MCP.",
        "auth": {"type": "none"},
        "api": {
            "type": "openapi",
            "url": "http://localhost:8000/openapi.json",
        },
        "logo_url": "https://example.com/logo.png",
        "contact_email": "support@example.com",
        "legal_info_url": "https://example.com/terms"
    }

    # Generate FastAPI proxy main file
    fastapi_main_content = f"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.openapi.docs import get_swagger_ui_html
import httpx
import os
import uvicorn

app = FastAPI(title="OpenAlex MCP Server", openapi_url=None )

# CORS for LLM or local dev tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAPI and Swagger UI
# ================================
@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    return {ai_plugin_content}
    
@app.get("/openapi.json", include_in_schema=False)
async def serve_openapi():
    return FileResponse("fastapi_proxy/openapi.json", media_type="application/json")


@app.get("/docs", include_in_schema=False)
async def custom_docs():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="OpenAlex API Docs")

@app.get("/")
async def root():
    return {{"message": "FastAPI MCP-compatible proxy server is running.", "docs": "/docs", "openapi": "/openapi.json"}}

# Proxy endpoints
# ================================
@app.get("/{{full_path:path}}")
async def generic_proxy_get(full_path: str, request: Request):
    target_url = f"{base_url}/{{full_path}}"
    query_params = dict(request.query_params)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(target_url, params=query_params)
        return JSONResponse(status_code=response.status_code, content=response.json())
    except Exception as e:
        return JSONResponse(status_code=500, content={{"error": str(e)}})
"""
    with open(os.path.join(fastapi_proxy_dir, "main.py"), "w") as f:
        f.write(fastapi_main_content)

    # Generate FastMCP server main file
    fastmcp_main_content = """
import httpx
from fastmcp import FastMCP
import os
import subprocess

# Create an HTTP client for your API
client = httpx.AsyncClient(base_url="http://localhost:8000")

# Load your OpenAPI spec 
openapi_spec = httpx.get("http://localhost:8000/openapi.json").json()

# Create the MCP server
mcp = FastMCP.from_openapi(
    openapi_spec=openapi_spec,
    client=client,
    stateless_http=True, #!important for OpenAI Response API to accept the MCP streamable http transport mode
    name="MCP Server"
)
if __name__ == "__main__":
    print("Starting FastMCP server...")
    try:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=3333, path="/mcp")
    except Exception as e:
        print(f"FastMCP server crashed: {{e}}", exc_info=True)
"""
    with open(os.path.join(project_dir, "server.py"), "w") as f:
        f.write(fastmcp_main_content)
        
    # Generate ngrok tunnel script
    ngrok_script_content = f"""
import ngrok
import os
import time
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("NGROK_AUTHTOKEN"):
    raise ValueError("NGROK_AUTHTOKEN is not set in the environment variables.")

listener = ngrok.forward(3333, authtoken=os.getenv("NGROK_AUTHTOKEN"), subdomain="mcp")
# Output ngrok url to console
print(f"Ingress established at {{listener.url()}}")
# Keep the listener alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Closing listener")
"""
    with open(os.path.join(project_dir, "ngrok_tunnel.py"), "w") as f:
        f.write(ngrok_script_content)
        
    # Generate requirements.txt
    requirements_content = """fastapi
fastapi
fastmcp
httpx
ngrok
python-dotenv
uvicorn
"""
    with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
        f.write(requirements_content)
        
    # Generate .env file
    env_content = f"POSTMAN_API_KEY={postman_api_key}\n"
    if ngrok_authtoken:
        env_content += f"NGROK_AUTHTOKEN={ngrok_authtoken}\n"
    with open(os.path.join(project_dir, ".env"), "w") as f:
        f.write(env_content)
        
    # Generate README.md
    readme_content = """# FastAPI MCP Project
This project contains a FastAPI-based MCP server that proxies requests to an OpenAPI-compliant API.

It has been generated with the [`postman2mcp`](https://github.com/gegedenice/postman2mcp) tool, which converts a Postman collection into an OpenAPI specification and sets up a FastAPI server to handle requests.

## Prerequisites

- Python 3.7 or later
- **Optional (for FastMCP Inspector):**  
   - [Node.js](https://nodejs.org/) (version 14 or later recommended)
   - [npm](https://www.npmjs.com/) (comes with Node.js)
   - To use the FastMCP Inspector, you will need to install the npm package `@modelcontextprotocol/inspector@0.16.0`:
      ```
      npm install -g @modelcontextprotocol/inspector@0.16.0
      ```
- **Optional:** an [Ngrok](https://ngrok.com/) account (for public tunneling)

## Setup (in several steps and separate terminals)

1. Install dependencies:
   ```   
    pip install -r requirements.txt
    ```
    
2. Set up your environment variables in `.env`:

   Normally the `.env` file is already generated in the project directory and should contain your Postman API key and ngrok authtoken:
   ```
   POSTMAN_API_KEY=your_postman_api_key
   NGROK_AUTHTOKEN=your_ngrok_authtoken
   ```
   Check if you have a `.env` file in the project directory, if not create one (the POSTMAN_API_KEY is optional at this stage).
   
3. Run the FastAPI server:
   ```
    uvicorn fastapi_proxy.main:app --host 0.0.0.0 --port 8000
    ```
4. Run the FastMCP server:
   ```
    python server.py
    ```
5. Optional but useful: run the FastMCP inspecteur:
   ```
   fastmcp dev server.py
    ```
5. Start the ngrok tunnel:
   ```
    python ngrok_tunnel.py
    ```
## Available URLs and Endpoints

### Postman Collection
You can find the Postman collection in `fastapi_proxy/postman_collection.json`.

### OpenAPI Specification
The OpenAPI specification is available at `fastapi_proxy/openapi.json`.    

### FastAPI Server
- The FastAPI server will be running at `http://localhost:8000`.
- Acces the plugin manifest at `http://localhost:8000/.well-known/ai-plugin.json`.
- Access the OpenAPI specification at `http://localhost:8000/openapi.json`.
- Access the Swagger API documentation at `http://localhost:8000/docs`.

### FastMCP server

The MCP server url is `http://localhost:3333/mcp`

### FastMCP Inspector
- Access the FastMCP Inspector at `http://localhost:6274` (get the token in the console output of the FastMCP server).

### Ngrok Tunnel
- Get the ngrok public url in the console output of the `ngrok_tunnel.py` script.
- You can access the MCP server at `http://<ngrok_url>/mcp`.
- Monitore your ngrok requests at `https://dashboard.ngrok.com` (login with your ngrok account).

## Integrations examples

### Claude Desktop

Currently, Claude Desktop does not support HTTP streamable transport for MCP. To connect your MCP server, you need to add it to your `claude_desktop_config.json` using mcp-remote with the http-only transport option:
```
{
  "mcpServers": {
    "my-mcp-server": {
      "command": "npx",
      "args": [
	    "-y",
        "mcp-remote",
        "http://localhost:3333/mcp",
        "--transport",
        "http-only"
      ]
    }
  }	
}
```
This configuration ensures Claude Desktop communicates with your MCP server over HTTP.
"""
    with open(os.path.join(project_dir, "README.md"), "w") as f:
        f.write(readme_content)
    
    print(f"Project files generated in {project_dir}")
        
    