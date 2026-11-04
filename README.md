
# JARVIS Dashboard — local/cloud AI starter

Vue 3 + Vite dashboard with a Django REST Framework backend. This version supports
local Ollama and an NVIDIA-compatible hosted chat-completions API.

## Privacy and provider selection

The backend defaults to `privacy_mode: "local"` and sends prompts to Ollama on
`127.0.0.1:11434`.

Cloud processing is never enabled implicitly. To use NVIDIA, the frontend must
send `allow_cloud: true` and choose `privacy_mode: "cloud"` or `"hybrid"`.

- `local`: Ollama only.
- `cloud`: NVIDIA only, but only with `allow_cloud: true`.
- `hybrid`: NVIDIA first only with `allow_cloud: true`; if NVIDIA fails, it falls
  back to Ollama. Without permission, it stays local.

This is an explicit-consent routing design, not a complete sensitive-data detector.
Do not send confidential information to a hosted provider unless you have reviewed
its applicable data terms.

## Requirements

- Python 3.10+
- Node.js 20+
- Ollama installed and running on the same PC
- Optional: NVIDIA API key and access to the configured model

## 1. Start local Ollama

```powershell
ollama pull qwen2.5:1.5b-instruct
ollama run qwen2.5:1.5b-instruct
```

You can exit the model chat with `/bye`. Ollama should remain running in the
background. Keep its API bound to localhost; do not expose port 11434 publicly.

## 2. Backend (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend\.env`. Set `NVIDIA_API_KEY` only if you want to enable hosted AI.
The default model value is `nvidia/nemotron-3-ultra-550b-a55b`; verify that this
model is enabled for your NVIDIA account.

Then:

```powershell
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

## 3. Frontend (second PowerShell window)

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL Vite prints (normally http://localhost:5173).

## 4. Chat API request examples

Local-only (default and safest):

```json
{
  "message": "Hello JARVIS",
  "history": [],
  "privacy_mode": "local",
  "allow_cloud": false
}
```

Explicitly permit NVIDIA, with local fallback:

```json
{
  "message": "Explain this programming concept",
  "history": [],
  "privacy_mode": "hybrid",
  "allow_cloud": true
}
```

The response includes `answer`, `model`, and `provider` (`local`, `nvidia`, or
`local_fallback`).

## Notes

- This starter is for local development only. It does not yet implement user login,
  durable conversation history, or production deployment.
- The Django API allows the local Vite dev origin by default and should bind to
  localhost during development.
- Never put NVIDIA API keys in frontend code.
- Do not expose Django's development server, Vite, or Ollama to the internet.


## Frontend privacy selector

The dashboard now includes Local, Hybrid, and Cloud modes plus an explicit cloud-permission checkbox. Local is selected by default. In Hybrid or Cloud mode, the checkbox must be enabled before a request can be sent to NVIDIA. The response shows which provider/model answered.
=======
# voiceAssistant
django voice assistant application

