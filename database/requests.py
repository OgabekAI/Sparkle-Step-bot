from database.models import User, Item, Cart, Order, PromoCode, session_maker
from sqlalchemy import insert, select, update, delete, func
from datetime import datetime, timedelta

current_time = datetime.utcnow()
gmt_plus_5_time = current_time + timedelta(hours=5)


async def user_exists(tgID):
    async with session_maker() as session:
        query = select(User).where(User.tgID == tgID)
        result = await session.execute(query)
        return result.scalar() is not None

async def add_user(tgID, lang):
    async with session_maker() as session:
        query = insert(User).values(tgID=tgID, lang=lang)
        await session.execute(query)
        await session.commit()

async def get_lang(tgID):
    async with session_maker() as session:
        query = select(User.lang).where(User.tgID == tgID)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
async def get_user_number(tgID):
    async with session_maker() as session:
        query = select(User.userNumber).where(User.tgID == tgID)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    

async def get_user_lat(tgID):
    async with session_maker() as session:
        query = select(User.latitude).where(User.tgID == tgID)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
async def get_user_long(tgID):
    async with session_maker() as session:
        query = select(User.longitude).where(User.tgID == tgID)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
async def update_lang(tgID, new_lang):
    async with session_maker() as session:
        stmt = (
            update(User)
            .where(User.tgID == tgID)
            .values(lang=new_lang)
        )
        await session.execute(stmt)
        await session.commit()

async def save_user_to_db(tgID, new_name):
    async with session_maker() as session:
        stmt = (
            update(User)
            .where(User.tgID == tgID)
            .values(userName=new_name)
        )
        await session.execute(stmt)
        await session.commit()

async def get_user_name(tgID):
    async with session_maker() as session:
        query = select(User.userName).where(User.tgID == tgID)
        result = await session.execute(query)
        return result.scalar_one_or_none()

async def delete_user(tgID):
    async with session_maker() as session:
        query = delete(User).where(User.tgID == tgID)
        await session.execute(query)
        await session.commit()

async def save_location(tgID, lang, latitude, longitude):
    async with session_maker() as session:
        query = (
            update(User)
            .where(User.tgID == tgID)
            .values(
                lang=lang,
                latitude=latitude,
                longitude=longitude,
                updated=gmt_plus_5_time
            )
        )
        await session.execute(query)
        await session.commit()

async def save_number(tgID, userNumber):
    async with session_maker() as session:
        query = (
            update(User)
            .where(User.tgID == tgID)
            .values(
                userNumber=userNumber,
                updated=gmt_plus_5_time
            )
        )
        await session.execute(query)
        await session.commit()

async def get_items():
    async with session_maker() as session:
        query = select(Item)
        result = await session.execute(query)
        return result.scalars().all()

async def get_item(product_id: int):
    async with session_maker() as session:
        query = select(Item).where(Item.Id == product_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

async def orm_delete_product(product_id: int):
    async with session_maker() as session:
        query = delete(Item).where(Item.Id == product_id)
        await session.execute(query)
        await session.commit()

async def getItemDetailsByName(item_name):
    async with session_maker() as session:
        query = select(Item).where(Item.ItemName == item_name)
        result = await session.execute(query)
        return result.scalar_one_or_none()

async def getItemDetailsByNameUz(item_nameUz):
    async with session_maker() as session:
        query = select(Item).where(Item.ItemNameUz == item_nameUz)
        result = await session.execute(query)
        return result.scalar_one_or_none()

async def orm_add_to_cart(user_id: int, product_id: int, item_name: str, quantity: int):
    async with session_maker() as session:
        obj = Cart(
            userId=user_id,
            itemId=product_id,
            itemName=item_name,
            orderQuantity=quantity
        )
        session.add(obj)
        await session.commit()

async def get_cart_items(tgID):
    async with session_maker() as session:
        query = select(Cart).where(Cart.userId == tgID)
        result = await session.execute(query)
        cart_items = result.scalars().all()
        
        return cart_items



async def get_items_by_id(item_id):
    async with session_maker() as session:
        query = select(Item).where(Item.Id == item_id)
        result = await session.execute(query)
        return result.scalar()
    
async def get_order_ids_by_user_id(user_id):
    async with session_maker() as session:
        query = select(Order.orderId).where(
            (Order.userId == user_id) & (Order.orderStatus == True)
        )
        result = await session.execute(query)
        return result.scalars().all()
    

async def get_order_quantity_sum(tgID):
    async with session_maker() as session:
        stmt = select(
            Cart.itemId,
            func.sum(Cart.orderQuantity).label('total_quantity')
        ).where(
            Cart.userId == tgID
        ).group_by(
            Cart.itemId
        )

        result = await session.execute(stmt)
        return result.all()
    
async def delete_from_cart(tgID: int):
    async with session_maker() as session:
        query = delete(Cart).where(Cart.userId == tgID)
        await session.execute(query)
        await session.commit()

async def delete_item_from_cart(tgID: int, item_id: int):
    async with session_maker() as session:
        query = delete(Cart).where(Cart.userId == tgID, Cart.itemId == item_id)
        await session.execute(query)
        await session.commit()


async def add_order_to_db(userId, userNumber, itemId, itemName, itemNameUz, orderTotalSum, orderQuantity, userPaymentMethod, userPromoCode, orderStatus, created):
    async with session_maker() as session:
        query = insert(Order).values(userId=userId,
                                     userNumber=userNumber,
                                      itemId=itemId,
                                        itemName=itemName,
                                        itemNameUz=itemNameUz,
                                          orderTotalSum=orderTotalSum,
                                          orderQuantity=orderQuantity,
                                          userPaymentMethod=userPaymentMethod,
                                          userPromoCode=userPromoCode,
                                          orderStatus=orderStatus,
                                          created=created)
        await session.execute(query)
        await session.commit()

async def update_item_quantity(item_id: int, new_quantity: int):
    async with session_maker() as session:
        query = (
            update(Item)
            .where(Item.Id == item_id)
            .values(
                ItemQuantity=new_quantity,
                updated=gmt_plus_5_time
            )
        )
        await session.execute(query)
        await session.commit()


async def get_user_location(tgID):
    async with session_maker() as session:
        result = await session.execute(select(User.latitude, User.longitude).where(User.tgID == tgID))
        return result.first() 


async def update_user_location(tgID, latitude, longitude):
    async with session_maker() as session:
        query = update(User).where(User.tgID == tgID).values(latitude=latitude, longitude=longitude)
        await session.execute(query)
        await session.commit()


async def update_payment_method(tgID: int, new_method: str):
    async with session_maker() as session:
        query = (
            update(User)
            .where(User.tgID == tgID)
            .values(
                userPaymentMethod=new_method,
                updated=gmt_plus_5_time
            )
        )
        await session.execute(query)
        await session.commit()

async def get_user_payment_method(tgID):
    async with session_maker() as session:
        query = select(User.userPaymentMethod).where(User.tgID == tgID)
        result = await session.execute(query)
        return result.scalar_one_or_none()
        
async def update_user_promo(tgID: int, new_promo: str):
    async with session_maker() as session:
        query = (
            update(User)
            .where(User.tgID == tgID)
            .values(
                userPromoCode=new_promo,
                updated=gmt_plus_5_time
            )
        )
        await session.execute(query)
        await session.commit()


async def get_user_promo(tgID):
    async with session_maker() as session:
        query = select(User.userPromoCode).where(User.tgID == tgID)
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    

async def get_all_promo_codes():
    async with session_maker() as session:
        query = select(PromoCode)
        result = await session.execute(query)
        return result.scalars().all() 
    

    
async def update_promo_activations(promo_id: int, new_activations: int):
    async with session_maker() as session:
        query = (
            update(PromoCode)
            .where(PromoCode.id == promo_id)
            .values(
                activations=new_activations,
                updated=gmt_plus_5_time
            )
        )
        await session.execute(query)
        await session.commit()


async def get_all_active_orders():
    async with session_maker() as session:
        query = select(Order).where(Order.orderStatus == True)
        result = await session.execute(query)
        active_orders = result.scalars().all()
        return active_orders
    
async def get_user_active_orders(user_id):
    async with session_maker() as session:
        query = select(Order).where(
            (Order.userId == user_id) & (Order.orderStatus == True)
        )
        result = await session.execute(query)
        return result.scalars().all()