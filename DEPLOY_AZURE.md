# TARE — Azure Web App Deployment Guide

## Overview

This guide deploys TARE as a **Docker container** on Azure Web App (App Service).
The container bundles the React frontend + FastAPI backend + ML model into a single image.

**Stack:** Python 3.11 · FastAPI · Uvicorn · React 18 · scikit-learn · Groq LLM

---

## Prerequisites

Install these tools before starting:

| Tool | Install |
|---|---|
| Azure CLI | https://learn.microsoft.com/en-us/cli/azure/install-azure-cli |
| Docker Desktop | https://www.docker.com/products/docker-desktop |
| Git | https://git-scm.com |

Verify installs:
```bash
az --version
docker --version
git --version
```

Log in to Azure:
```bash
az login
```

---

## Part 1 — One-Time Azure Setup

### 1.1 Create a Resource Group

```bash
az group create \
  --name tare-rg \
  --location eastus
```

> You can change `eastus` to any Azure region (e.g. `westeurope`, `southeastasia`).

---

### 1.2 Create an Azure Container Registry (ACR)

ACR stores your Docker image privately.

```bash
az acr create \
  --resource-group tare-rg \
  --name tareregistry \
  --sku Basic \
  --admin-enabled true
```

> **Note:** ACR names must be globally unique. If `tareregistry` is taken, use something like `tare2025registry`.

Get the ACR login server URL:
```bash
az acr show \
  --name tareregistry \
  --query loginServer \
  --output tsv
```

It will output something like: `tareregistry.azurecr.io`

---

### 1.3 Create an App Service Plan

```bash
az appservice plan create \
  --name tare-plan \
  --resource-group tare-rg \
  --is-linux \
  --sku B2
```

> **SKU options:**
> - `B1` — 1 core, 1.75 GB RAM — minimum (may be slow)
> - `B2` — 2 cores, 3.5 GB RAM — recommended for demo
> - `B3` — 4 cores, 7 GB RAM — if ML inference feels slow

---

## Part 2 — Build and Push Docker Image

### 2.1 Make sure the ML model is trained

The Dockerfile copies `ml/model.pkl` — this file must exist before building.

```bash
# From the aegis-poc/ root directory
python ml/train_model.py
```

You should see:
```
Model saved → ml/model.pkl
```

---

### 2.2 Log Docker into ACR

```bash
az acr login --name tareregistry
```

---

### 2.3 Build the Docker image

From the `aegis-poc/` root directory (where the Dockerfile is):

```bash
docker build -t tareregistry.azurecr.io/tare-app:latest .
```

This takes 3–5 minutes on first build (installs Python packages + npm build).

---

### 2.4 Push the image to ACR

```bash
docker push tareregistry.azurecr.io/tare-app:latest
```

---

## Part 3 — Create the Web App

### 3.1 Get ACR credentials

```bash
az acr credential show --name tareregistry
```

Note the `username` and one of the `passwords` from the output.

---

### 3.2 Create the Web App

```bash
az webapp create \
  --resource-group tare-rg \
  --plan tare-plan \
  --name tare-demo-app \
  --deployment-container-image-name tareregistry.azurecr.io/tare-app:latest
```

> **Note:** `tare-demo-app` must be globally unique. It becomes your URL:
> `https://tare-demo-app.azurewebsites.net`

---

### 3.3 Configure ACR credentials on the Web App

```bash
az webapp config container set \
  --name tare-demo-app \
  --resource-group tare-rg \
  --docker-custom-image-name tareregistry.azurecr.io/tare-app:latest \
  --docker-registry-server-url https://tareregistry.azurecr.io \
  --docker-registry-server-user tareregistry \
  --docker-registry-server-password <YOUR_ACR_PASSWORD>
```

Replace `<YOUR_ACR_PASSWORD>` with the password from step 3.1.

---

### 3.4 Set the port

Azure App Service forwards traffic to port 8000 (what Uvicorn listens on):

```bash
az webapp config appsettings set \
  --name tare-demo-app \
  --resource-group tare-rg \
  --settings WEBSITES_PORT=8000
```

---

### 3.5 Set the GROQ API key

```bash
az webapp config appsettings set \
  --name tare-demo-app \
  --resource-group tare-rg \
  --settings GROQ_API_KEY="your_groq_api_key_here"
```

> Get a free Groq API key at: https://console.groq.com
> Without this key, TARE falls back to static LLM responses (still functional).

---

### 3.6 Enable WebSocket support

TARE uses WebSockets for real-time events — must be explicitly enabled:

```bash
az webapp config set \
  --name tare-demo-app \
  --resource-group tare-rg \
  --web-sockets-enabled true
```

---

## Part 4 — Verify Deployment

### 4.1 Check deployment status

```bash
az webapp show \
  --name tare-demo-app \
  --resource-group tare-rg \
  --query state \
  --output tsv
```

Should return `Running`.

---

### 4.2 Stream live logs

```bash
az webapp log tail \
  --name tare-demo-app \
  --resource-group tare-rg
```

Look for:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### 4.3 Open in browser

```
https://tare-demo-app.azurewebsites.net
```

---

## Part 5 — Updating the App

Every time you change code, rebuild and push:

```bash
# 1. Rebuild image
docker build -t tareregistry.azurecr.io/tare-app:latest .

# 2. Push to ACR
docker push tareregistry.azurecr.io/tare-app:latest

# 3. Restart the web app to pull the new image
az webapp restart \
  --name tare-demo-app \
  --resource-group tare-rg
```

Allow 1–2 minutes for the container to restart.

---

## Troubleshooting

### App shows "Application Error" page

Check the logs:
```bash
az webapp log tail --name tare-demo-app --resource-group tare-rg
```

Common causes:
- `GROQ_API_KEY` not set → TARE still works, LLM falls back to static
- ML model missing → check `ml/model.pkl` exists before docker build
- Port mismatch → confirm `WEBSITES_PORT=8000` is set

---

### WebSocket disconnects immediately

Make sure WebSockets are enabled (step 3.6). App Service Basic tier (B1/B2/B3) supports WebSockets — Free/Shared tiers do not.

---

### Container fails to start

```bash
# View container logs
az webapp log download \
  --name tare-demo-app \
  --resource-group tare-rg \
  --log-file logs.zip
```

Most common issue: `ml/model.pkl` not found. Run `python ml/train_model.py` before building.

---

### Image not updating after push

Force a fresh pull:
```bash
az webapp config container set \
  --name tare-demo-app \
  --resource-group tare-rg \
  --docker-custom-image-name tareregistry.azurecr.io/tare-app:latest

az webapp restart --name tare-demo-app --resource-group tare-rg
```

---

## Cost Estimate

| Resource | SKU | Approx. Monthly Cost |
|---|---|---|
| App Service Plan | B2 | ~$75 USD |
| Container Registry | Basic | ~$5 USD |
| **Total** | | **~$80 USD/month** |

> To save costs when not presenting: stop the web app (free while stopped, storage charges only):
> ```bash
> az webapp stop --name tare-demo-app --resource-group tare-rg
> az webapp start --name tare-demo-app --resource-group tare-rg
> ```

---

## Quick Reference — All Commands

```bash
# ── One-time setup ─────────────────────────────────────────────
az login
az group create --name tare-rg --location eastus
az acr create --resource-group tare-rg --name tareregistry --sku Basic --admin-enabled true
az appservice plan create --name tare-plan --resource-group tare-rg --is-linux --sku B2

# ── Build & push ───────────────────────────────────────────────
python ml/train_model.py
az acr login --name tareregistry
docker build -t tareregistry.azurecr.io/tare-app:latest .
docker push tareregistry.azurecr.io/tare-app:latest

# ── Create app ─────────────────────────────────────────────────
az webapp create --resource-group tare-rg --plan tare-plan --name tare-demo-app --deployment-container-image-name tareregistry.azurecr.io/tare-app:latest
az webapp config container set --name tare-demo-app --resource-group tare-rg --docker-custom-image-name tareregistry.azurecr.io/tare-app:latest --docker-registry-server-url https://tareregistry.azurecr.io --docker-registry-server-user tareregistry --docker-registry-server-password <ACR_PASSWORD>
az webapp config appsettings set --name tare-demo-app --resource-group tare-rg --settings WEBSITES_PORT=8000
az webapp config appsettings set --name tare-demo-app --resource-group tare-rg --settings GROQ_API_KEY="<your_key>"
az webapp config set --name tare-demo-app --resource-group tare-rg --web-sockets-enabled true

# ── Update after code changes ───────────────────────────────────
docker build -t tareregistry.azurecr.io/tare-app:latest .
docker push tareregistry.azurecr.io/tare-app:latest
az webapp restart --name tare-demo-app --resource-group tare-rg
```
