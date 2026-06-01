from aiogram import Router, F, types
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, or_f
import keyboards.reply.admin_key as ke
from settings import ADMINS, ADMIN_CHAT_ID
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import database.admin_requests as da
from database import requests as rq
import keyboards.inline.buttons as il
from translator.translations import translate, item_translations


routerAD = Router()
routerAD.message.filter()

class AddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    quantity = State()
    image = State()
    name_uz = State()
    description_uz = State()
    product_for_change = None

class PromoCodeStates(StatesGroup):
    waiting_for_promotext = State()
    waiting_for_activations = State()
    waiting_for_percentage = State()
    waiting_for_promo_id = State()

class DoneOrderStates(StatesGroup):
    waiting_for_order_ids = State()

class CancelOrderStates(StatesGroup):
    waiting_for_order_ids = State()


async def is_admin(message: Message):
    return str(message.from_user.id) in ADMINS

async def allItemNamesRu():
    all_items = await rq.get_items()
    return [item.ItemName for item in all_items]

async def allItemNamesUz():
    all_itemsUz = await rq.get_items()
    return [itemUz.ItemNameUz for itemUz in all_itemsUz]

@routerAD.message(Command('cancel'), is_admin)
async def cancelAddItem(message: Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer("Отменено добавление товар", reply_markup=ke.admin_main_key())
    except Exception as e:
        await message.answer("Не отменено\n\nnОбратись к программеру", reply_markup=ke.admin_main_key())


@routerAD.message(Command('done'), is_admin)
async def start_done_command(message: types.Message, state: FSMContext):

    await message.answer("Пожалуйста, укажите ID заказов, которые хотите завершить, через пробел.")
    await state.set_state(DoneOrderStates.waiting_for_order_ids)


@routerAD.message(DoneOrderStates.waiting_for_order_ids)
async def process_order_ids(message: types.Message, state: FSMContext):

    user_message = message.text

    try:
        order_ids = [int(order_id) for order_id in user_message.split()]

        user_orders = await da.get_user_id_by_order_id(order_ids)

        if not user_orders:
            await message.answer("Некорректные ID заказов. Пожалуйста, проверьте.")
            await state.clear()
            return

        for user_id, user_order_ids in user_orders.items():
            completed_orders = await da.get_completed_orders(user_order_ids)

            if completed_orders:
                await message.answer(f"Заказы с ID {', '.join(map(str, completed_orders))} уже завершены.")
                user_order_ids = [oid for oid in user_order_ids if oid not in completed_orders]

            if not user_order_ids:
                continue

            success, invalid_orders = await da.update_order_status_by_ids(user_order_ids)

            if success:
                lang = await rq.get_lang(user_id)
                await message.bot.send_message(
                    chat_id=user_id,
                    text=translate("Ваш заказ успешно доставлен, пожалуйста оставьте свой отзыв о продукте!", lang),
                    reply_markup=await il.review(lang)
                )
                await message.answer(f"Заказы {', '.join(map(str, user_order_ids))} успешно завершены, сообщение отправлено пользователю.")
                await message.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Заказы {', '.join(map(str, user_order_ids))} успешно завершен(ы).")

            else:
                await message.answer(f"Некорректные ID заказов: {', '.join(map(str, invalid_orders))}. Пожалуйста, проверьте.")
        
    except ValueError:
        await message.answer("Пожалуйста, отправьте действительные номера заказов, разделенные пробелами.")
    
    await state.clear()


@routerAD.message(Command('delete_all_orders'), is_admin)
async def delete_all_orders_handler(message: Message):
    await da.delete_all_orders()
    await message.answer("Все ордеры удален")



@routerAD.message(Command('cancel_order'), is_admin)
async def start_cancel_command(message: types.Message, state: FSMContext):

    await message.answer("Пожалуйста, укажите ID заказов, которые хотите отменить, через пробел.")
    await state.set_state(CancelOrderStates.waiting_for_order_ids)


@routerAD.message(CancelOrderStates.waiting_for_order_ids)
async def process_cancel_order_ids(message: types.Message, state: FSMContext):

    user_message = message.text

    try:
        order_ids = [int(order_id) for order_id in user_message.split()]

        user_orders = await da.get_user_id_by_order_id(order_ids)

        if not user_orders:
            await message.answer("Некорректные ID заказов. Пожалуйста, проверьте.")
            await state.clear()
            return

        for user_id, user_order_ids in user_orders.items():
            success, invalid_orders = await da.OrderDeleted(user_order_ids)

            if success:
                await message.bot.send_message(
                    chat_id=user_id,
                    text="Ваши заказы были отменены администратором."
                )
                await message.answer(f"Заказы {', '.join(map(str, user_order_ids))} успешно отменены, сообщение отправлено пользователю.")
            else:
                await message.answer(f"Некорректные ID заказов: {', '.join(map(str, invalid_orders))}. Пожалуйста, проверьте.")
        
    except ValueError:
        await message.answer("Пожалуйста, отправьте действительные номера заказов, разделенные пробелами.")
    
    await state.clear()

@routerAD.message(Command("active_orders_id"), is_admin)
async def send_active_orders(message: Message):
    active_orders = await da.get_all_active_orders()
    
    if not active_orders:
        await message.answer("Нет активных заказов.")
        return

    # Grouping orders by userId
    orders_by_user = {}
    
    for order in active_orders:
        user_id = order.userId
        if user_id not in orders_by_user:
            orders_by_user[user_id] = []
        orders_by_user[user_id].append(order.orderId)
    
    orders_message = []
    
    # Formatting the message to include all order IDs for each user on the same line
    for user_id, order_ids in orders_by_user.items():
        order_ids_str = ", ".join([f"<code>#{order_id}</code>" for order_id in order_ids])
        order_info = f"• <b>ID активных заказов:</b> {order_ids_str}"
        orders_message.append(order_info)

    final_message = "\n\n".join(orders_message)
    
    await message.answer(final_message)



@routerAD.message(Command('deletepromo'), is_admin)
async def start_deleting_promo(message: types.Message, state: FSMContext):
    await message.answer("Введите ID промокода, который хотите удалить:")
    await state.set_state(PromoCodeStates.waiting_for_promo_id)


@routerAD.message(PromoCodeStates.waiting_for_promo_id)
async def handle_promo_id_for_deletion(message: types.Message, state: FSMContext):
    promo_id = message.text
    
    if not promo_id.isdigit():
        await message.answer("Пожалуйста, введите корректный ID промокода (целое число).")
        return

    promo_id = int(promo_id)

    promo_code = await da.get_promo_code_by_id(promo_id)
    
    if not promo_code:
        await message.answer(f"Промокод с ID <code>{promo_id}</code> не найден.")
        return

    await da.delete_promo_code(promo_id)

    await message.answer(f"Промокод с ID <code>{promo_id}</code> успешно удален.")
    await state.clear()


@routerAD.message(Command('allpromo'), is_admin)
async def show_all_promos(message: types.Message, state: FSMContext):
    existing_promo_codes = await rq.get_all_promo_codes()
    
    if not existing_promo_codes:
        await message.answer("На данный момент нет активных промокодов.")
        return
    
    # Format the promo codes into a readable message with the promo ID included
    promo_details = "\n".join(
        f"🆔 <b>ID:</b> <code>{promo.id}</code>\n"
        f"📜 <b>Промокод:</b> <code>{promo.promoText}</code>\n"
        f"🔢 <b>Количество активаций:</b> <code>{promo.activations}</code>\n"
        f"💸 <b>Скидка:</b> <code>{promo.percentage}%</code>\n"
        "---------------------------"
        for promo in existing_promo_codes
    )
    
    await message.answer(f"<b>Список всех активных промокодов:</b>\n\n{promo_details}")



@routerAD.message(Command('addpromo'), is_admin)
async def start_adding_promo(message: types.Message, state: FSMContext):
    await message.answer("Введите текст промокода:")
    await state.set_state(PromoCodeStates.waiting_for_promotext)


@routerAD.message(PromoCodeStates.waiting_for_promotext)
async def handle_promo_text(message: types.Message, state: FSMContext):
    promo_text = message.text

    existing_promo_codes = await rq.get_all_promo_codes() 
    if any(promo.promoText == promo_text for promo in existing_promo_codes):
        await message.answer("Промокод с таким текстом уже существует. Введите другой текст промокода:")
        return 

    await state.update_data(promo_text=promo_text)
    await message.answer("Введите количество активаций:")
    await state.set_state(PromoCodeStates.waiting_for_activations)


@routerAD.message(PromoCodeStates.waiting_for_activations)
async def handle_activations(message: types.Message, state: FSMContext):
    activations = message.text
    await state.update_data(activations=activations)

    await message.answer("Введите процент скидки:")
    await state.set_state(PromoCodeStates.waiting_for_percentage)


@routerAD.message(PromoCodeStates.waiting_for_percentage)
async def handle_percentage(message: types.Message, state: FSMContext):
    percentage = message.text
    await state.update_data(percentage=percentage)

    data = await state.get_data()
    promo_text = data.get('promo_text')
    activations = int(data.get('activations')) 
    percentage = float(data.get('percentage'))
    
    await da.add_promo_codes(promo_text, activations, percentage)
    await message.answer("Промокод успешно добавлен!")
    await state.clear()


@routerAD.callback_query(F.data.startswith('delete_'), is_admin)
async def delete_item(callback: CallbackQuery):
    await callback.message.delete()
    product_id = callback.data.split("_")[-1]
    await rq.orm_delete_product(int(product_id))
    await callback.answer(f"Товар удален по айди {product_id}", show_alert=True)
    await callback.message.answer(f"Товар удален по айди {product_id}", reply_markup=ke.admin_main_key())


@routerAD.callback_query(F.data.startswith('change_'), is_admin)
async def change_product_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    product_id = callback.data.split("_")[-1]

    product_for_change = await rq.get_item(int(product_id))

    AddProduct.product_for_change = product_for_change

    await callback.answer()
    await callback.message.answer(
        "Введите название товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.name)

@routerAD.message(Command('help'), is_admin)
async def help_command(message: Message):
    help_text = (
        "Команды администратора:\n\n"
        "/admin - Перейти в панель администратора и увидеть доступные действия.\n\n"
        "/cancel - Отменить текущее действие.\n\n"
        "/done - Завершить заказы.\n\n"
        "/delete_all_orders - Удалить все заказы.\n\n"
        "/cancel_order - Отменить конкретный заказ.\n\n"
        "/active_orders_id - Показать ID все активные заказы.\n\n"
        "/deletepromo - Удалить промокод.\n\n"
        "/allpromo - Показать все активные промокоды.\n\n"
        "/addpromo - Добавить новый промокод.\n\n"
        "/help - Показать это справочное сообщение.\n"
    )
    await message.answer(help_text)





@routerAD.message(Command('admin'), is_admin)
async def admin_features(message: Message):
    await message.answer("Добро пожаловать в админ панель!\n\nЧто хотите сделать?", reply_markup=ke.admin_main_key())

@routerAD.message(F.text == 'Добавить товар', is_admin)
async def add_item(message: Message, state: FSMContext):
    await state.set_state(AddProduct.name)
    await message.answer("Введите название товара:", reply_markup=types.ReplyKeyboardRemove())

@routerAD.message(AddProduct.name, or_f(F.text, F.text == '.'), is_admin)
async def name_item(message: Message, state: FSMContext):
     
    if message.text == ".":
        await state.update_data(name=AddProduct.product_for_change.ItemName)
    else:

        if len(message.text) >= 100:
            await message.answer(
                "Название товара не должно превышать 100 символов. \n Введите заново"
            )
            return
        await state.update_data(name=message.text)

    await message.answer("Введите описание товара:")
    await state.set_state(AddProduct.description)

@routerAD.message(AddProduct.description, or_f(F.text, F.text == '.'), is_admin)
async def description_item(message: Message, state: FSMContext):

    if message.text == ".":
        await state.update_data(description=AddProduct.product_for_change.ItemDescription)
    else:
        await state.update_data(description=message.text)
    await message.answer("Введите стоимость товара:")
    await state.set_state(AddProduct.price)

@routerAD.message(AddProduct.price, or_f(F.text, F.text == '.'), is_admin)
async def price_item(message: Message, state: FSMContext):

    if message.text == ".":
        await state.update_data(price=AddProduct.product_for_change.ItemPrice)
    else:
        try:
            float(message.text)
        except ValueError:
            await message.answer("Введите корректное значение цены")
            return

        await state.update_data(price=message.text)
    await message.answer("Введите количество товара:")
    await state.set_state(AddProduct.quantity)

@routerAD.message(AddProduct.quantity, or_f(F.text, F.text == '.'), is_admin)
async def quantity_item(message: Message, state: FSMContext):

    if message.text == ".":
        await state.update_data(quantity=AddProduct.product_for_change.ItemQuantity)
    else:
        try:
            int(message.text)
        except ValueError:
            await message.answer("Введите корректное значение количество")
            return

        await state.update_data(quantity=message.text)
    await message.answer("Отправьте изображение товара:")
    await state.set_state(AddProduct.image)

@routerAD.message(AddProduct.image, or_f(F.photo, F.text == '.'), is_admin)
async def image_item(message: Message, state: FSMContext):

    if message.text and message.text == ".":
        await state.update_data(image=AddProduct.product_for_change.ItemImg)
    else:
        if not message.photo:
            await message.answer("Пожалуйста, отправьте изображение товара.")
            return
        await state.update_data(image=str(message.photo[-1].file_id))

    await message.answer("Введите название товара на узбекском:")
    await state.set_state(AddProduct.name_uz)


@routerAD.message(AddProduct.name_uz, or_f(F.text, F.text == '.'), is_admin)
async def name_item_uz(message: Message, state: FSMContext):

    if message.text == ".":
        await state.update_data(name_uz=AddProduct.product_for_change.ItemNameUz)
    else:
        await state.update_data(name_uz=message.text)
    await message.answer("Введите описание товара на узбекском:")
    await state.set_state(AddProduct.description_uz)

@routerAD.message(AddProduct.description_uz, or_f(F.text, F.text == '.'), is_admin)
async def description_item_uz(message: Message, state: FSMContext):

    if message.text == ".":
        await state.update_data(description_uz=AddProduct.product_for_change.ItemDescriptionUz)
    else:
        await state.update_data(description_uz=message.text)
    data = await state.get_data()

    try:
        if AddProduct.product_for_change:
            await da.orm_update_product(AddProduct.product_for_change.Id, data)
        else:
            await da.admin_add_item(data)

        # # Add translations to the dictionary
        item_translations['uz'][data['name']] = data['name_uz']
        item_translations['uz'][data['description']] = data['description_uz']

        await message.answer("Товар добавлен", reply_markup=ke.admin_main_key())
        await state.clear()
    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}\nОбратись к программеру.",
            reply_markup=ke.admin_main_key(),
        )
        await state.clear()
    AddProduct.product_for_change = None

@routerAD.message(F.text == 'Все товары', is_admin)
async def all_item(message: Message):
    items = await rq.get_items()
    if not items:
        await message.answer("В базе данных нет товары!\n\nЧтобы добавить товар нажмите на кнопку: <b>Добавить товар</b>", reply_markup=ke.admin_main_key())
    else:
        kb = await ke.adminItems()
        await message.answer("Список всех товаров:\n\nЧтобы получить всю информацию о товаре, нажмите на название:", reply_markup=kb)

        


@routerAD.message(is_admin)
async def forItems(message: Message):
    all_item_names = await allItemNamesRu()

    if message.text in all_item_names:
        item_details = await rq.getItemDetailsByName(message.text)
        if item_details:
            formatted_price = f"{item_details.ItemPrice:,.0f}"
            response = (
                f"Айди товара: <b>{item_details.Id}</b>\n\n"
                f"Название товара: <b>{item_details.ItemName}</b>\n\n"
                f"Название продукта на узбекском: <b>{item_details.ItemNameUz}</b>\n\n"
                f"Описание товаров: <b>{item_details.ItemDescription}</b>\n\n"
                f"Описание товара на узбекском: <b>{item_details.ItemDescriptionUz}</b>\n\n"
                f"Цена товара: <b>{formatted_price}</b>\n\n"
                f"Количество товара: <b>{item_details.ItemQuantity}</b>\n\n"
            )
            
            in_edit_or_change = await il.get_callback_btns(btns={
            'Удалить': f'delete_{item_details.Id}',
            'Изменить': f'change_{item_details.Id}'
            })
            await message.answer_photo(photo=f'{item_details.ItemImg}', caption=response, reply_markup=in_edit_or_change)
        else:
            await message.answer("Item details not found.")
    else:
        await message.answer("Товар не найден.")