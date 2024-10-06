from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from handlers.users.admin_private import allItemNamesUz, allItemNamesRu
import keyboards.reply.key as kb
import database.requests as db
import keyboards.inline.buttons as il
from translator.translations import translate 
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
import aiohttp
import ssl
from decimal import Decimal
from datetime import datetime, timedelta
from settings import API_KEY_MAPS, ADMIN_CHAT_ID, CHAT_ID


router = Router()


async def get_address_from_lat_lng(latitude: float, longitude: float):
    url = f"https://geocode-maps.yandex.ru/1.x/?format=json&geocode={longitude},{latitude}&lang=ru&apikey={API_KEY_MAPS}"
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=ssl_context) as response:
            if response.status == 200:
                data = await response.json()
                try:
                    feature_member = data['response']['GeoObjectCollection']['featureMember'][0]
                    geo_object = feature_member['GeoObject']
                    meta_data = geo_object['metaDataProperty']['GeocoderMetaData']
                    address = meta_data['text']
                    country_code = meta_data['Address']['country_code']
                    return address, country_code
                except (KeyError, IndexError):
                    return "", ""
            return "", ""
        

class ReviewState(StatesGroup):
    waiting_for_review = State()

class PromoState(StatesGroup):
    waiting_for_promo = State()

class Form(StatesGroup):
    waiting_for_name = State() 

@router.message(CommandStart())
async def getStart(message: Message):
 

    user_id = message.from_user.id

    if message.chat.type != 'private':
        return

    if not await db.user_exists(user_id):
        await message.answer("🇷🇺 Выберите язык:\n🇺🇿 Tilni tanlang:", reply_markup=il.lang_inline())
    else:
        lang = await db.get_lang(user_id)
        await message.answer(translate("Выберите одно из следующих:", lang), reply_markup=kb.mainMenu(lang=lang))

@router.message(F.text.in_(['Русский язык 🇷🇺', "O'zbek tili 🇺🇿"]))
async def set_language(message: Message):
    """Handle setting language."""
    lang = 'ru' if message.text == 'Русский язык 🇷🇺' else 'uz'
    await db.update_lang(message.from_user.id, lang)
    await message.answer(translate("✅ Готово", lang), reply_markup=kb.mainMenu(lang=lang))


@router.callback_query(F.data.in_({"ru", "uz"}))
async def setLang(callback: CallbackQuery):
    await callback.message.delete()
    tgID = callback.from_user.id
    lang = callback.data
    await callback.answer()

    if not await db.user_exists(tgID):
        if lang == "ru":
            welcome_message = f"Здраствуйте <b>{callback.from_user.first_name}</b>, я ваш личный помощник по вопросам заказа продуктов Sparkle Stepp.\n\nВыберите одно из следующих:"
        else:
            welcome_message = f"Salom <b>{callback.from_user.first_name}</b>, men Sparkle Stepp mahsulotlariga buyurtma berish bo'yicha sizning shaxsiy yordamchingizman.\n\nQuyidagilardan birini tanlang:"

        await db.add_user(tgID, lang)

        await callback.message.answer(welcome_message, reply_markup=kb.mainMenu(lang=lang))



@router.callback_query(F.data == "promo")
async def ask_for_promo(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    tgID = callback.from_user.id
    lang = await db.get_lang(tgID)
    await callback.message.answer(translate("Пожалуйста, пришлите ваш промокод.", lang), reply_markup=kb.backfr(lang))
    await callback.answer()
    await state.set_state(PromoState.waiting_for_promo)

@router.message(PromoState.waiting_for_promo, F.text)
async def receive_promo_code(message: Message, state: FSMContext):
    user_message = message.text
    user_id = message.from_user.id
    lang = await db.get_lang(user_id)
    payment_methods = await db.get_user_payment_method(user_id)
    all_promo_codes = await db.get_all_promo_codes()

    if user_message == "⬅️ Назад":
        await message.answer(translate('Выберите продукт, который хотите купить.', lang), reply_markup=await kb.Items(lang=lang))
        await state.clear()
        return

    for promo in all_promo_codes:
        if user_message == promo.promoText:

            if promo.activations == 0:
                await message.answer(translate("Этот промокод больше не активен.", lang))
                return

            if lang == "ru":
                await message.answer(f"Ваш промокод применён: {int(promo.percentage)}% скидка.", reply_markup=ReplyKeyboardRemove())
            else:
                await message.answer(f"Sizning promo-kod qo‘llanildi: {int(promo.percentage)}% chegirma.", reply_markup=ReplyKeyboardRemove())

            await db.update_user_promo(user_id, user_message)
            total_cart_price = Decimal(0)
            response = []
            order_sums = await db.get_order_quantity_sum(user_id)
            latitude = await db.get_user_lat(user_id)
            longitude = await db.get_user_long(user_id)
            userAdress, country_code = await get_address_from_lat_lng(latitude, longitude)

            for order in order_sums:
                item = await db.get_items_by_id(order[0])
                total_quantity = order[1]
                total_price = Decimal(item.ItemPrice) * Decimal(total_quantity)
                total_cart_price += total_price

                # Accumulate all orders' information
                if lang == 'ru':
                    response.append(f"{total_quantity} ✖️ {item.ItemName}")
                else:
                    response.append(f"{total_quantity} ✖️ {item.ItemNameUz}")

            final_price = total_cart_price * (1 - (Decimal(promo.percentage) / Decimal(100)))

            # Construct the full message with all items
            if lang == 'ru':
                full_message = (
                    f"💼 <b>Ваш заказ:</b>\n\n"
                    f"🏠 <b>Адрес:</b> <code>{userAdress}</code>\n\n"
                    f"{'\n'.join(response)}\n\n"
                    f"💳 <b>Тип оплаты:</b> <code>{payment_methods}</code>\n\n"
                    f"💰 <b>Итого:</b> <s>{total_cart_price:,.0f}</s> <b>{final_price:,.0f} сум</b>\n\n"
                    f"🏷 <b>Промокод:</b> <code>{user_message}</code>\n\n"
                )
            else:
                full_message = (
                    f"💼 <b>Sizning buyurtmangiz:</b>\n\n"
                    f"🏠 <b>Manzil:</b> <code>{userAdress}</code>\n\n"
                    f"{'\n'.join(response)}\n\n"
                    f"💳 <b>To'lov turi:</b> <code>{payment_methods}</code>\n\n"
                    f"💰 <b>Jami:</b> <s>{total_cart_price:,.0f}</s> <b>{final_price:,.0f} so'm</b>\n\n"
                    f"🏷 <b>Promokod:</b> <code>{user_message}</code>\n\n"
                )

            await message.answer(full_message, reply_markup=await il.finish_or_not(lang))

            break

    else:
        await message.answer(translate("Неверный промокод, попробуйте еще раз.", lang))

    await state.clear()



@router.callback_query(F.data.in_({"yes", "no"}))
async def handle_yes_no(callback: CallbackQuery):
    await callback.message.delete()
    tgID = callback.from_user.id
    lang = await db.get_lang(tgID)
    
    if callback.data == "yes":

        await callback.message.answer(translate("Выберите одно из следующих:", lang), reply_markup=ReplyKeyboardRemove())
        await callback.message.answer(translate("Отправьте номер своего телефона:", lang), reply_markup=kb.keyNumber(lang=lang))
    else:
        await callback.message.answer(translate("📍 Отправьте место, куда нужно доставить товар!", lang), reply_markup=kb.keyLocation(lang=lang))
    
    await callback.answer()


@router.callback_query(F.data == "confirm")
async def confirm_order(callback: CallbackQuery):
    await callback.message.delete()
    user_id = callback.from_user.id
    lang = await db.get_lang(user_id)
    payment_method = await db.get_user_payment_method(user_id)
    cart_items = await db.get_cart_items(user_id)
    user_promo = await db.get_user_promo(user_id)
    all_promo_codes = await db.get_all_promo_codes()

    valid_promo = None
    if user_promo:
        for promo in all_promo_codes:
            if user_promo == promo.promoText:
                valid_promo = promo
                break 

    if not cart_items:
        await callback.message.answer(translate("Ваша корзина пуста. Нельзя подтвердить заказ.", lang))
        return

    latitude = await db.get_user_lat(user_id)
    longitude = await db.get_user_long(user_id)
    user_address, country_code = await get_address_from_lat_lng(latitude, longitude)
    user_phone_number = await db.get_user_number(user_id)

    total_cart_price = 0
    order_details = {}

    for cart_item in cart_items:
        item_id = cart_item.itemId
        quantity = cart_item.orderQuantity
        item_details = await db.get_items_by_id(item_id)

        total_price = item_details.ItemPrice * quantity

        if valid_promo:
            discount_percentage = Decimal(valid_promo.percentage) / Decimal(100)
            discount_amount = total_price * discount_percentage
            total_price -= discount_amount

            if valid_promo.activations > 0:
                valid_promo.activations -= 1
                await db.update_promo_activations(valid_promo.id, valid_promo.activations)

        total_cart_price += total_price

        current_time = datetime.utcnow()
        gmt_plus_5_time = current_time + timedelta(hours=5) 
        formatted_time = gmt_plus_5_time.strftime('%y/%m/%d %H:%M')

        if item_id in order_details:
            order_details[item_id]['quantity'] += quantity
            order_details[item_id]['total_price'] += total_price
        else:
            order_details[item_id] = {
                'name': item_details.ItemName,
                'quantity': quantity,
                'total_price': total_price,
            }

        new_item_quantity = max(0, item_details.ItemQuantity - quantity)
        await db.update_item_quantity(item_id, new_item_quantity)

        await db.add_order_to_db(
            userId=user_id,
            userNumber=user_phone_number,
            itemId=item_details.Id,
            itemName=item_details.ItemName,
            itemNameUz=item_details.ItemNameUz,
            orderTotalSum=total_price,  
            orderQuantity=quantity,
            userPaymentMethod=payment_method,
            userPromoCode=user_promo,
            orderStatus=True, 
            created=gmt_plus_5_time
        )

    await db.delete_from_cart(user_id)

    await callback.message.answer(translate("Ваш заказ принят, чтобы получить больше информации о нем свяжитесь с <a href='https://t.me/SparkleSteppmanager'>Aдмином</a>", lang), reply_markup=kb.mainMenu(lang=lang))

    order_ids = await db.get_order_ids_by_user_id(user_id)
    formatted_order_ids = ' '.join([f"#{order_id}" for order_id in order_ids])
    await db.update_user_promo(user_id, new_promo=None)
    username = await db.get_user_name(user_id)

    order_detail_lines = '\n'.join(
        f"{details['quantity']} шт: {details['name']} = {details['total_price']:,.0f} сум"
        for details in order_details.values()
    )

    admin_message = (
        f"🆕 <b>Новый заказ</b>\n\n"
        f"📋 <b>ID заказа:</b> <code>{formatted_order_ids}</code>\n"
        f"📅 <b>Дата заказа:</b> <code>{formatted_time}</code>\n\n"
        f"👤 <b>Пользователь:</b>\n\n"
        f"  🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"  🔹 <b>Имя:</b> <code>{username}</code>\n"
        f"  📞 <b>Номер:</b> +{user_phone_number}\n\n"
        f"🏠 <b>Адрес:</b>\n\n"
        f"<code>{user_address}</code>\n\n"
        f"🌐 <b>Координаты:</b>\n\n"
        f"  📍 <b>Широта:</b> <code>{latitude}</code>\n"
        f"  📍 <b>Долгота:</b> <code>{longitude}</code>\n\n"
        f"🛒 <b>Подробности заказа:</b>\n\n"
        f"<code>{order_detail_lines}</code>\n\n"
        f"💳 <b>Тип оплаты:</b> <code>{payment_method}</code>\n\n"
        f"🏷 <b>Промокод:</b> <code>{user_promo}</code>\n\n"
        f"💵 <b>Итоговая сумма:</b> <code>{total_cart_price:,.0f} сум</code>"
    )

    await callback.message.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)
    await callback.answer()


@router.callback_query(F.data == "noconfirm")
async def noconfirm_order(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()
    user_id = callback.from_user.id
    lang = await db.get_lang(user_id)

    await db.delete_from_cart(user_id)
    await db.update_user_promo(user_id, new_promo=None)
    await callback.message.answer("Заказ отменено!\nВыберите одно из следующих:", reply_markup=await kb.Items(lang=lang))
    await callback.answer()

@router.callback_query(F.data == "review")
async def prompt_review(callback: CallbackQuery, state: FSMContext):
    tgID = callback.from_user.id
    lang = await db.get_lang(tgID)

    await callback.message.answer(
        translate("Пожалуйста, отправьте свой отзыв о продукте!", lang), 
        reply_markup=ReplyKeyboardRemove()
    )
    
    await state.set_state(ReviewState.waiting_for_review)
    await state.update_data(user_id=tgID)
    await callback.answer()


@router.callback_query(F.data == "checkout")
async def checkout(callback_query: CallbackQuery, state: FSMContext):

    await callback_query.message.delete()
    user_id = callback_query.from_user.id
    lang = await db.get_lang(user_id)
    await callback_query.message.answer(translate("Пожалуйста отправьте ваше имя!", lang), reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.waiting_for_name)
    await callback_query.answer()

@router.message(Form.waiting_for_name) 
async def process_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.text 
    lang = await db.get_lang(user_id)
    await db.save_user_to_db(user_id,name)
    await message.answer(translate("📍 Отправьте место, куда нужно доставить товар:", lang), reply_markup=kb.keyLocation(lang=lang))
    await state.clear()



@router.message(ReviewState.waiting_for_review)
async def receive_review(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    lang = await db.get_lang(user_id)
    userName = await db.get_user_name(user_id)

    user_review = message.text
    
    if message.from_user.username:
        user_identifier = f"@{message.from_user.username}"  
    else:
        user_identifier = userName 

    if user_review:
        await message.bot.send_message(chat_id=CHAT_ID, text=f"Отзыв от пользователя {user_identifier}: <b>{user_review}</b>")

        await message.answer(translate("Спасибо за отзыв!", lang), reply_markup=kb.mainMenu(lang))
    else:
        await message.answer(translate("Вы не отправили отзыв.", lang))

    await state.clear()


@router.message(F.location)
async def getLocation(message: Message):
    tgID = message.from_user.id
    lang = await db.get_lang(tgID)
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    address, country_code = await get_address_from_lat_lng(latitude, longitude)

    if not address:
        await message.answer(translate("Не удалось получить адрес!", lang))
        return

    if country_code != 'UZ':
        await message.answer(translate("Доставка по вашему адресу невозможна!", lang))
        return

    if lang == "ru":
        await message.answer(f"Ваш адрес: {address}\n\nВы подтверждаете этот адрес?", reply_markup=await il.isLocationTrue(lang))
    else:
        await message.answer(f"Sizning manzilingiz: {address}\n\nBu manzilni tasdiqlaysizmi?", reply_markup=await il.isLocationTrue(lang))

    user_location = await db.get_user_location(tgID)

    if user_location:
        try:
            await db.update_user_location(tgID=tgID, latitude=latitude, longitude=longitude)
        except Exception as e:
            await message.answer(translate('Ошибка при обновлении местоположения!', lang))
    else:
        try:
            await db.save_location(tgID=tgID, lang=lang, latitude=latitude, longitude=longitude)
        except Exception as e:
            await message.answer(translate('Ошибка при сохранении местоположения!', lang))

@router.message(F.contact)
async def check_number(message: Message):
    userNumber = message.contact.phone_number
    tgID = message.from_user.id
    lang = await db.get_lang(message.from_user.id)
    # if userNumber.startswith("998") and len(userNumber) == 12 and userNumber[3:].isdigit():
    await db.save_number(tgID=tgID, userNumber=userNumber)
    await message.answer(translate("Выберите одно из следующих:", lang), reply_markup=ReplyKeyboardRemove())
    await message.answer(translate("Выберите тип оплаты:", lang), reply_markup=await il.cardOrCash(lang))
    # else:
    #     await message.answer(translate('Неправильный формат вашего номера телефона', lang))
    #     return


@router.message()
async def orderBtn(message: Message, state: FSMContext):

    counter = 1
    await state.update_data(counter=counter)
    
    id_user = message.from_user.id
    lang = await db.get_lang(id_user)

    if message.text == translate('⚙️ Настройки', lang):
        await message.answer(translate('Выберите действие:', lang), reply_markup=kb.settings_lang(lang))

    elif message.text == translate('Изменить язык', lang):
        await message.answer(translate('Выберите язык:', lang), reply_markup=kb.lang_key())

    elif message.text == translate('Заказать', lang):
        await message.answer(translate('Выберите продукт, который хотите купить.', lang), reply_markup=await kb.Items(lang=lang))

    elif message.text == translate('⬅️  Назад', lang):
        await message.answer(translate("Выберите одно из следующих:", lang), reply_markup=kb.mainMenu(lang=lang))

    elif message.text == translate('📞 Контакты', lang):
        keyboardAdmin = await il.admin_contact()
        await message.answer(translate("Для получения информации по заказу и другим вопросам напишите в <a href='https://t.me/SparkleSteppmanager'>Aдмин</a>, ответим на все вопросы", lang), reply_markup=keyboardAdmin)

    elif message.text == translate('🛍 Мои заказы', lang):

        active_orders = await db.get_user_active_orders(id_user)

        if not active_orders:
            await message.answer(translate("У вас нет активных заказов!", lang))
            return

        orders_by_date = {}
        for order in active_orders:
            created_date = order.created.strftime("%Y-%m-%d %H:%M")
            item_id = order.itemId

            # Choose item name based on language
            item_name = order.itemName if lang == "ru" else order.itemNameUz  # Assuming you have itemNameUz for Uzbek

            if created_date not in orders_by_date:
                orders_by_date[created_date] = {
                    "userNumber": order.userNumber,
                    "items": {},
                    "totalSum": 0.0,
                    "paymentMethod": order.userPaymentMethod,
                    "orderStatus": order.orderStatus,
                }

            if item_id in orders_by_date[created_date]["items"]:
                orders_by_date[created_date]["items"][item_id]["quantity"] += order.orderQuantity
            else:
                orders_by_date[created_date]["items"][item_id] = {
                    "name": item_name,
                    "quantity": order.orderQuantity,
                }

            orders_by_date[created_date]["totalSum"] += order.orderTotalSum

        for created_date, order_data in orders_by_date.items():
            item_lines = "\n".join(
                f"• <b>{item['name']}</b>: <code>{item['quantity']} {'шт.' if lang == 'ru' else 'dona.'}</code>"
                for item in order_data["items"].values()
            )

            if lang == "ru":
                order_info = (
                    f"📦 <b>Информация о заказе</b>\n\n"
                    f"• <b>Дата заказа:</b> <code>{created_date}</code>\n\n"
                    f"• <b>Телефон:</b> <code>+{order_data['userNumber']}</code>\n\n"
                    f"{item_lines}\n\n"
                    f"💰 <b>Общая сумма:</b> <code>{order_data['totalSum']:,.0f} сум</code>\n\n"
                    f"💳 <b>Метод оплаты:</b> <code>{order_data['paymentMethod']}</code>\n\n"
                    f"📋 <b>Статус заказа:</b> <b>{'✅ В процессе' if order_data['orderStatus'] else '❌ Неактивен'}</b>\n\n"
                )
            else:
                order_info = (
                    f"📦 <b>Buyurtma haqida ma'lumot</b>\n\n"
                    f"📅 <b>Buyurtma sanasi:</b> <code>{created_date}</code>\n\n"
                    f"📞 <b>Telefon:</b> <code>+{order_data['userNumber']}</code>\n\n"
                    f"{item_lines}\n\n"
                    f"💰 <b>Umumiy summa:</b> <code>{order_data['totalSum']:,.0f} so'm</code>\n\n"
                    f"💳 <b>To'lov usuli:</b> <code>{order_data['paymentMethod']}</code>\n\n"
                    f"📋 <b>Buyurtma holati:</b> <b>{'✅ Jarayonda' if order_data['orderStatus'] else '❌ Aktiv emas'}</b>\n\n"
                )

            await message.answer(order_info)


    
    all_item_names = await allItemNamesRu() if lang == 'ru' else await allItemNamesUz()
    
    if message.text in all_item_names:
        item_details = await (db.getItemDetailsByName if lang == 'ru' else db.getItemDetailsByNameUz)(message.text)
        
        if item_details:
            formatted_price = f"{item_details.ItemPrice:,.0f} {translate('сум', lang)}"
            response = (
                            f"🛍️ <b>{'Названия:' if lang == 'ru' else 'Mahsulot:'}</b> "
                            f"{translate(item_details.ItemName if lang == 'ru' else item_details.ItemNameUz, lang=lang)}\n\n"
                            f"📝 <b>{'Описание:' if lang == 'ru' else 'Tavsif:'}</b> "
                            f"{translate(item_details.ItemDescription if lang == 'ru' else item_details.ItemDescriptionUz, lang=lang)}\n\n"
                            f"💰 <b>{'Цена:' if lang == 'ru' else 'Narxi:'}</b> {formatted_price}\n"
                        )
            keyboardInline = await il.create_keyboard(lang, counter, item_details.Id)

            response_msg2 = await message.answer("Выберите одно из следующих:", reply_markup=kb.create_reply_keyboard(lang))
            response_msg = await message.answer_photo(photo=item_details.ItemImg, caption=response, reply_markup=keyboardInline)
            await state.update_data(last_photo_message_id=response_msg.message_id, last_answer_message_id=response_msg2.message_id)

    elif message.text == translate('⬅️ Назад', lang):
        data = await state.get_data()
        keyboard = await kb.Items(lang=lang)
        last_photo_message_id = data.get('last_photo_message_id')
        last_answer_message_id = data.get('last_answer_message_id')

        if last_photo_message_id:
            await message.chat.delete_message(last_photo_message_id)
        if last_answer_message_id:
            await message.chat.delete_message(last_answer_message_id)
        await message.answer(translate('Выберите продукт, который хотите купить.', lang), reply_markup=keyboard)

    elif message.text == translate('🛒 Корзина', lang):
        await handle_cart(message, lang, state)


async def handle_cart(message: Message, lang: str, state: FSMContext):
    user_id = message.from_user.id
    cart_items = await db.get_cart_items(user_id)
    order_sums = await db.get_order_quantity_sum(user_id)

    if not cart_items:
        keyboard = await kb.Items(lang=lang)
        await message.answer(translate("Ваша корзина пуста.\n\nВыберите одно из следующих:", lang), reply_markup=keyboard)
        return

    response = []
    total_cart_price = 0
    item_unavailable = False

    for order in order_sums:
        item = await db.get_items_by_id(order[0])
        total_quantity = order[1]
        total_price = item.ItemPrice * total_quantity
        total_cart_price += total_price

        if item.ItemQuantity < total_quantity:
            item_unavailable = True
            keyboard1 = await kb.Items(lang=lang)
            await message.answer(translate("В настоящее время у нас нет необходимого вам количества товара, и мы удалили все товары из вашей корзины.", lang), reply_markup=keyboard1)
            await db.delete_from_cart(user_id)
            return

        response.append(f"{total_quantity} ✖️ {item.ItemName if lang == 'ru' else item.ItemNameUz}")

    if not item_unavailable:
        full_message = (
                        f"🛒 <b>{'В корзине:' if lang == 'ru' else 'Savatda:'}</b>\n\n"
                        f"{'\n'.join([f'<b>{item}</b>' for item in response])}\n\n"
                        f"💰 <b>{'Итого: ' if lang == 'ru' else 'Jami: '}</b><b>{total_cart_price:,.0f} {'сум' if lang == 'ru' else 'so\'m'}</b>"
                    )
        cart_message = await message.answer(full_message, reply_markup=await il.delete_cart_items(lang, user_id))
        await state.update_data(cart_message_id=cart_message.message_id)


@router.callback_query(F.data.startswith("increment_"))
async def increment_counter(callback_query: CallbackQuery, state: FSMContext):
    
    try:
        data_parts = callback_query.data.split('_')
        if len(data_parts) != 2 or not data_parts[1].isdigit():
            raise ValueError("Неверный формат данных для действия приращения")
        product_id = int(data_parts[1])
    except (ValueError, IndexError) as e:
        await callback_query.answer("Неверный формат действия.")
        return
    
    lang = await db.get_lang(callback_query.from_user.id)
    data = await state.get_data()
    counter = data.get("counter", 1)
    counter += 1
    await state.update_data(counter=counter)
    
    keyboard = await il.create_keyboard(lang, counter, product_id)
    
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer(f'{counter}')

@router.callback_query(F.data.startswith("decrement_"))
async def decrement_counter(callback_query: CallbackQuery, state: FSMContext):
    
    try:
        data_parts = callback_query.data.split('_')
        if len(data_parts) != 2 or not data_parts[1].isdigit():
            raise ValueError("Неверный формат данных для действия уменьшения")
        product_id = int(data_parts[1])
    except (ValueError, IndexError) as e:
        await callback_query.answer("Неверный формат действия.")
        return
    
    lang = await db.get_lang(callback_query.from_user.id)
    data = await state.get_data()
    counter = data.get("counter", 1)
    counter -= 1 if counter > 1 else 0
    await state.update_data(counter=counter)
    
    keyboard = await il.create_keyboard(lang, counter, product_id)
    
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    await callback_query.answer(f'{counter}')



@router.callback_query(F.data.startswith("add_to_cart_"))
async def basket_action(callback_query: CallbackQuery, state: FSMContext):
    try:
        data_parts = callback_query.data.split('_')
        product_id = int(data_parts[-1])
    except (ValueError, IndexError):
        await callback_query.answer("Неверный формат действия.")
        return
    
    lang = await db.get_lang(callback_query.from_user.id)
    
    data = await state.get_data()
    item_name = await db.get_item(product_id)
    counter = data.get("counter", 1)
    user = callback_query.from_user

    await db.orm_add_to_cart(user_id=user.id, product_id=product_id, item_name=item_name.ItemName, quantity=counter)

    last_photo_message_id = data.get('last_photo_message_id')
    last_answer_message_id = data.get('last_answer_message_id')

    await callback_query.message.chat.delete_message(last_photo_message_id)
    await callback_query.message.chat.delete_message(last_answer_message_id)

    
    await callback_query.answer(translate("Товар добавлен в корзину", lang))
    keyboard = await kb.Items(lang=lang)
    await callback_query.message.answer(translate('✔️ Товар добавлен в корзину:', lang), reply_markup=keyboard)
    await callback_query.message.answer(translate('Выберите одно из следующих:', lang), reply_markup=keyboard)
    await callback_query.answer()


@router.callback_query(F.data.startswith('delete_cart_'))
async def process_delete_cart_item(callback_query: CallbackQuery, state: FSMContext):
    item_id = int(callback_query.data.split('_')[2])
    user_id = callback_query.from_user.id
    lang = await db.get_lang(user_id)

    await db.delete_item_from_cart(user_id, item_id)
    order_sums = await db.get_order_quantity_sum(user_id)

    if not order_sums:
        full_message = translate("Ваша корзина пусто.", lang)
        reply_markup = None
    else:
        response = []
        total_cart_price = 0
        item_unavailable = False

        for order in order_sums:
            item = await db.get_items_by_id(order[0])
            total_quantity = order[1]
            total_price = item.ItemPrice * total_quantity
            total_cart_price += total_price

            if item.ItemQuantity < total_quantity:
                item_unavailable = True
                await db.delete_from_cart(user_id)
                break

            response.append(f"{total_quantity} ✖️ {item.ItemNameUz if lang == 'uz' else item.ItemName} = {total_price:,.0f} {'soʻm' if lang == 'uz' else 'сум'}")

        full_message = translate(
                                    "💼 <b>Ваша корзина пусто.</b>" if not order_sums else (
                                        "⚠️ <b>В настоящее время у нас нет необходимого вам количества товара, и мы удалили все товары из вашей корзины.</b>"
                                        if item_unavailable 
                                        else (
                                            f"🛒 <b>В корзине:</b>\n{'\n'.join([f'<b>{item}</b>' for item in response])}\n"
                                            f"💰 <b>Итого:</b> <b>{total_cart_price:,.0f} сум</b>"
                                        )
                                    ), lang
                                )
        reply_markup = await il.delete_cart_items(lang, user_id) if not item_unavailable else None

    cart_message_id = (await state.get_data()).get('cart_message_id')

    if cart_message_id:
        try:
            await callback_query.bot.edit_message_text(
                chat_id=callback_query.message.chat.id,
                message_id=cart_message_id,
                text=full_message,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Error editing message: {e}")
            await callback_query.message.answer(full_message, reply_markup=reply_markup)
    else:
        await callback_query.message.answer(full_message, reply_markup=reply_markup)


    await callback_query.answer()

@router.callback_query(F.data == "back")
async def back(callback_query: CallbackQuery, state: FSMContext):

    user_id = callback_query.from_user.id
    lang = await db.get_lang(user_id)

    cart_message_id = (await state.get_data()).get('cart_message_id')

    await callback_query.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=cart_message_id)

    await callback_query.answer()

    await callback_query.message.answer(translate("Выберите одно из следующих:", lang))


@router.callback_query(F.data == "emptybasket")
async def empty_cart(callback_query: CallbackQuery, state: FSMContext):

    user_id = callback_query.from_user.id
    await db.delete_from_cart(user_id)
    lang = await db.get_lang(user_id)
    cart_message_id = (await state.get_data()).get('cart_message_id')
    await callback_query.bot.delete_message(chat_id=callback_query.message.chat.id, message_id=cart_message_id)
    await callback_query.answer()
    await callback_query.message.answer(translate("Ваша корзина пуста.\n\nВыберите одно из следующих:", lang))




@router.callback_query(F.data.in_({"card", "cash"}))
async def payment_method(callback_query: CallbackQuery):
    await callback_query.message.delete()
    user_id = callback_query.from_user.id
    
    payment_method = "Карта" if callback_query.data == "card" else "Наличные"

    await db.update_payment_method(user_id, new_method=payment_method)

    total_cart_price = 0
    response = []
    lang = await db.get_lang(user_id)
    order_sums = await db.get_order_quantity_sum(user_id)
    latitude = await db.get_user_lat(user_id)
    longitude = await db.get_user_long(user_id)
    userAdress, country_code = await get_address_from_lat_lng(latitude, longitude)

    for order in order_sums:
        item = await db.get_items_by_id(order[0])
        total_quantity = order[1]
        total_price = item.ItemPrice * total_quantity
        total_cart_price += total_price

        if lang == 'ru':
            response.append(f"{total_quantity} ✖️ {item.ItemName}")
        else:
            response.append(f"{total_quantity} ✖️ {item.ItemNameUz}")

    if lang == 'ru':
        full_message = (
        f"📦 <b>Ваш заказ:</b>\n\n"
        f"🏠 <b>Адрес:</b> <code>{userAdress}</code>\n\n"
        f"{'\n'.join(response)}\n\n"
        f"💳 <b>Тип оплаты:</b> <code>{payment_method}</code>\n\n"
        f"💵 <b>Итого:</b> <code>{total_cart_price:,.0f} сум</code>\n\n"
    )
    else:
        full_message = (
    f"📦 <b>Sizning buyurtmangiz:</b>\n\n"
    f"🏠 <b>Manzil:</b> <code>{userAdress}</code>\n\n"
    f"{'\n'.join(response)}\n\n"
    f"💳 <b>To'lov turi:</b> <code>{translate(payment_method, lang)}</code>\n\n"
    f"💵 <b>Jami:</b> <code>{total_cart_price:,.0f} so'm</code>\n\n"
)

    await callback_query.message.answer(full_message, reply_markup=await il.promo_finish_or_not(lang))
    await callback_query.answer()
