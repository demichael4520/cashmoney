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

## 🌐 Public API Endpoints

The tools (either local or via the MCP server) interact with the following public endpoints. If deploying the agent behind an **Agent Gateway** or firewall, outbound traffic (egress rules) must be permitted to these hosts:

*   **Current Fiat Rates**: `https://open.er-api.com` (ExchangeRate-API)
*   **Current Crypto Prices**: `https://api.coinbase.com` (Coinbase Public API)
*   **Historical Rates**: `https://api.frankfurter.app` (Frankfurter ECB API)

---

## 💬 Sample Prompts for Testing

To test the agent's tools in the ADK Web UI, local tests, or the Vertex AI Playground, use the following sample prompts:

*   **Fiat Conversion**: `"Convert 100 USD to EUR"`
*   **Batch Conversion**: `"Convert 1000 USD to EUR, GBP, and INR"`
*   **Crypto Rates**: `"What is the current exchange rate for BTC in USD and EUR?"`
*   **Historical Lookup**: `"What was the historical exchange rate of USD to INR on 2025-01-15?"`

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

When using custom Agent Identity and Agent Gateways to govern traffic to private endpoints or services peered via Private Service Connect (PSC), configure the Agent Gateway with private egress and DNS peering.

#### 1. Define Agent Gateway Configuration with DNS Peering

Create a file named `agw-egress-dns.yaml` containing the `dnsPeeringConfig` to resolve domain names in the target VPC network:

```yaml
name: agent-gateway-egress
protocols:
  - MCP
googleManaged:
  governedAccessPath: AGENT_TO_ANYWHERE
registries:
  - "//agentregistry.googleapis.com/projects/<PROJECT_ID>/locations/<REGION>"
networkConfig:
  egress:
    networkAttachment: projects/<PROJECT_ID>/regions/<REGION>/networkAttachments/<PSC_ATTACHMENT_NAME>
  dnsPeeringConfig:
    domains:
      - "internal.domain.corp."  # Suffix must end with a dot
    targetProject: <TARGET_PROJECT_ID>
    targetNetwork: projects/<TARGET_PROJECT_NUMBER>/global/networks/<VPC_NAME>
```

Import or update the Agent Gateway resource:
```bash
gcloud alpha network-services agent-gateways import agent-gateway-egress \
  --source="agw-egress-dns.yaml" \
  --location=<REGION> \
  --project=<PROJECT_ID>
```

#### 2. Grant DNS Peering IAM Role

For DNS peering to resolve successfully, the Agent Gateway service account must have the `roles/dns.peer` role on the target project hosting the DNS zone:

```bash
gcloud alpha projects add-iam-policy-binding <TARGET_PROJECT_ID> \
  --member=serviceAccount:service-<GATEWAY_PROJECT_NUMBER>@gcp-sa-dep.iam.gserviceaccount.com \
  --role=roles/dns.peer
```

#### 3. Bind your reasoning engine to the gateway

Execute the following `PATCH` request to bind the reasoning engine:

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

#### 4. Validation: Verify Agent Gateway Binding

To verify that the deployed Reasoning Engine is correctly configured to route traffic through the Agent Gateway, query the Reasoning Engine details using the GET API:

```bash
export REGION="us-east4"
export PROJECT_ID="579295505315"
export ENGINE_ID="6906419562154033152"

curl -s -X GET \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://${REGION}-aiplatform.googleapis.com/v1beta1/projects/${PROJECT_ID}/locations/${REGION}/reasoningEngines/${ENGINE_ID}" \
  | jq '.spec.deploymentSpec.agentGatewayConfig'
```

**Expected Output:**
```json
{
  "agentToAnywhereConfig": {
    "agentGateway": "projects/579295505315/locations/us-east4/agentGateways/agent-gateway-egress"
  }
}
```

