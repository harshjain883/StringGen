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

OWNER_ID = int(getenv("OWNER_ID", 7854213599))
SUPPORT_CHAT = getenv("SUPPORT_CHAT", "https://t.me/FallenX")
