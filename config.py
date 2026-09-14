import sys
from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Read credentials
_api_id_raw = getenv("API_ID")
API_HASH = getenv("API_HASH")

BOT_TOKEN = getenv("BOT_TOKEN")
MONGO_URI = getenv("MONGO_URI")

# Validation check for API credentials
if not _api_id_raw or not _api_id_raw.strip().isdigit() or int(_api_id_raw) == 0:
    sys.exit(
        "Critical Error: 'API_ID' missing hai ya invalid (0) hai. "
        "Apne .env file ya Config Vars mein correct integer API_ID set karein."
    )

if not API_HASH or not API_HASH.strip():
    sys.exit(
        "Critical Error: 'API_HASH' missing hai. "
        "Apne .env file ya Config Vars mein correct API_HASH string set karein."
    )

API_ID = int(_api_id_raw)

# Owner ID validation
_owner_id_raw = getenv("OWNER_ID", "7854213599")
OWNER_ID = int(_owner_id_raw) if _owner_id_raw and _owner_id_raw.strip().isdigit() else 7854213599

# Auto-format SUPPORT_CHAT to prevent ButtonUrlInvalid crash
_raw_support = getenv("SUPPORT_CHAT", "https://t.me/FallenX")
if not _raw_support or not _raw_support.strip():
    SUPPORT_CHAT = "https://t.me/FallenX"
else:
    _raw_support = _raw_support.strip()
    if _raw_support.startswith("@"):
        SUPPORT_CHAT = f"https://t.me/{_raw_support[1:]}"
    elif not _raw_support.startswith(("http://", "https://")):
        SUPPORT_CHAT = f"https://{_raw_support}"
    else:
        SUPPORT_CHAT = _raw_support
        
