# Deploy: Azure (API) + GitHub (code / optional static UI)

The app is one FastAPI service that serves the checklist UI from `app/static/` and the `/api/*` routes. You can deploy **everything on Azure** (simplest), or host the **static files on GitHub Pages** and point them at the API (requires CORS + `config.js`).

---

## 1. Push code to GitHub

1. Create a new repository on GitHub (empty, no README required).
2. From your machine (install [Git](https://git-scm.com/) if needed):

```powershell
cd "C:\xahive compliance Project\coding"
git init
git add .
git commit -m "Initial import: Xahive compliance checklist"
git branch -M main
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

Ensure `.env` stays **untracked** (it is in `.gitignore`). Never commit API keys.

---

## 2. Deploy the backend to Azure (Docker you already have)

Build context must be the **`backend`** folder (where `Dockerfile` and `modules/` live).

```powershell
cd "C:\xahive compliance Project\coding\backend"
docker build -t xahive-compliance-api .
docker run --rm -p 8000:8000 -e OPENAI_API_KEY=your-key-here xahive-compliance-api
```

### Azure Container Apps or App Service (containers)

1. Create an **Azure Container Registry** (ACR), push the image:  
   `docker tag` / `docker push` your ACR login server image name.
2. Create **Container Apps** or **Web App for Containers**, pull from ACR, port **8000**.
3. **Application settings / Environment variables** (not `.env` in git):
   - `OPENAI_API_KEY` — your OpenAI key
   - Optional: `OPENAI_NARRATIVE_MODEL`, `OPENAI_NARRATIVE_SEED`
   - If the UI is only on Azure: you do **not** need `CORS_ORIGINS`.

Your public URL will look like `https://<app>.azurecontainerapps.io` or `https://<app>.azurewebsites.net`. Opening that URL loads the checklist and API on the **same origin** — no change to `config.js` required.

---

## 3. Optional: static site on GitHub Pages + API on Azure

Use this when the HTML is served from `https://<user>.github.io/<repo>/` and the API is on Azure.

1. In `backend/app/static/config.js`, set (no trailing slash):

   ```js
   window.__API_BASE__ = 'https://YOUR-AZURE-API-HOST';
   ```

2. On the **Azure** app, add an environment variable:

   - `CORS_ORIGINS` = `https://YOUR_USER.github.io`  
     (if the Pages URL uses a project path, you may need `https://YOUR_USER.github.io,https://YOUR_USER.github.io/YOUR_REPO` — test in the browser Network tab if preflight fails.)

3. Enable **GitHub Pages** on the repo (e.g. branch `gh-pages` or `/docs` folder). Publish the contents of `backend/app/static/` **plus** `index.html` from the same folder layout so `./static/config.js` still resolves, **or** copy the whole `static` tree and place `index.html` at the site root as required by your Pages setup.

Same-origin note: GitHub Pages **cannot** host the Python API; only the static files.

---

## 4. CI/CD (optional)

Many teams use **GitHub Actions** to build the Docker image on push and deploy to Azure with the [Azure login](https://github.com/Azure/login) action. Wire that to your subscription and target (Container Apps / App Service). This repo does not enforce a single pipeline; choose what matches your Azure subscription.

---

## Summary

| Goal | What to do |
|------|------------|
| Fastest “online” | Docker → Azure, one URL for UI + API |
| Code backup + collaboration | Push `coding/` to GitHub |
| UI on GitHub, API on Azure | Edit `config.js` + set `CORS_ORIGINS` on Azure |
