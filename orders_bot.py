import asyncio

import logging

from aiogram import Bot, Dispatcher, types, F

from aiogram.filters import Command

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

import os

from dotenv import load_dotenv

import requests

load_dotenv()

TOKEN = os.getenv("ORDERS_BOT_TOKEN")

COURIER_BOT_URL = os.getenv("COURIER_BOT_URL")  # رابط بوت المناديب (مثلاً https://your-railway-url.up.railway.app)

bot = Bot(token=TOKEN)

dp = Dispatcher()

@dp.message(Command("start"))

async def start(msg: Message):

    keyboard = InlineKeyboardMarkup(inline_keyboard=[

        [InlineKeyboardButton(text="🍰 عرض المنيو", callback_data="show_menu")],

        [InlineKeyboardButton(text="🛒 سلتي", callback_data="show_cart")],

        [InlineKeyboardButton(text="📦 طلباتي", callback_data="my_orders")]

    ])

    await msg.answer("🎉 مرحبا في خدمة التوصيل!\nاختر من القائمة:", reply_markup=keyboard)

# باقي المنيو والدفع راح أكمله بعد ما تعطيني التفاصيل

async def main():

    logging.basicConfig(level=logging.INFO)

    await dp.start_polling(bot)

if __name__ == "__main__":

    asyncio.run(main())
