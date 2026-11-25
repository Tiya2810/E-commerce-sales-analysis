# Deploy on Streamlit Community Cloud

This repository is prepared for Streamlit Community Cloud. The app entrypoint is at the repository root, and its local CSV files and SQLite database are committed with the project.

## Create the app

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and choose **Create app**.
2. Select repository `Tiya2810/E-commerce-sales-analysis`.
3. Select branch `main`.
4. Set **Main file path** to `app.py`.
5. In **Advanced settings**, choose Python 3.12, then deploy.

The root `requirements.txt` pins Streamlit and limits major dependency upgrades to versions compatible with this project. `.streamlit/config.toml` provides the dashboard theme.

## If deployment fails

Open the app's **Manage app** page and copy the first build or runtime traceback from **Logs**. The log identifies whether the failure is package installation, app startup, or data loading; the exact error is needed to fix any remaining account or deployment-specific issue.
