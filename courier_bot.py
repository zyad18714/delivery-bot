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
                username TEXT,
                full_name TEXT,
                iban TEXT,
                approved INTEGER DEFAULT 1,
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

# إضافة مندوب مع إيبان
@dp.message(Command("add"))
async def add_courier(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    try:
        parts = msg.text.split(maxsplit=3)
        user_id = int(parts[1])
        name = parts[2]
        iban = parts[3] if len(parts) > 3 else ""
        
        async with aiosqlite.connect("couriers.db") as db:
            await db.execute("""INSERT OR REPLACE INTO couriers 
                (user_id, username, full_name, iban, approved, added_at) 
                VALUES (?, ?, ?, ?, 1, ?)""",
                (user_id, None, name, iban, datetime.now().isoformat()))
            await db.commit()
        await msg.answer(f"✅ تم إضافة {name} (ID: {user_id})")
    except:
        await msg.answer("الصيغة: /add ID الاسم الايبان")

# قائمة المناديب
@dp.message(Command("list"))
async def list_couriers(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    async with aiosqlite.connect("couriers.db") as db:
        async with db.execute("SELECT user_id, full_name, iban FROM couriers") as cursor:
            rows = await cursor.fetchall()
    text = "المناديب:\n" + "\n".join([f"• {r[1]} ({r[0]}) | IBAN: {r[2] or 'غير محدد'}" for r in rows])
    await msg.answer(text or "لا يوجد مناديب")

# تقرير أسبوعي
@dp.message(Command("weekly"))
async def weekly_report(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    async with aiosqlite.connect("couriers.db") as db:
        async with db.execute("""
            SELECT c.full_name, c.iban, SUM(e.amount) as total
            FROM earnings e
            JOIN couriers c ON e.courier_id = c.user_id
            WHERE e.date > ?
            GROUP BY c.user_id
        """, (week_ago,)) as cursor:
            rows = await cursor.fetchall()
    text = "📊 تقرير أسبوعي:\n\n"
    for r in rows:
        text += f"• {r[0]}\n  المبلغ: {r[2]:.2f} ريال\n  IBAN: {r[1] or 'غير محدد'}\n\n"
    await msg.answer(text or "لا يوجد أرباح هذا الأسبوع")

async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
