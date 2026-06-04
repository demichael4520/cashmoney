# CashMoney Currency Assistant Agent

`CashMoney` is a premier currency conversion and exchange rate assistant agent built using the **Agent Development Kit (ADK)** and deployed on **Vertex AI Reasoning Engine**. 

It can run completely **locally** using lightweight Python tools, or connect **remotely** to an external Model Context Protocol (MCP) server (such as one deployed on Google Cloud Run) to fetch real-time fiat and cryptocurrency data.

---

## 🚀 Features

*   **Dual Mode Execution**: Toggle between local Python functions and remote MCP servers.
*   **Comprehensive Data**: Supports 60+ fiat currencies and 30+ cryptocurrencies.
*   **Zero-Auth Setup**: Standard APIs used do not require any API keys.
*   **Easy Deployment**: Fully integrated with Vertex AI Reasoning Engine deployment standards.

---

## 📦 Directory Structure

```
├── agent.py                 # Core agent logic and tool registration
├── requirements.txt         # Package dependencies
├── test_local.py           # Quick verification script
└── .agent_engine_config.json # Deployment configuration file
```

---

## 🛠️ Local Development & Quick Start

### 1. Set Up Virtual Environment

We recommend using Python 3.9+ and a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Local Verification

Execute the local verification script to test the tool logic:

```bash
python test_local.py
```

### 3. Run the ADK Web UI Playground

You can run and test the agent interactive experience locally using ADK's web dashboard:

```bash
# Make sure you are in the source directory
adk web
```
Open `http://localhost:8000` in your browser to interact with the agent.

---

## 🌐 Targeting a Cloud Run Hosted MCP Server

To route tool execution to a remote **Model Context Protocol (MCP)** server (such as one hosted on Cloud Run via SSE or Streamable HTTP):

1.  Set the `MCP_SERVER_URL` environment variable to your Cloud Run endpoint (e.g. `https://your-mcp-service.a.run.app/sse` or `https://your-mcp-service.a.run.app/mcp`).
2.  The agent will automatically switch from local python tools to using the `McpToolset` pointing to the remote server.

### Example Local Run with Remote MCP:

```bash
export MCP_SERVER_URL="https://your-mcp-service.a.run.app/mcp"
python test_local.py
```

---

## ☁️ Deploying to Vertex AI Reasoning Engine

### Option A: Clean Deployment with SDK

Create a script `deploy.py` to package and deploy the agent to Google Cloud:

```python
import vertexai
from vertexai.preview import reasoning_engines
from agent import cash_money_agent

# Initialize Vertex AI
vertexai.init(
    project="your-gcp-project-id",
    location="us-central1"
)

# Deployment configuration
config = {
    "identity_type": "AGENT_IDENTITY",
    "env_vars": {
        # Optional: Pass the Cloud Run MCP Server URL to the deployment environment
        "MCP_SERVER_URL": "https://your-mcp-service.a.run.app/mcp"
    }
}

# Deploy to Vertex AI
remote_agent = reasoning_engines.ReasoningEngine.create(
    reasoning_class=cash_money_agent,
    requirements=["google-cloud-aiplatform[agent_engines]", "google-adk", "mcp"],
    config=config,
    display_name="cash-money-currency-agent"
)

print(f"Deployment successful! Resource Name: {remote_agent.resource_name}")
```

Run the script to deploy:
```bash
python deploy.py
```

---

## 🔄 Updating an Existing Deployment to Target Cloud Run

If your reasoning engine is already deployed, you can update it to target your Cloud Run hosted MCP server using either an in-place patch or a redeployment.

### Method 1: Patch Deployment Environment Variable (In-Place)

Update the environment variable `MCP_SERVER_URL` on your deployed reasoning engine.

Using the REST API:

```bash
export REGION="us-east4"
export PROJECT_ID="579295505315"
export ENGINE_ID="6906419562154033152"
export CLOUD_RUN_URL="https://your-mcp-service.a.run.app/mcp"

curl -X PATCH \
  "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${ENGINE_ID}?updateMask=spec.deploymentSpec.env" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "spec": {
      "deploymentSpec": {
        "env": [
          {
            "name": "MCP_SERVER_URL",
            "value": "'"${CLOUD_RUN_URL}"'"
          }
        ]
      }
    }
  }'
```

### Method 2: Route via regional Agent Gateway (Egress Control)

When using custom Agent Identity and Agent Gateways to govern traffic to the Cloud Run endpoint:

1.  Make sure your Agent Gateway is deployed in the target region.
2.  Bind your reasoning engine to the gateway by patching its `agentGatewayConfig`:

```bash
export REGION="us-east4"
export PROJECT_ID="579295505315"
export ENGINE_ID="6906419562154033152"

curl -X PATCH \
  "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${ENGINE_ID}?updateMask=spec.deploymentSpec.agentGatewayConfig" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "spec": {
      "deploymentSpec": {
        "agentGatewayConfig": {
          "agentToAnywhereConfig": {
            "agentGateway": "projects/'"${PROJECT_ID}"'/locations/'"${REGION}"'/agentGateways/agent-gateway-egress"
          }
        }
      }
    }
  }'
```
