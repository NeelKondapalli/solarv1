# Solar-v1 ☀
  

A verifiable, user-facing agent that abstracts and automates key financial workflows on the Flare Layer 1 network. Built with Google Gemini and deployed to run inside a Trustable Execution Environment on Google Cloud.

Demo: https://www.loom.com/share/6de10ae187814ef59ef9e3a71f46a735?sid=a725a816-5e5f-41f0-90d2-da0486704175

Showcase: https://dorahacks.io/buidl/23884

$4000 award on the Decentralized Financial AI (DeFAI) track

  
## 🚀 Key Features

  
- **Live Market Analytics**

Convert NLP commands to declarative workflows to access and query the Flare Time Series Oracle (FTSO) for real-time analysis of coin prices and market trends in the past few days


- **Wallet Abstraction**

Automatically send tokens and swap arbitrary ERC-20 pairs, all with simple NLP commands. Single token swaps are done via [SparkDEX](http://sparkdex.ai/)

-  **Secure AI Execution**

Runs within a Trusted Execution Environment (TEE) featuring remote attestation support for robust security.
  


  

## 🖥️  Getting Started

  
You can deploy Flare AI DeFAI using Docker (recommended) or set up the backend and frontend manually.

  

### Environment Setup

  

1.  **Prepare the Environment File:**

Rename `.env.example` to `.env` and update the variables accordingly. Add you Gemini API keys. Set `SIMULATE_ATTESTATION=true` for local testing (without TEE deployment).

  

### Build using Docker
  

1.  **Build the Docker Image:**

```bash

docker build -t flare-ai-defai .

```

  

2.  **Run the Docker Container:**

  

```bash

docker run -p 80:80 -it --env-file .env flare-ai-defai

```

  

3.  **Access the Frontend:**

Open your browser and navigate to [http://localhost:80](http://localhost:80) to interact with the Chat UI.

  

## 🛠 Build Manually

  

Flare AI DeFAI is composed of a Python-based backend and a JavaScript frontend. Follow these steps for manual setup:

  

#### Backend Setup

  

1.  **Install Dependencies:**

Use [uv](https://docs.astral.sh/uv/getting-started/installation/) to install backend dependencies:

  

```bash

uv sync --all-extras

```

  

2.  **Start the Backend:**

The backend runs by default on `0.0.0.0:8080`:

  

```bash

uv run start-backend

```

  

#### Frontend Setup

  

1.  **Install Dependencies:**

In the `chat-ui/` directory, install the required packages using [npm](https://nodejs.org/en/download):

  

```bash

cd chat-ui/

npm install

```

  

2.  **Configure the Frontend:**

Update the backend URL in `chat-ui/src/App.js` for testing:

  

```js

const  BACKEND_ROUTE = "http://localhost:8080/api/routes/chat/";

```

  

>  **Note:** Remember to change `BACKEND_ROUTE` back to `'api/routes/chat/'` after testing.

  

3.  **Start the Frontend:**

  

```bash

npm start

```

  

## 📁 Repo Structure

  

```plaintext

src/flare_ai_defai/

├── ai/ # AI Provider implementations

│ ├── base.py # Base AI provider interface

│ ├── gemini.py # Google Gemini integration

│ └── openrouter.py # OpenRouter integration

├── api/ # API layer

│ ├── middleware/ # Request/response middleware

│ └── routes/ # API endpoint definitions

├── attestation/ # TEE attestation

│ ├── vtpm_attestation.py # vTPM client

│ └── vtpm_validation.py # Token validation

├── blockchain/ # Blockchain operations

│ ├── explorer.py # Chain explorer client

│ └── flare.py # Flare network provider

├── prompts/ # AI system prompts & templates

│ ├── library.py # Prompt module library

│ ├── schemas.py # Schema definitions

│ ├── service.py # Prompt service module

│ └── templates.py # Prompt templates

├── exceptions.py # Custom errors

├── main.py # Primary entrypoint

└── settings.py # Configuration settings error

```

  

## 🚀 Deploy on TEE

  

Deploy on a [Confidential Space](https://cloud.google.com/confidential-computing/confidential-space/docs/confidential-space-overview) using AMD SEV.

  

### Prerequisites

  

-  **Google Cloud Platform Account:**

Access to the [`verifiable-ai-hackathon`](https://console.cloud.google.com/welcome?project=verifiable-ai-hackathon) project is required.

  

-  **Gemini API Key:**

Ensure your [Gemini API key](https://aistudio.google.com/app/apikey) is linked to the project.

  

-  **gcloud CLI:**

Install and authenticate the [gcloud CLI](https://cloud.google.com/sdk/docs/install).

  

### Environment Configuration

  

1.  **Set Environment Variables:**

Update your `.env` file with:

  

```bash

TEE_IMAGE_REFERENCE=ghcr.io/flare-foundation/flare-ai-defai:main  # Replace with your repo build image

INSTANCE_NAME=<PROJECT_NAME-TEAM_NAME>

```

  

2.  **Load Environment Variables:**

  

```bash

source .env

```

  

>  **Reminder:** Run the above command in every new shell session or after modifying `.env`. On Windows, we recommend using [git BASH](https://gitforwindows.org) to access commands like `source`.

  

3.  **Verify the Setup:**

  

```bash

echo $TEE_IMAGE_REFERENCE  # Expected output: Your repo build image

```

  

### Deploying to Confidential Space

  

Run the following command:

  

```bash

gcloud  compute  instances  create  $INSTANCE_NAME  \

--project=verifiable-ai-hackathon \

--zone=us-west1-b  \

--machine-type=n2d-standard-2 \

--network-interface=network-tier=PREMIUM,nic-type=GVNIC,stack-type=IPV4_ONLY,subnet=default  \

--metadata=tee-image-reference=$TEE_IMAGE_REFERENCE,\

tee-container-log-redirect=true,\

tee-env-GEMINI_API_KEY=$GEMINI_API_KEY,\

tee-env-GEMINI_MODEL=$GEMINI_MODEL,\

tee-env-WEB3_PROVIDER_URL=$WEB3_PROVIDER_URL,\

tee-env-FLARE_PRIVATE_KEY=$FLARE_PRIVATE_KEY,\

tee-env-FLARE_ADDRESS=$FLARE_ADDRESS,\

tee-env-SIMULATE_ATTESTATION=false  \

--maintenance-policy=MIGRATE \

--provisioning-model=STANDARD  \

--service-account=confidential-sa@verifiable-ai-hackathon.iam.gserviceaccount.com \

--scopes=https://www.googleapis.com/auth/cloud-platform  \

--min-cpu-platform="AMD Milan" \

--tags=flare-ai,http-server,https-server  \

--create-disk=auto-delete=yes,\

boot=yes,\

device-name=$INSTANCE_NAME,\

image=projects/confidential-space-images/global/images/confidential-space-debug-250100,\

mode=rw,\

size=11,\

type=pd-standard  \

--shielded-secure-boot \

--shielded-vtpm  \

--shielded-integrity-monitoring \

--reservation-affinity=any  \

--confidential-compute-type=SEV

```

  

#### Post-deployment

  

1. After deployment, you should see an output similar to:

  

```plaintext

NAME ZONE MACHINE_TYPE PREEMPTIBLE INTERNAL_IP EXTERNAL_IP STATUS

defai-team1 us-central1-c n2d-standard-2 10.128.0.18 34.41.127.200 RUNNING

```

  

2. It may take a few minutes for Confidential Space to complete startup checks. You can monitor progress via the [GCP Console](https://console.cloud.google.com/welcome?project=verifiable-ai-hackathon) logs.

Click on **Compute Engine** → **VM Instances** (in the sidebar) → **Select your instance** → **Serial port 1 (console)**.

  

When you see a message like:

  

```plaintext

INFO: Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)

```

  

the container is ready. Navigate to the external IP of the instance (visible in the **VM Instances** page) to access the Chat UI.

  

### 🔧 Troubleshooting

  

If you encounter issues, follow these steps:

  

1.  **Check Logs:**

  

```bash

gcloud compute instances get-serial-port-output $INSTANCE_NAME  --project=verifiable-ai-hackathon

```

  

2.  **Verify API Key(s):**

Ensure that all API Keys are set correctly (e.g. `GEMINI_API_KEY`).

  

3.  **Check Firewall Settings:**

Confirm that your instance is publicly accessible on port `80`.

