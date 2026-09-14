import os
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pyrogram import Client, errors
from telethon import TelegramClient, errors as telerror
from telethon.sessions import StringSession

app_web = FastAPI()

# Temporary storage for active authentication attempts
# In production, consider using Redis for TTL support
sessions = {}

class AuthRequest(BaseModel):
    lib_type: str  # 'pyrogram' or 'telethon'
    api_id: int
    api_hash: str
    phone_number: str

class OTPRequest(BaseModel):
    phone_number: str
    otp: str
    phone_code_hash: str = None

class PasswordRequest(BaseModel):
    phone_number: str
    password: str

@app_web.post("/api/send-otp")
async def send_otp(data: AuthRequest):
    try:
        if data.lib_type == "pyrogram":
            client = Client(":memory:", api_id=data.api_id, api_hash=data.api_hash, in_memory=True)
            await client.connect()
            code = await client.send_code(data.phone_number)
            sessions[data.phone_number] = {"client": client, "type": "pyrogram", "hash": code.phone_code_hash}
            return {"phone_code_hash": code.phone_code_hash}
        else:
            client = TelegramClient(StringSession(), data.api_id, data.api_hash)
            await client.connect()
            code = await client.send_code_request(data.phone_number)
            sessions[data.phone_number] = {"client": client, "type": "telethon", "hash": code.phone_code_hash}
            return {"phone_code_hash": code.phone_code_hash}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app_web.post("/api/verify-otp")
async def verify_otp(data: OTPRequest):
    sess = sessions.get(data.phone_number)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found. Restart process.")
    
    client = sess["client"]
    try:
        if sess["type"] == "pyrogram":
            await client.sign_in(data.phone_number, sess["hash"], data.otp)
            string_session = await client.export_session_string()
        else:
            await client.sign_in(data.phone_number, data.otp)
            string_session = client.session.save()
            
        return {"status": "success", "session": string_session}
    except (errors.SessionPasswordNeeded, telerror.SessionPasswordNeededError):
        return {"status": "2fa_required"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app_web.post("/api/verify-2fa")
async def verify_2fa(data: PasswordRequest):
    sess = sessions.get(data.phone_number)
    if not sess:
        raise HTTPException(status_code=404, detail="Session expired.")
    
    client = sess["client"]
    try:
        if sess["type"] == "pyrogram":
            await client.check_password(data.password)
            string_session = await client.export_session_string()
        else:
            await client.sign_in(password=data.password)
            string_session = client.session.save()
            
        return {"status": "success", "session": string_session}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount static files
if os.path.exists("static"):
    app_web.mount("/static", StaticFiles(directory="static"), name="static")
