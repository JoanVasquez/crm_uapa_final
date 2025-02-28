from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    Numeric
)
from sqlalchemy.orm import relationship
from app.config.database import Base
from datetime import datetime

# -------------------------------
# Existing User model (example)
# -------------------------------


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # New relationship: a user can have many bills.
    bills = relationship("Bill", back_populates="user",
                         cascade="all, delete-orphan")

    def __str__(self):
        return self.email

# -------------------------------
# New Product model
# -------------------------------


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    # Using Numeric for price is common when you need decimals.
    price = Column(Numeric(10, 2), nullable=False)
    available_quantity = Column(Integer, default=0, nullable=False)

    # Relationship: a product can be sold many times.
    sells = relationship("Sell", back_populates="product",
                         cascade="all, delete-orphan")

    def __str__(self):
        return self.name

# -------------------------------
# New Bill model (Invoice)
# -------------------------------


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # A timestamp for when the bill was created.
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    # Total amount (for example, in dollars as a decimal)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Relationship: a bill has many sale items.
    sells = relationship("Sell", back_populates="bill",
                         cascade="all, delete-orphan")
    # Relationship: the bill belongs to one user.
    user = relationship("User", back_populates="bills")

    def __str__(self):
        return f"Bill #{self.id} for user {self.user_id}"

# -------------------------------
# New Sell model (Sale Line)
# -------------------------------


class Sell(Base):
    __tablename__ = "sells"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    # Sale price (price at the time of sale); using Numeric for currency.
    sale_price = Column(Numeric(10, 2), nullable=False)

    # Relationships: each sell references a product and a bill.
    product = relationship("Product", back_populates="sells")
    bill = relationship("Bill", back_populates="sells")

    def __str__(self):
        return f"Sell #{self.id}: {self.quantity} of {self.product_id} on bill {self.bill_id}"
