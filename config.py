import os

class Config:
    # ── Flask ─────────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "ministry-of-failures-2025-secret")

    # ── Google Drive ──────────────────────────────────────────────────────────
    # Path to your Google Service Account JSON key file
    SERVICE_ACCOUNT_FILE = os.environ.get(
        "GOOGLE_SERVICE_ACCOUNT_FILE",
        "credentials/ministry-of-failures-ab050d2a6922.json"
    )

    # The Google Drive FOLDER ID where files are stored and uploaded to.
    # Get this from the URL: drive.google.com/drive/folders/<FOLDER_ID>
    DRIVE_FOLDER_ID = os.environ.get(
        "DRIVE_FOLDER_ID",
        "1-7LOmRn2mZrsZNUBD0WbsrBgAqym-PQg"
    )
