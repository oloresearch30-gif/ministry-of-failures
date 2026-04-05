import os
import json

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ministry-of-failures-2025-secret")
    DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "1-7LOmRn2mZrsZNUBD0WbsrBgAqym-PQg")
    SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/ministry-of-failures-ab050d2a6922.json")

    @staticmethod
    def get_credentials_info():
        """Returns credentials dict — from env variable (Render) or file (local)."""
        json_str = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if json_str:
            return json.loads(json_str)
        return None