# Face Consistency Studio 📸

An AI-powered wedding portrait studio web application that generates consistent, stylized wedding portraits from a single reference photo while faithfully preserving the subject's facial identity.

---

## 🌟 Key Features

- **Multi-Model Provider Chain**:
  - **Primary**: [fal.ai](https://fal.ai) FLUX PuLID (`fal-ai/flux-pulid`) with identity guidance weight tuning.
  - **Fallback**: [Google Gemini](https://aistudio.google.com) Imagen/GenAI models (`gemini-nano-banana-2.1`).
- **Curated Wedding Scenes**:
  - **Luxury Cinematic**: Grand venue, candlelit ambience, formal editorial wedding attire.
  - **Beach / Destination**: Oceanfront golden hour, seaside backdrop, airy natural light.
  - **Traditional Indian**: Ornate ceremonial attire, detailed gold jewelry, vibrant floral decor.
- **Client Experience**:
  - Drag-and-drop reference photo upload with real-time preview & consent confirmation.
  - Live per-scene async generation polling with error handling and retry actions.
  - Side-by-side reference comparison, high-resolution modal lightbox, single portrait downloads, and full `.zip` bundle export.
- **Privacy & Cleanup**:
  - Ephemeral session storage with automatic 30-minute expiration and instant session reset.
  - API keys stay securely on the backend server.

---

## 📁 Repository Structure

```
faceAi/
├── backend.py            # FastAPI backend server with model chain and endpoints
├── requirements.txt      # Python backend dependencies
├── .python-version       # Python version specification (3.12.5)
├── render.yaml           # Render Blueprint for automated deployment
├── build.sh              # Unified build script (single web service option)
├── .env.example          # Sample environment configuration template
├── data/                 # Ephemeral runtime storage for uploads and outputs
│   ├── uploads/
│   └── generated/
└── faceAi-client/        # React 19 + TypeScript + Vite frontend
    ├── package.json
    ├── vite.config.ts
    ├── index.html
    └── src/
        ├── components/   # Upload, scene selection, generation, results, lightbox
        ├── lib/api.ts    # Typed API client
        └── types.ts      # Shared TypeScript data models
```

---

## 🚀 Quick Local Setup

### 1. Backend Setup
1. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create your `.env` file from the example:
   ```bash
   cp .env.example .env
   ```
   Add your API keys to `.env`:
   - `FAL_KEY`: Get from [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys) (recommended)
   - `GEMINI_API_KEY`: Get from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
4. Start the backend:
   ```bash
   uvicorn backend:app --reload --port 8000
   ```

### 2. Frontend Setup
1. In a new terminal window:
   ```bash
   cd faceAi-client
   npm install
   npm run dev
   ```
2. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## ☁️ Deploying to Render

You can deploy to Render using any of the following methods:

### Option 1: Render Blueprint (Recommended — Deploys Both Frontend & Backend)

1. Push this repository to GitHub.
2. Log in to [Render](https://dashboard.render.com).
3. Click **New +** > **Blueprint**.
4. Connect your GitHub repository (`faceAi-studio`).
5. Render reads [`render.yaml`](./render.yaml) and automatically creates:
   - **`faceai-backend`** (Python Web Service)
   - **`faceai-frontend`** (Static Site with automatic API URL wiring)
6. When prompted in the Render Dashboard, fill in your environment secret:
   - `FAL_KEY`: Your fal.ai API key
   - `GEMINI_API_KEY`: Your Gemini API key (optional fallback)
7. Click **Apply**. Both services will build and deploy!

---

### Option 2: Manual Two-Service Setup on Render

#### Step A: Deploy Backend (Web Service)
1. In Render, click **New +** > **Web Service**.
2. Select your repository.
3. Configure:
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend:app --host 0.0.0.0 --port $PORT`
4. In **Environment Variables**, add:
   - `FAL_KEY`: `<your_fal_key>`
   - `GEMINI_API_KEY`: `<your_gemini_key>` (optional)
   - `IMAGE_MODEL_PRIMARY`: `fal:fal-ai/flux-pulid`
   - `IMAGE_MODEL_FALLBACK`: `gemini:gemini-nano-banana-2.1`
   - `FAL_ID_WEIGHT`: `1`
5. Click **Deploy Web Service** and note your backend URL (e.g., `https://faceai-backend.onrender.com`).

#### Step B: Deploy Frontend (Static Site)
1. In Render, click **New +** > **Static Site**.
2. Select your repository.
3. Configure:
   - **Root Directory**: `faceAi-client`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
4. In **Redirects / Rewrites**, add:
   - **Type**: Rewrite
   - **Source**: `/*`
   - **Destination**: `/index.html`
5. In **Environment Variables**, add:
   - `VITE_API_BASE`: `https://faceai-backend.onrender.com` (your backend URL from Step A)
6. Click **Deploy Static Site**.

---

### Option 3: Unified Single Service (1 URL for both Frontend + Backend)

If you prefer deploying a single Render Web Service where FastAPI serves both the API and the pre-built React frontend:
1. In Render, click **New +** > **Web Service**.
2. Select your repository.
3. Configure:
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh` (or `pip install -r requirements.txt && cd faceAi-client && npm install && npm run build && cd ..`)
   - **Start Command**: `uvicorn backend:app --host 0.0.0.0 --port $PORT`
4. Add your environment variables (`FAL_KEY`, `GEMINI_API_KEY`).
5. Click **Deploy Web Service**.

---

## 🔐 Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `FAL_KEY` | Recommended | — | fal.ai API key for FLUX PuLID identity generation |
| `GEMINI_API_KEY` | Optional | — | Google Gemini API key for fallback image generation |
| `IMAGE_MODEL_PRIMARY` | No | `fal:fal-ai/flux-pulid` | Primary model identifier (`provider:model`) |
| `IMAGE_MODEL_FALLBACK` | No | `gemini:gemini-nano-banana-2.1` | Fallback model identifier |
| `FAL_ID_WEIGHT` | No | `1.0` | PuLID identity preservation weight (0.0 – 1.0) |
| `CORS_ORIGINS` | No | `*` / onrender regex | Comma-separated allowed origins for frontend |
| `PORT` | Auto (Render) | `8000` | Port for the backend server |
| `VITE_API_BASE` | Yes (Static Site) | `""` | Backend URL for standalone frontend client |

---

## 📄 License
MIT
