import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import aiosqlite
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("COURIER_BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip()]

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def init_db():
    async with aiosqlite.connect("couriers.db") as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS couriers (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                approved INTEGER DEFAULT 1,
                added_at TEXT
            );
        """)
        await db.commit()

# أمر الأدمن لإضافة مندوب
@dp.message(Command("add"))
async def add_courier(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return await msg.answer("للأدمن فقط.")
    
    try:
        parts = msg.text.split(maxsplit=2)
        user_id = int(parts[1])
        name = parts[2] if len(parts) > 2 else "Unknown"
        
        async with aiosqlite.connect("couriers.db") as db:
            await db.execute("""INSERT OR REPLACE INTO couriers 
                (user_id, username, full_name, approved, added_at) 
                VALUES (?, ?, ?, 1, ?)""",
                (user_id, None, name, datetime.now().isoformat()))
            await db.commit()
        
        await msg.answer(f"✅ تم إضافة المندوب: {user_id} ({name})")
        try:
            await bot.send_message(user_id, "🎉 تم تفعيل حسابك كمندوب!\nستصلك الطلبات قريباً.")
        except:
            pass
    except:
        await msg.answer("الصيغة: /add USER_ID الاسم")

# أمر عرض المناديب
@dp.message(Command("list"))
async def list_couriers(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    async with aiosqlite.connect("couriers.db") as db:
        async with db.execute("SELECT user_id, full_name FROM couriers") as cursor:
            rows = await cursor.fetchall()
    text = "المناديب المسجلين:\n" + "\n".join([f"{r[0]} - {r[1]}" for r in rows])
    await msg.answer(text or "لا يوجد مناديب بعد.")

async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
