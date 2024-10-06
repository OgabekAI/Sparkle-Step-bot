from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncSession, AsyncAttrs, async_sessionmaker, create_async_engine
from settings import DB_LITE
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from datetime import datetime, timedelta

engine = create_async_engine(url=DB_LITE, echo=True, connect_args={"timeout": 10})

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


current_time = datetime.utcnow()
gmt_plus_5_time = current_time + timedelta(hours=5)

class Base(AsyncAttrs, DeclarativeBase):
    created = Column(DateTime, default=gmt_plus_5_time)
    updated = Column(DateTime, default=gmt_plus_5_time)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tgID = Column(Integer, nullable=False, unique=True)
    lang = Column(String(10))
    userName = Column(String(50), default=None)
    userNumber = Column(String(20))
    userPaymentMethod = Column(String(20), default=None)
    userPromoCode = Column(String(20), default=None)
    latitude = Column(Float())
    longitude = Column(Float())

class Item(Base):
    __tablename__ = "items"

    Id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    ItemName = Column(String(100))
    ItemNameUz = Column(String(100))
    ItemDescription = Column(Text)
    ItemDescriptionUz = Column(Text)
    ItemPrice = Column(Float(asdecimal=True))
    ItemQuantity = Column(Integer)
    ItemImg = Column(String())

class Cart(Base):
    __tablename__ = "cart"

    Id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    userId = Column(Integer, ForeignKey('users.tgID', ondelete='CASCADE')) 
    itemId = Column(Integer, ForeignKey('items.Id', ondelete='CASCADE'))
    itemName = Column(String(100))
    orderQuantity = Column(Integer)

    user = relationship('User', backref='carts')
    item = relationship('Item', backref='carts')

class Order(Base):
    __tablename__ = "orders"

    orderId = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    userId = Column(Integer, ForeignKey('users.tgID', ondelete='CASCADE'))
    userNumber = Column(String(20))
    itemId = Column(Integer, ForeignKey('items.Id', ondelete='CASCADE'))
    itemName = Column(String(100))
    itemNameUz = Column(String(100))
    orderTotalSum = Column(Float())
    orderQuantity = Column(Integer)
    userPaymentMethod = Column(String(20))
    userPromoCode = Column(String(20), default=None)
    orderStatus = Column(Boolean(), default=True)
    isOrderDeleted = Column(Boolean(), default=False)


class PromoCode(Base):
    __tablename__ = "promocodes"

    id = Column(Integer, primary_key=True)
    promoText = Column(String(100), unique=True)
    activations = Column(Integer, default=0)
    percentage = Column(Float, default=0)


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)