# Video Share — MVP

## Backend
Install Python 3.11+, FFmpeg on PATH.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Frontend
Install Node.js 20+.

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 . For remote backend set `NEXT_PUBLIC_API_URL` at build time and `ALLOWED_ORIGINS` on API.

## Scope and limitations
- Functional video metadata and single-video download endpoints via yt-dlp, subject to extractor availability, rights and provider policies. No credentials, cookies, DRM circumvention or private-video access.
- UI allows collecting links, selecting and sequential downloading; ZIP and full channel are not implemented yet (buttons explain limitation).
- Frontend uses browser-memory state; no persistent history or login yet.
- Backend is a development MVP, **not production hardened**. Before public deployment: enforce DNS/IP allowlists at the actual downloader network layer including redirect chains, restrict egress, add auth, rate limits, job queue, malware scanning, disk/time/byte quotas, logging, cleanup and abuse controls. Do not expose this server publicly as-is.
- No guarantee of support for every URL on the six platforms. YouTube and other services may restrict third-party downloading.
