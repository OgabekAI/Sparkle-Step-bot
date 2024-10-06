from database.models import Item, Order, PromoCode, session_maker
from sqlalchemy import insert, select, update, delete, desc
from datetime import datetime, timedelta

current_time = datetime.utcnow()
gmt_plus_5_time = current_time + timedelta(hours=5)


async def admin_add_item(data: dict):
    async with session_maker() as session:
        obj = Item(
        ItemName=data["name"],
        ItemNameUz=data["name_uz"],
        ItemDescriptionUz=data["description_uz"],
        ItemDescription=data["description"],
        ItemPrice=float(data["price"]),
        ItemQuantity=int(data["quantity"]),
        ItemImg=str(data["image"]),
    )
    session.add(obj)
    await session.commit()


async def delete_all_orders():
    async with session_maker() as session:
        query = delete(Order)
        await session.execute(query)
        await session.commit()

async def get_promo_code_by_id(promo_id: int):
    async with session_maker() as session: 
        query = select(PromoCode).where(PromoCode.id == promo_id)
        result = await session.execute(query)
        return result.scalars().first()

async def delete_promo_code(promo_id: int):
    async with session_maker() as session:  
        query = delete(PromoCode).where(PromoCode.id == promo_id)  
        await session.execute(query)  
        await session.commit()  


async def orm_update_product(product_id: int, data):
    async with session_maker() as session:
        query = update(Item).where(Item.Id == product_id).values(
            ItemName=data["name"],
            ItemNameUz=data["name_uz"],
            ItemDescriptionUz=data["description_uz"],
            ItemDescription=data["description"],
            ItemPrice=float(data["price"]),
            ItemQuantity=int(data["quantity"]),
            ItemImg=str(data["image"]),)
        await session.execute(query)
        await session.commit()


async def update_order_status_by_ids(order_ids):
    async with session_maker() as session:
        query = select(Order.orderId).where(Order.orderId.in_(order_ids))
        result = await session.execute(query)
        existing_order_ids = [row[0] for row in result.fetchall()]

        invalid_order_ids = list(set(order_ids) - set(existing_order_ids))

        if invalid_order_ids:
            return False, invalid_order_ids

        update_query = (
            update(Order)
            .where(Order.orderId.in_(existing_order_ids))
            .values(
                orderStatus=False,
                updated=gmt_plus_5_time
            )
        )
        await session.execute(update_query)
        await session.commit()
        return True, None
    
async def get_completed_orders(order_ids: list[int]) -> list[int]:
    async with session_maker() as session:
        stmt = (
            select(Order.orderId)
            .where(Order.orderId.in_(order_ids), Order.orderStatus == False)
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall()]
    

async def OrderDeleted(order_ids):
    async with session_maker() as session:
        query = select(Order.orderId).where(Order.orderId.in_(order_ids))
        result = await session.execute(query)
        existing_order_ids = [row[0] for row in result.fetchall()]

        invalid_order_ids = list(set(order_ids) - set(existing_order_ids))

        if invalid_order_ids:
            return False, invalid_order_ids

        update_query = (
            update(Order)
            .where(Order.orderId.in_(existing_order_ids))
            .values(
                isOrderDeleted=True,
                updated=gmt_plus_5_time
            )
        )
        await session.execute(update_query)
        await session.commit()
        return True, None
    
async def get_user_id_by_order_id(order_ids):
    async with session_maker() as session:
        query = select(Order.userId, Order.orderId).where(Order.orderId.in_(order_ids))
        result = await session.execute(query)
        user_orders = {}
        for row in result.fetchall():
            user_id = row[0]
            order_id = row[1]
            if user_id in user_orders:
                user_orders[user_id].append(order_id)
            else:
                user_orders[user_id] = [order_id]
        return user_orders
    

async def add_promo_codes(promo_text: str, activations: int, percentage: int):
    async with session_maker() as session:
        query = insert(PromoCode).values(
            promoText=promo_text,  # Change this line
            activations=activations,
            percentage=percentage
        )
        await session.execute(query)
        await session.commit()

async def get_all_active_orders():
    async with session_maker() as session:
        query = select(Order).where(Order.orderStatus == True)
        result = await session.execute(query)
        active_orders = result.scalars().all()
        return active_orders
    

async def get_all_finished_orders():
    async with session_maker() as session:
        query = select(Order).where(Order.orderStatus == False)
        result = await session.execute(query)
        active_orders = result.scalars().all()
        return active_orders