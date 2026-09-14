import os
from pyrogram import filters, types
from pyrogram.types import InlineKeyboardButton, WebAppInfo

from anony import app, buttons, db

# Railway URL set as default
DEFAULT_WEBAPP_URL = "https://stringgen-production.up.railway.app"


@app.on_message(filters.command(["start"]) & filters.private)
async def f_start(_, m: types.Message):
    # Fetch from env if provided, else use the Railway public URL
    webapp_url = os.environ.get("WEBAPP_URL", DEFAULT_WEBAPP_URL).strip()

    # Ensure https protocol prefix exists
    if not webapp_url.startswith("https://"):
        webapp_url = f"https://{webapp_url.replace('http://', '')}"

    keyboard = buttons.start_key()

    # Add Mini App launch button at the top
    keyboard.inline_keyboard.insert(
        0,
        [
            InlineKeyboardButton(
                text="🚀 Open String Gen Mini App",
                web_app=WebAppInfo(url=webapp_url),
            )
        ],
    )

    await m.reply_text(
        text=(
            f"Hey {m.from_user.first_name},\n\n"
            f"This is {app.me.mention},\n"
            "An open source session generator bot.\n\n"
            "You can now generate sessions faster using our **Telegram Mini App** below!"
        ),
        reply_markup=keyboard,
    )

    await db.add_user(m.from_user.id)
