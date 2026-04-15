# Deploy Repo-Sage Web App (3 Commands!)

## Fastest Way to Deploy

```bash
# 1. Install Streamlit
uv pip install streamlit

# 2. Run locally (test first)
streamlit run app.py

# 3. Deploy to cloud (free!)
# - Push to GitHub
# - Go to share.streamlit.io
# - Connect your repo
# - Add OPENAI_API_KEY in secrets
# - Done!
```

---

## Your App URL

After deployment: `https://repo-sage-yourname.streamlit.app`

Share it with anyone - no auth needed!

---

## Files You Need

✅ `app.py` - Already created
✅ `requirements.txt` - Already created
✅ `.streamlit/config.toml` - Already created

All set! Just push to GitHub and deploy.

---

## Test Locally First

```bash
streamlit run app.py
```

Open: http://localhost:8501

Try:
1. Load "Java Design Patterns" repo
2. Ask: "What is the Singleton pattern?"
3. See AI answer!

---

## Deploy in 5 Minutes

1. **Push code**: `git push`
2. **Go to**: share.streamlit.io
3. **Sign in**: with GitHub
4. **New app**: Select your repo
5. **Add secret**: OPENAI_API_KEY
6. **Deploy**: Click deploy button
7. **Share**: Get your URL!

---

**It's that simple!** 🚀

No servers, no Docker, no config - just push and deploy!
