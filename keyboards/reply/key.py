from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import requests as rq
from translator.translations import translate
from aiogram.utils.keyboard import ReplyKeyboardBuilder



def mainMenu(lang):
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=translate('Заказать', lang))
            ],
            [
                KeyboardButton(text=translate('🛍 Мои заказы', lang)),
                KeyboardButton(text=translate('📞 Контакты', lang))
            ],
            [
                KeyboardButton(text=translate('⚙️ Настройки', lang)),
            ],
        ],
        resize_keyboard=True,
    )

    return main_menu

def lang_key():
    langKey = ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(text='Русский язык 🇷🇺'),
                KeyboardButton(text="O'zbek tili 🇺🇿")
            ],
        ],
        resize_keyboard=True,
    )

    return langKey

def settings_lang(lang):
    settings_lang = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=translate('Изменить язык', lang)),
            ],
            [
                KeyboardButton(text=translate('⬅️  Назад', lang))
            ]
        ],
        resize_keyboard=True,
    )

    return settings_lang


def create_reply_keyboard(lang):
    reply_keyboard_builder = ReplyKeyboardBuilder()
    
    reply_keyboard_builder.add(KeyboardButton(text=translate('🛒 Корзина', lang)))
    reply_keyboard_builder.add(KeyboardButton(text=translate('⬅️ Назад', lang)))
    
    return reply_keyboard_builder.as_markup(resize_keyboard=True)


def keyLocation(lang):
    location = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=translate('📍 Моя геолокация', lang), request_location=True),
                KeyboardButton(text=translate('⬅️  Назад', lang))
            ],
        ],
        resize_keyboard=True,
    )

    return location

def keyNumber(lang):
    number = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=translate('Мой номер', lang), request_contact=True),
            ],
        ],
        resize_keyboard=True,
    )

    return number


def backfr(lang):
    number = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=translate('⬅️ Назад', lang)),
            ],
        ],
        resize_keyboard=True,
    )

    return number



async def Items(lang):
    all_items = await rq.get_items() 

    keyboard_rows = []

    keyboard_rows.append([KeyboardButton(text=translate("🛒 Корзина", lang))])

    item_buttons = [KeyboardButton(text=translate(f"{item.ItemName}", lang)) for item in all_items]
    while item_buttons:
        row = item_buttons[:2] 
        item_buttons = item_buttons[2:]
        keyboard_rows.append(row)

    # keyboard_rows.append([KeyboardButton(text=translate("Подписки", lang))])

    keyboard_rows.append([KeyboardButton(text=translate('⬅️  Назад', lang))])


    items_keyboard = ReplyKeyboardMarkup(keyboard=keyboard_rows, resize_keyboard=True)
    return items_keyboard