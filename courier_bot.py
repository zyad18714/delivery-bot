import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
import aiosqlite
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
                full_name TEXT,
                iban TEXT,
                added_at TEXT
            );
            CREATE TABLE IF NOT EXISTS earnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                courier_id INTEGER,
                order_id TEXT,
                amount REAL,
                date TEXT
            );
        """)
        await db.commit()

@dp.message(Command("add"))
async def add_courier(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        parts = msg.text.split()
        user_id = int(parts[1])
        iban = parts[-1]  # آخر كلمة = الإيبان
        full_name = " ".join(parts[2:-1])  # كل اللي في الوسط = الاسم
        
        if not full_name:
            full_name = "غير محدد"
        
        async with aiosqlite.connect("couriers.db") as db:
            async with db.execute("SELECT user_id FROM couriers WHERE user_id = ?", (user_id,)) as cursor:
                if await cursor.fetchone():
                    return await msg.answer("⚠️ المندوب موجود مسبقاً.")
            
            await db.execute("""INSERT INTO couriers 
                (user_id, full_name, iban, added_at) 
                VALUES (?, ?, ?, ?)""",
                (user_id, full_name, iban, datetime.now().isoformat()))
            await db.commit()
        
        await msg.answer(f"✅ تم إضافة {full_name} (ID: {user_id})\nIBAN: {iban}")
    except:
        await msg.answer("الصيغة:\n/add ID الاسم الكامل الايبان\nمثال:\n/add 123456789 محمد علي SA89723743789234897349782")

@dp.message(Command("list"))
async def list_couriers(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    async with aiosqlite.connect("couriers.db") as db:
        async with db.execute("SELECT user_id, full_name, iban FROM couriers ORDER BY added_at DESC") as cursor:
            rows = await cursor.fetchall()
    if not rows:
        return await msg.answer("لا يوجد مناديب.")
    
    text = "📋 **المناديب المسجلين:**\n\n"
    for r in rows:
        text += f"• {r[1]} (ID: {r[0]})\n"
        if r[2]:
            text += f"  IBAN: `{r[2]}`\n\n"   # ← قابل للنسخ
        else:
            text += "  IBAN: غير محدد\n\n"
    
    await msg.answer(text, parse_mode="Markdown")
    
@dp.message(Command("delete"))
async def delete_courier(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        user_id = int(msg.text.split()[1])
        async with aiosqlite.connect("couriers.db") as db:
            await db.execute("DELETE FROM couriers WHERE user_id = ?", (user_id,))
            await db.commit()
        await msg.answer(f"🗑️ تم حذف المندوب {user_id}")
    except:
        await msg.answer("الصيغة: /delete ID")

async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
