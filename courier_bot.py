import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command 
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import aiosqlite
import os
from dotenv import load_dotenv
from datetime import datetime
import requests  # للتواصل مع بوت الطلبات

load_dotenv()
TOKEN = os.getenv("COURIER_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ORDERS_BOT_URL = os.getenv("ORDERS_BOT_URL")  # رابط webhook بوت الطلبات

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def init_db():
    async with aiosqlite.connect("couriers.db") as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS couriers (user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT);
            CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, customer_id INTEGER, details TEXT, fee TEXT, pickup TEXT, dropoff TEXT, status TEXT DEFAULT 'pending');
        """)
        await db.commit()

@dp.message(Command("start"))
async def start(msg: Message):
    user_id = msg.from_user.id
    async with aiosqlite.connect("couriers.db") as db:
        await db.execute("INSERT OR IGNORE INTO couriers VALUES (?, ?, ?)", 
                        (user_id, msg.from_user.username, msg.from_user.full_name))
        await db.commit()
    await msg.answer("✅ تم تسجيلك كمندوب.")

@dp.callback_query(F.data.startswith("accept_"))
async def accept_order(callback: CallbackQuery):
    order_id = callback.data.split("_")[1]
    user_id = callback.from_user.id
    username = callback.from_user.username or str(user_id)
    
    async with aiosqlite.connect("couriers.db") as db:
        async with db.execute("SELECT status FROM orders WHERE order_id = ?", (order_id,)) as cursor:
            result = await cursor.fetchone()
            if result and result[0] != 'pending':
                return await callback.answer("❌ الطلب تم أخذه", show_alert=True)
        
        await db.execute("UPDATE orders SET status = 'taken', taken_by = ? WHERE order_id = ?", (user_id, order_id))
        await db.commit()
    
    await callback.message.edit_text(callback.message.text + f"\n\n✅ **أخذه:** @{username}")
    await callback.answer("🎉 أنت المسؤول عن الطلب!", show_alert=True)
    
    # إشعار بوت الطلبات
    try:
        requests.post(f"{ORDERS_BOT_URL}/order_taken", json={"order_id": order_id, "courier": username})
    except:
        pass

async def main():
    await init_db()
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
