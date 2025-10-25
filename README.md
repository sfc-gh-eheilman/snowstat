# Accessible Snowflake Status (Deployable)

This folder contains a minimal, self-contained app ready for Streamlit Community Cloud.

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy to Streamlit Community Cloud

1. Create a new GitHub repo and push the contents of this `DEPLOY/` folder to it (files at repo root).
2. Go to `https://share.streamlit.io/` and connect the repo.
3. App file path: `streamlit_app.py` (at repo root).
4. Python version: 3.11 (provided via `.python-version`).
5. No secrets required. Optionally configure theme in `.streamlit/config.toml`.

## Contents
- `streamlit_app.py` (entrypoint)
- `lib/` (application modules)
- `.streamlit/` (theme + services order)
- `requirements.txt` (pinned)
- `.python-version` (3.11)
- `.gitignore` (sane defaults)

---
Built by Eric Heilman. This is an open-source community tool and not officially affiliated with Snowflake Inc.
