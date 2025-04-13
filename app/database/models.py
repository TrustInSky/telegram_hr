from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Text, DateTime
from datetime import date, datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    telegram_id = Column(Integer, primary_key=True, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=True)
    fullname = Column(String, nullable=False)
    birth_date = Column(Date, nullable=True)
    hire_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    tpoints = Column(Integer, default=0)
    department = Column(String, nullable=True)
    post = Column(String, nullable=True)
    role = Column(String, nullable=False, default="user")

    orders = relationship("Order", back_populates="user")
    carts = relationship("Cart", back_populates="user")  # Изменили на связь с Cart
    
    
class Cart(Base):
    __tablename__ = "carts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="carts")  # Обратная связь
    items = relationship("CartItem", back_populates="cart")


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("catalog.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    size = Column(String, nullable=True)
    color = Column(String, nullable=True)
    added_at = Column(DateTime, default=datetime.now)
    
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")


class TPointsTransaction(Base):
    __tablename__ = "tpoints"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Integer, nullable=False)
    transaction_date = Column(Date, default=date.today)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("catalog.id"), nullable=True)
    comment = Column(Text, nullable=True)

    product = relationship("Product", back_populates="tpoints")
    order = relationship("Order", back_populates="transactions")
    
    
class CommonImage(Base):
    __tablename__ = "common_images"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    image_url = Column(String, nullable=True)
    

class Product(Base):
    __tablename__ = "catalog"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)
    image_url = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)
    stock = Column(Integer, default=1)
    sizes = Column(String, nullable=True)
    colors = Column(String, nullable=True)

    order_items = relationship("OrderItem", back_populates="product")
    tpoints = relationship("TPointsTransaction", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    status = Column(String, default="pending")
    order_date = Column(DateTime, default=datetime.now)
    total_price = Column(Integer, nullable=False)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    transactions = relationship("TPointsTransaction", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("catalog.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    price_at_purchase = Column(Integer, nullable=False)
    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


class AnonymousQuestion(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    question_text = Column(String, nullable=False)
    question_status = Column(String, nullable=True)
    submitted_at = Column(Date, default=date.today)