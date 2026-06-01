from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from translator.translations import translate 
from aiogram.types import InlineKeyboardButton
import database.requests as db
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup






def lang_inline():
    chooseLang = InlineKeyboardBuilder()
    chooseLang.button(text='Русский язык 🇷🇺', callback_data='ru')
    chooseLang.button(text="O'zbek tili 🇺🇿", callback_data='uz')

    chooseLang.adjust(2)
    return chooseLang.as_markup()

async def admin_contact():
    chooseLang = InlineKeyboardBuilder()
    chooseLang.button(text='Admin/Админ', url="https://t.me/SparkleSteppmanager")

    return chooseLang.as_markup()



async def create_keyboard(lang, counter: int, product_id: int):
    inline_keyboard_builder = InlineKeyboardBuilder()
    
    inline_keyboard_builder.button(text="-", callback_data=f"decrement_{product_id}")
    inline_keyboard_builder.button(text=f"{counter}", callback_data="counter")
    inline_keyboard_builder.button(text="+", callback_data=f"increment_{product_id}")
    
    add_to_cart_text = translate("📥 Добавить в корзину", lang)
    inline_keyboard_builder.button(text=add_to_cart_text, callback_data=f"add_to_cart_{product_id}")
    
    return inline_keyboard_builder.adjust(3, 1).as_markup()

async def delete_cart_items(lang, user_id):

    all_items = await db.get_cart_items(user_id)
    

    item_quantities = {}
    for item in all_items:
        if item.itemId in item_quantities:
            item_quantities[item.itemId]['quantity'] += 1
        else:
            item_quantities[item.itemId] = {
                'name': item.itemName,
                'quantity': 1
            }

    items_keyboard = InlineKeyboardBuilder()

    items_keyboard.row(
        InlineKeyboardButton(text=translate("⬅️ Назад", lang), callback_data="back"),
        InlineKeyboardButton(text=translate("🚖 Оформить заказ", lang), callback_data="checkout")
    )

    items_keyboard.row(
        InlineKeyboardButton(text=translate("🗑 Очистить корзину", lang), callback_data="emptybasket")
    )

    for item_id, data in item_quantities.items():
        item_name_translated = translate(data['name'], lang)
        button_text = f"❌ {item_name_translated}"
        items_keyboard.row(
            InlineKeyboardButton(text=button_text, callback_data=f"delete_cart_{item_id}")
        )

    return items_keyboard.as_markup()



async def isLocationTrue(lang: str) -> InlineKeyboardMarkup:

    yes_button = InlineKeyboardButton(text=translate("✅ Да", lang), callback_data="yes")
    no_button = InlineKeyboardButton(text=translate("❌ Нет", lang), callback_data="no")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [yes_button],
        [no_button]
    ])
    
    return keyboard

async def finish_or_not(lang: str) -> InlineKeyboardMarkup:

    yes_button = InlineKeyboardButton(text=translate("✅ Подтвердить", lang), callback_data="confirm")
    no_button = InlineKeyboardButton(text=translate("❌ Отмена", lang), callback_data="noconfirm")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [yes_button],
        [no_button]
    ])
    
    return keyboard




async def cardOrCash(lang: str) -> InlineKeyboardMarkup:

    yes_button = InlineKeyboardButton(text=translate("💳 Карта", lang), callback_data="card")
    no_button = InlineKeyboardButton(text=translate("💵 Наличный", lang), callback_data="cash")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [yes_button],
        [no_button]
    ])
    
    return keyboard

async def promo_finish_or_not(lang: str) -> InlineKeyboardMarkup:

    ok_button = InlineKeyboardButton(text=translate("✉️ У меня есть промокод", lang), callback_data="promo")
    yes_button = InlineKeyboardButton(text=translate("✅ Подтвердить", lang), callback_data="confirm")
    no_button = InlineKeyboardButton(text=translate("❌ Отмена", lang), callback_data="noconfirm")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [ok_button],
        [yes_button],
        [no_button],
    ])
    
    return keyboard

async def review(lang: str) -> InlineKeyboardMarkup:

    yes_button = InlineKeyboardButton(text=translate('✍️ Оставить отзыв', lang), callback_data="review")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [yes_button],
    ])
    
    return keyboard


async def get_callback_btns(
    btns: dict[str, str],
    sizes: tuple[int] = (2,)):

    keyboard = InlineKeyboardBuilder()

    for text, data in btns.items():
        
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()
