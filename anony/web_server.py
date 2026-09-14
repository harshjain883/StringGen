import os
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Telegram Clients
from pyrogram import Client
from pyrogram.errors import (
    SessionPasswordNeeded as PyroSessionPass,
    PhoneCodeInvalid as PyroCodeInvalid,
    PhoneCodeExpired as PyroCodeExpired,
    PasswordHashInvalid as PyroPassInvalid,
)
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError as TeleSessionPass,
    PhoneCodeInvalidError as TeleCodeInvalid,
    PhoneCodeExpiredError as TeleCodeExpired,
    PasswordHashInvalidError as TelePassInvalid,
)
from telethon.sessions import StringSession

app_web = FastAPI(title="StringGen Bot Web Server")

# In-memory storage for pending client sessions
SESSION_STORAGE: Dict[str, Dict[str, Any]] = {}

# Locate StringGen/static folder dynamically
CURRENT_DIR = Path(__file__).resolve().parent  # /app/anony
PROJECT_ROOT = CURRENT_DIR.parent              # /app

# Check possible locations for StringGen/static or static
CANDIDATE_PATHS = [
    PROJECT_ROOT / "StringGen" / "static",
    PROJECT_ROOT / "static",
    CURRENT_DIR / "static",
]

STATIC_DIR = None
for path in CANDIDATE_PATHS:
    if (path / "index.html").is_file():
        STATIC_DIR = path
        break

if STATIC_DIR and STATIC_DIR.exists():
    app_web.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# --- Request Models ---
class SendOtpRequest(BaseModel):
    lib_type: str
    api_id: int
    api_hash: str
    phone_number: str


class VerifyOtpRequest(BaseModel):
    phone_number: str
    otp: str
    phone_code_hash: str


class Verify2faRequest(BaseModel):
    phone_number: str
    password: str


# --- Web Routes ---
@app_web.get("/")
async def serve_index():
    if STATIC_DIR:
        index_file = STATIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
    return JSONResponse(
        content={"status": "error", "message": "StringGen/static/index.html not found"},
        status_code=404,
    )


@app_web.get("/health")
async def health_check():
    return {"status": "ok", "service": "running"}


# --- API Routes for Mini App ---
@app_web.post("/api/send-otp")
async def send_otp(data: SendOtpRequest):
    phone = data.phone_number.strip().replace(" ", "")
    lib = data.lib_type.lower().strip()

    try:
        if lib == "pyrogram":
            client = Client(
                name=f"pyro_{phone}",
                api_id=data.api_id,
                api_hash=data.api_hash,
                in_memory=True,
            )
            await client.connect()
            sent_code = await client.send_code(phone)
            
            SESSION_STORAGE[phone] = {
                "lib": "pyrogram",
                "client": client,
                "phone_code_hash": sent_code.phone_code_hash,
            }
            return {"status": "otp_sent", "phone_code_hash": sent_code.phone_code_hash}

        elif lib == "telethon":
            client = TelegramClient(StringSession(), data.api_id, data.api_hash)
            await client.connect()
            sent_code = await client.send_code_request(phone)

            SESSION_STORAGE[phone] = {
                "lib": "telethon",
                "client": client,
                "phone_code_hash": sent_code.phone_code_hash,
            }
            return {"status": "otp_sent", "phone_code_hash": sent_code.phone_code_hash}

        else:
            raise HTTPException(status_code=400, detail="Invalid library type selected")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app_web.post("/api/verify-otp")
async def verify_otp(data: VerifyOtpRequest):
    phone = data.phone_number.strip().replace(" ", "")
    stored = SESSION_STORAGE.get(phone)

    if not stored:
        raise HTTPException(status_code=400, detail="Session expired or not initialized. Please re-send OTP.")

    lib = stored["lib"]
    client = stored["client"]

    try:
        if lib == "pyrogram":
            try:
                await client.sign_in(
                    phone_number=phone,
                    phone_code_hash=data.phone_code_hash,
                    phone_code=data.otp,
                )
                session_str = await client.export_session_string()
                await client.disconnect()
                SESSION_STORAGE.pop(phone, None)
                return {"status": "success", "session": session_str}
            except PyroSessionPass:
                return {"status": "2fa_required"}
            except (PyroCodeInvalid, PyroCodeExpired) as e:
                raise HTTPException(status_code=400, detail=str(e))

        elif lib == "telethon":
            try:
                await client.sign_in(
                    phone=phone,
                    code=data.otp,
                    phone_code_hash=data.phone_code_hash,
                )
                session_str = client.session.save()
                await client.disconnect()
                SESSION_STORAGE.pop(phone, None)
                return {"status": "success", "session": session_str}
            except TeleSessionPass:
                return {"status": "2fa_required"}
            except (TeleCodeInvalid, TeleCodeExpired) as e:
                raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app_web.post("/api/verify-2fa")
async def verify_2fa(data: Verify2faRequest):
    phone = data.phone_number.strip().replace(" ", "")
    stored = SESSION_STORAGE.get(phone)

    if not stored:
        raise HTTPException(status_code=400, detail="Session expired. Please start over.")

    lib = stored["lib"]
    client = stored["client"]

    try:
        if lib == "pyrogram":
            try:
                await client.check_password(password=data.password)
                session_str = await client.export_session_string()
                await client.disconnect()
                SESSION_STORAGE.pop(phone, None)
                return {"status": "success", "session": session_str}
            except PyroPassInvalid:
                raise HTTPException(status_code=400, detail="Invalid 2FA password")

        elif lib == "telethon":
            try:
                await client.sign_in(password=data.password)
                session_str = client.session.save()
                await client.disconnect()
                SESSION_STORAGE.pop(phone, None)
                return {"status": "success", "session": session_str}
            except TelePassInvalid:
                raise HTTPException(status_code=400, detail="Invalid 2FA password")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
