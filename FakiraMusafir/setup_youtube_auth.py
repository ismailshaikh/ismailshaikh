# -*- coding: utf-8 -*-
"""
One-time OAuth setup for YouTube Data API v3 (FREE).

Steps:
1. Go to https://console.cloud.google.com/ -> create a project.
2. Enable "YouTube Data API v3".
3. Create OAuth client credentials (type: Desktop app).
4. Download the JSON and save it as:
   FakiraMusafir/.credentials/client_secret.json
   (or point YOUTUBE_CLIENT_SECRETS_FILE in .env to it)
5. Run: python setup_youtube_auth.py
   A browser window opens - log in with the channel's Google account
   and approve. A token.json is saved in .credentials/ for reuse.
"""
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]


def get_authenticated_service():
    creds = None
    token_path = config.YOUTUBE_TOKEN_FILE
    if Path_exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path_exists(config.YOUTUBE_CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"Missing {config.YOUTUBE_CLIENT_SECRETS_FILE}. "
                    "Download OAuth client_secret.json from Google Cloud Console first."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                config.YOUTUBE_CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=creds)


def Path_exists(p) -> bool:
    from pathlib import Path
    return Path(p).exists()


if __name__ == "__main__":
    service = get_authenticated_service()
    resp = service.channels().list(part="snippet", mine=True).execute()
    if resp.get("items"):
        title = resp["items"][0]["snippet"]["title"]
        print(f"[setup_youtube_auth] Authenticated as channel: {title}")
    print(f"[setup_youtube_auth] Token saved to {config.YOUTUBE_TOKEN_FILE}")
