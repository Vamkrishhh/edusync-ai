# EduSync AI — Deployment Guide

This guide provides step-by-step instructions for deploying EduSync AI to Streamlit Community Cloud.

---

## Prerequisites

- GitHub account: [https://github.com/Vamkrishhh](https://github.com/Vamkrishhh)
- Streamlit Community Cloud account: [https://share.streamlit.io/](https://share.streamlit.io/)
- (Optional) Google Gemini API key from [AI Studio](https://aistudio.google.com/)

---

## Step 1: Repository Setup (Completed)

✅ Repository initialized with Git  
✅ All application code, tests, and documentation committed  
✅ `.gitignore` configured to exclude secrets, databases, and temporary files

---

## Step 2: Push to GitHub

The repository should be pushed to:
- **Repository URL:** `https://github.com/Vamkrishhh/edusync-ai`
- **Branch:** `main`

### Commands to Push

```bash
# Navigate to project directory
cd "path/to/Multi tool agent"

# Verify Git status
git status

# If needed, add any remaining files
git add .
git commit -m "docs: add deployment guide and secrets example"

# Push to GitHub
git push -u origin main
```

---

## Step 3: Deploy on Streamlit Community Cloud

### 3.1 Log In

1. Go to [https://share.streamlit.io/](https://share.streamlit.io/)
2. Sign in with your GitHub account

### 3.2 Create New App

1. Click **"New app"** button
2. Configure the deployment:

   **Repository Settings:**
   - Repository: `Vamkrishhh/edusync-ai`
   - Branch: `main`
   - Main file path: `app.py`

   **Advanced Settings:**
   - Python version: `3.12` (or latest available)
   
3. Click **"Deploy!"**

### 3.3 Optional: Configure Secrets (For AI Mode)

If you want to enable Gemini AI features:

1. While app is deploying, click **"Advanced settings"**
2. Find the **"Secrets"** section
3. Add your secrets in TOML format:

```toml
GEMINI_API_KEY = "your_actual_gemini_api_key_here"
GEMINI_MODEL = "gemini-2.5-flash"
```

4. Click **"Save"**

**Note:** The application works perfectly in Demo Mode without any API key.

---

## Step 4: Verify Deployment

Once deployment completes:

1. ✅ App loads without errors
2. ✅ Click **"📥 Load Sample DBMS Material"** in sidebar
3. ✅ Navigate to all 7 pages (Dashboard, Document Library, AI Assistant, Quiz Generator, Performance, Study Planner, Progress Tracker)
4. ✅ Submit a quiz and verify scores are recorded
5. ✅ Generate a study plan and verify tasks appear
6. ✅ Complete a task checkbox and verify it persists

### Expected URL Format

Your deployed app will be available at:
```
https://[auto-generated-name].streamlit.app/
```

Or you can set a custom URL subdomain in the Streamlit Cloud settings.

---

## Important Notes for Cloud Deployment

### ⚠️ Ephemeral Storage

- **SQLite data is NOT persistent** on Streamlit Community Cloud
- Database resets on app restart or redeployment
- User-uploaded documents and quiz history are temporary
- For production with data persistence, use PostgreSQL or external database

### 🔒 Security

- Never commit `.env` or `.streamlit/secrets.toml` to Git
- API keys should only be configured via Streamlit Cloud secrets UI
- The `.gitignore` file is configured to exclude all sensitive files

### 📊 Resource Limits

Streamlit Community Cloud has the following limits:
- **CPU:** Shared resources
- **Memory:** 1 GB RAM
- **Storage:** Ephemeral (no persistent disk)
- **Idle timeout:** Apps sleep after inactivity

For production deployments with higher traffic:
- Consider **Streamlit for Teams** (paid tier)
- Or self-host on AWS/GCP/Azure with PostgreSQL backend

---

## Troubleshooting

### Build Fails with Dependency Errors

Check that `requirements.txt` has compatible versions:
```
streamlit>=1.35.0,<=1.65.0
pypdf>=5.0.0,<=6.20.0
numpy>=1.26.0,<=2.5.3
scikit-learn>=1.5.0,<=1.9.1
google-genai>=2.0.0,<=2.29.0
pandas>=2.2.0,<=3.0.6
python-dotenv>=1.0.0,<=1.2.3
pytest>=8.0.0,<=9.1.1
```

### App Shows "Demo Mode" Even with API Key

1. Verify secret key name is exactly `GEMINI_API_KEY` (case-sensitive)
2. Check for extra spaces or quotes in the secrets.toml
3. Restart the app after adding secrets

### Database Resets After Navigation

This is expected behavior on Streamlit Cloud. SQLite storage is in-memory and ephemeral. For persistent storage, migrate to PostgreSQL.

---

## Post-Deployment Checklist

- [ ] Repository pushed to GitHub
- [ ] App deployed on Streamlit Cloud
- [ ] All 7 pages load without errors
- [ ] Sample data loads successfully
- [ ] Quiz submission works
- [ ] Study plan generation works
- [ ] Navigation buttons work across pages
- [ ] (Optional) Gemini API key configured for AI Mode

---

## Updating the Deployed App

To update your deployed application:

```bash
# Make changes locally
git add .
git commit -m "feat: your change description"
git push

# Streamlit Cloud automatically redeploys on push
```

The app will automatically rebuild and redeploy when you push to the `main` branch.

---

## Support Resources

- **Streamlit Documentation:** [https://docs.streamlit.io/](https://docs.streamlit.io/)
- **Streamlit Community Forum:** [https://discuss.streamlit.io/](https://discuss.streamlit.io/)
- **EduSync AI GitHub Issues:** [https://github.com/Vamkrishhh/edusync-ai/issues](https://github.com/Vamkrishhh/edusync-ai/issues)
- **Gemini API Documentation:** [https://ai.google.dev/docs](https://ai.google.dev/docs)

---

**Last Updated:** 2026-10-15  
**Repository:** https://github.com/Vamkrishhh/edusync-ai
