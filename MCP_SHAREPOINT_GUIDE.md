# MCP Server for SharePoint Knowledge Base
### Python Setup Guide — Blueverse Ltd Agents
*Connects your AI agents to SharePoint documents via a local or remote MCP server*

---

## What This Does

Your SharePoint site holds knowledge base documents (Word, PDF, text files).
This MCP server sits between your Blueverse agents and SharePoint, exposing tools
the agent can call to search and read those documents.

```
Blueverse Agent
      │
      ▼
MCP Server (Python, running locally or on a server)
      │
      ▼
Microsoft Graph API
      │
      ▼
SharePoint — your knowledge base documents
```

---

## Prerequisites

- Python 3.10+
- A Microsoft 365 / SharePoint account (Blueverse tenant)
- Access to Azure Portal (to register an app)
- Your SharePoint site URL

---

## PART 1 — Azure App Registration (One-Time Setup)

This gives your MCP server permission to read SharePoint on behalf of Blueverse.

### Step 1 — Create the App Registration

1. Go to **portal.azure.com**
2. Search for **"App registrations"** → click **New registration**
3. Fill in:
   - **Name:** `BlueverseMCP` (or any name you prefer)
   - **Supported account types:** Accounts in this organisational directory only
   - **Redirect URI:** leave blank
4. Click **Register**
5. Copy and save:
   - **Application (client) ID** → you'll need this
   - **Directory (tenant) ID** → you'll need this

### Step 2 — Create a Client Secret

1. In your app registration → **Certificates & secrets**
2. Click **New client secret**
3. Description: `mcp-server-secret`, Expires: 24 months
4. Click **Add**
5. Copy the **Value** immediately — it won't show again

### Step 3 — Add SharePoint Permissions

1. In your app registration → **API permissions**
2. Click **Add a permission** → **Microsoft Graph** → **Application permissions**
3. Search and add:
   - `Sites.Read.All` — read all SharePoint sites
   - `Files.Read.All` — read all files
4. Click **Grant admin consent for Blueverse** → confirm

> **Note:** Admin consent requires a Global Admin or SharePoint Admin account.
> If you don't have admin rights, ask your IT/Azure admin to grant consent.

---

## PART 2 — Find Your SharePoint Details

You need two values from your SharePoint site.

### Step 4 — Get Your Site ID

1. Open your SharePoint site in browser
2. Note the URL format:
   ```
   https://blueverse.sharepoint.com/sites/KnowledgeBase
   ```
3. Your **site hostname** = `blueverse.sharepoint.com`
4. Your **site path** = `/sites/KnowledgeBase`

You can confirm the Site ID by visiting this URL in your browser (while logged in):
```
https://blueverse.sharepoint.com/sites/KnowledgeBase/_api/site/id
```

### Step 5 — Get Your Drive/Library Name

The default document library in SharePoint is usually called **"Documents"** or **"Shared Documents"**.
You can check by going to your SharePoint site → **Documents** tab in the left sidebar.

---

## PART 3 — Build the MCP Server

### Step 6 — Create the Project

```bash
mkdir blueverse-mcp
cd blueverse-mcp
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### Step 7 — Install Dependencies

```bash
pip install mcp httpx python-dotenv
```

Create `requirements.txt`:
```
mcp
httpx
python-dotenv
```

### Step 8 — Create the .env File

Create `blueverse-mcp/.env`:
```
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here
SHAREPOINT_HOSTNAME=blueverse.sharepoint.com
SHAREPOINT_SITE_PATH=/sites/KnowledgeBase
```

### Step 9 — Write the MCP Server

Create `blueverse-mcp/server.py`:

```python
import os
import httpx
import asyncio
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────
TENANT_ID       = os.getenv("AZURE_TENANT_ID")
CLIENT_ID       = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET   = os.getenv("AZURE_CLIENT_SECRET")
SP_HOSTNAME     = os.getenv("SHAREPOINT_HOSTNAME")
SP_SITE_PATH    = os.getenv("SHAREPOINT_SITE_PATH")
GRAPH_BASE      = "https://graph.microsoft.com/v1.0"

server = Server("blueverse-sharepoint-mcp")

# ── Auth: get access token from Azure ───────────────────────────────────────
async def get_token() -> str:
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]

# ── Helper: get SharePoint site ID ──────────────────────────────────────────
async def get_site_id(token: str) -> str:
    url = f"{GRAPH_BASE}/sites/{SP_HOSTNAME}:{SP_SITE_PATH}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        return resp.json()["id"]

# ── Helper: get default drive ID ────────────────────────────────────────────
async def get_drive_id(token: str, site_id: str) -> str:
    url = f"{GRAPH_BASE}/sites/{site_id}/drive"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
        resp.raise_for_status()
        return resp.json()["id"]

# ── Tool 1: list_documents ───────────────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_documents",
            description="List all documents in the Blueverse SharePoint knowledge base.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="read_document",
            description="Read the full text content of a specific document by its name.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "The name of the file to read (e.g. 'onboarding.docx')"
                    }
                },
                "required": ["file_name"],
            },
        ),
        types.Tool(
            name="search_documents",
            description="Search for documents in the SharePoint knowledge base by keyword.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keyword or phrase to search for"
                    }
                },
                "required": ["query"],
            },
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:

    token    = await get_token()
    site_id  = await get_site_id(token)
    drive_id = await get_drive_id(token, site_id)
    headers  = {"Authorization": f"Bearer {token}"}

    # ── list_documents ──────────────────────────────────────────────────────
    if name == "list_documents":
        url = f"{GRAPH_BASE}/drives/{drive_id}/root/children"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            items = resp.json().get("value", [])

        files = [
            f"- {item['name']} ({round(item.get('size', 0) / 1024, 1)} KB)"
            for item in items if "file" in item
        ]
        result = "\n".join(files) if files else "No documents found."
        return [types.TextContent(type="text", text=f"Documents in SharePoint:\n{result}")]

    # ── read_document ───────────────────────────────────────────────────────
    elif name == "read_document":
        file_name = arguments["file_name"]

        # Find the file
        url = f"{GRAPH_BASE}/drives/{drive_id}/root/children"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            items = resp.json().get("value", [])

        match = next((i for i in items if i["name"].lower() == file_name.lower()), None)
        if not match:
            return [types.TextContent(type="text", text=f"File '{file_name}' not found in SharePoint.")]

        # Download content
        download_url = match.get("@microsoft.graph.downloadUrl")
        if not download_url:
            return [types.TextContent(type="text", text=f"Cannot download '{file_name}' — no download URL available.")]

        async with httpx.AsyncClient() as client:
            content_resp = await client.get(download_url)
            content_resp.raise_for_status()

        # Return text content (works for .txt files directly)
        # For .docx / .pdf you'd add python-docx / pdfplumber parsing here
        try:
            text = content_resp.text
        except Exception:
            text = "[Binary file — text extraction not supported for this format]"

        return [types.TextContent(type="text", text=f"Content of '{file_name}':\n\n{text}")]

    # ── search_documents ────────────────────────────────────────────────────
    elif name == "search_documents":
        query = arguments["query"]
        url   = f"{GRAPH_BASE}/sites/{site_id}/drive/root/search(q='{query}')"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            items = resp.json().get("value", [])

        if not items:
            return [types.TextContent(type="text", text=f"No documents found matching '{query}'.")]

        results = "\n".join(
            f"- {item['name']} (last modified: {item.get('lastModifiedDateTime', 'unknown')})"
            for item in items
        )
        return [types.TextContent(type="text", text=f"Search results for '{query}':\n{results}")]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


# ── Run ──────────────────────────────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

---

## PART 4 — Connect Your Agent to the MCP Server

### Step 10 — Run the MCP Server

```bash
cd blueverse-mcp
venv\Scripts\activate
python server.py
```

The server starts and listens over stdio — ready for agent connections.

### Step 11 — Configure Your Agent

If your Blueverse agent supports MCP (Claude-based or MCP-compatible), add this to its MCP config:

**For Claude Desktop / Claude Code (`claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "blueverse-sharepoint": {
      "command": "python",
      "args": ["C:/path/to/blueverse-mcp/server.py"],
      "env": {
        "AZURE_TENANT_ID": "your-tenant-id",
        "AZURE_CLIENT_ID": "your-client-id",
        "AZURE_CLIENT_SECRET": "your-client-secret",
        "SHAREPOINT_HOSTNAME": "blueverse.sharepoint.com",
        "SHAREPOINT_SITE_PATH": "/sites/KnowledgeBase"
      }
    }
  }
}
```

**For a custom Python agent using MCP SDK:**
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="python",
    args=["path/to/blueverse-mcp/server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # List documents
        result = await session.call_tool("list_documents", {})

        # Search
        result = await session.call_tool("search_documents", {"query": "onboarding"})

        # Read a specific file
        result = await session.call_tool("read_document", {"file_name": "policy.txt"})
```

---

## PART 5 — Adding .docx and PDF Support (Optional)

Plain `.txt` files work out of the box. For Word and PDF:

```bash
pip install python-docx pdfplumber
```

Add this to `server.py` inside `read_document`, after downloading the file:

```python
import io
import pdfplumber
from docx import Document

content_bytes = content_resp.content
file_lower    = file_name.lower()

if file_lower.endswith(".pdf"):
    with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

elif file_lower.endswith(".docx"):
    doc  = Document(io.BytesIO(content_bytes))
    text = "\n".join(p.text for p in doc.paragraphs)

else:
    text = content_resp.text
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `401 Unauthorized` | Client secret expired or wrong. Regenerate in Azure portal. |
| `403 Forbidden` | Admin consent not granted. Ask Azure admin to grant `Sites.Read.All`. |
| `Site not found` | Check `SHAREPOINT_HOSTNAME` and `SHAREPOINT_SITE_PATH` exactly match your URL. |
| `File not found` | Filename is case-sensitive. Use `list_documents` first to see exact names. |
| `pip install mcp fails` | Try `pip install mcp --pre` — the MCP Python SDK may need pre-release flag. |

---

## Quick Reference

```
ONE-TIME SETUP
──────────────
1. Azure Portal → App Registrations → New → copy Tenant ID, Client ID
2. Certificates & Secrets → New client secret → copy Value
3. API Permissions → Microsoft Graph → Sites.Read.All + Files.Read.All → Grant consent
4. Create .env with all 5 values

EVERY TIME YOU RUN
──────────────────
cd blueverse-mcp
venv\Scripts\activate
python server.py

TOOLS YOUR AGENT CAN CALL
──────────────────────────
list_documents()                    → see all docs in SharePoint
search_documents(query="keyword")   → find docs by keyword
read_document(file_name="doc.txt")  → read full content of a file
```

---

*Blueverse Ltd — Internal Guide*
*MCP SharePoint Knowledge Base Integration — Python*
*Version 1.0 — March 2026*
