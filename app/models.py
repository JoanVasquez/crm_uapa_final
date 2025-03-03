"""SQLAlchemy models for the application.

This module defines the database models for users, products, bills, and sells.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.config.database import Base


class User(Base):
    """Model representing a user in the system.

    Attributes:
        id (int): Primary key.
        email (str): Unique email of the user.
        name (str): The user's full name.
        password (str): Hashed password.
        is_active (bool): Whether the user is active.
        bills (list[Bill]): Bills associated with the user.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationship: A user can have many bills.
    bills = relationship("Bill", back_populates="user", cascade="all, delete-orphan")

    def __str__(self):
        """Return the string representation of the user."""
        return self.email

    def to_dict(self):
        """Return a dictionary representation of the user."""
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "is_active": self.is_active,
        }


class Product(Base):
    """Model representing a product.

    Attributes:
        id (int): Primary key.
        name (str): Unique product name.
        description (str): Description of the product.
        price (Decimal): Price of the product.
        available_quantity (int): Number of items available.
        sells (list[Sell]): List of sales of the product.
    """

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    available_quantity = Column(Integer, default=0, nullable=False)

    # Relationship: A product can be sold many times.
    sells = relationship("Sell", back_populates="product", cascade="all, delete-orphan")

    def __str__(self):
        """Return the string representation of the product."""
        return self.name

    def to_dict(self):
        """Return a dictionary representation of the product."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "available_quantity": self.available_quantity,
        }


class Bill(Base):
    """Model representing a bill.

    Attributes:
        id (int): Primary key.
        user_id (int): Foreign key referencing the user.
        date (datetime): Date when the bill was created.
        total_amount (Decimal): Total amount of the bill.
        sells (list[Sell]): Sales associated with the bill.
        user (User): The user who owns the bill.
    """

    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Relationship: A bill has many sale items.
    sells = relationship("Sell", back_populates="bill", cascade="all, delete-orphan")
    # Relationship: The bill belongs to one user.
    user = relationship("User", back_populates="bills")

    def __str__(self):
        """Return the string representation of the bill."""
        return f"Bill #{self.id} for user {self.user_id}"

    def to_dict(self):
        """Return a dictionary representation of the bill."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date.isoformat() if self.date else None,
            "total_amount": float(self.total_amount),
        }


class Sell(Base):
    """Model representing a sale transaction.

    Attributes:
        id (int): Primary key.
        bill_id (int): Foreign key referencing a bill.
        product_id (int): Foreign key referencing a product.
        quantity (int): Number of items sold.
        sale_price (Decimal): Sale price of the product at the time of sale.
        product (Product): The product sold.
        bill (Bill): The bill containing this sale.
    """

    __tablename__ = "sells"

    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=False)

    # Relationships: each sell references a product and a bill.
    product = relationship("Product", back_populates="sells")
    bill = relationship("Bill", back_populates="sells")

    def __str__(self):
        """Return the string representation of the sale."""
        return f"Sell #{self.id}: {self.quantity} of {self.product_id} on bill {self.bill_id}"

    def to_dict(self):
        """Return a dictionary representation of the sale."""
        return {
            "id": self.id,
            "bill_id": self.bill_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "sale_price": float(self.sale_price),
        }
