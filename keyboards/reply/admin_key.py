from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import requests as rq
from aiogram.utils.keyboard import ReplyKeyboardBuilder



def admin_main_key() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Добавить товар'),
            ],
            [
                KeyboardButton(text='Все товары'),
            ]
        ],
        resize_keyboard=True,
    )

async def adminItems():
    all_items = await rq.get_items() 
    items_keyboard = ReplyKeyboardBuilder()

    for item in all_items:
        items_keyboard.add(KeyboardButton(text=item.ItemName)) 

    
    return items_keyboard.adjust(2).as_markup(resize_keyboard=True)

