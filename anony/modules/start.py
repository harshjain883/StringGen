from pyrogram import filters, types
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import os

from anony import app, buttons, db

@app.on_message(filters.command(["start"]) & filters.private)
async def f_start(_, m: types.Message):
    # The URL should point to your hosted domain. 
    # For many cloud providers, the URL is provided via environment variables.
    webapp_url = os.environ.get("WEBAPP_URL", "[link removed]")

    # We extend the existing start_key with the Mini App launcher
    keyboard = buttons.start_key()
    
    # Adding the Web App button at the top of the existing keyboard
    keyboard.inline_keyboard.insert(0, [
        InlineKeyboardButton(
            text="🚀 Open String Gen Mini App",
            web_app=WebAppInfo(url=webapp_url)
        )
    ])

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
