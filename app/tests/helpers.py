# app/tests/factories.py


class FakeProduct:
    """
    A stand-in for your Product model in repository tests.
    """

    name = "TestProduct"  # Class-level attr used for filtering.

    def __init__(self, id, name, description, price, available_quantity):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.available_quantity = available_quantity

    def __eq__(self, other):
        if not isinstance(other, FakeProduct):
            return False
        return (
            self.id == other.id
            and self.name == other.name
            and self.description == other.description
            and float(self.price) == float(other.price)
            and self.available_quantity == other.available_quantity
        )

    def __repr__(self):
        return f"FakeProduct(id={self.id}, name={self.name})"


class DummyProduct:
    """
    Another stand-in for your Product model, used in service tests (or anywhere else).
    """

    def __init__(self, id, name, description, price, available_quantity):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.available_quantity = available_quantity

    def __eq__(self, other):
        return (
            isinstance(other, DummyProduct)
            and self.id == other.id
            and self.name == other.name
            and self.description == other.description
            and self.price == other.price
            and self.available_quantity == other.available_quantity
        )


class FakeBill:
    """
    A stand-in for your Bill model in repository tests.
    """

    user_id = 0

    def __init__(self, id, user_id, date, total_amount):
        self.id = id
        self.user_id = user_id
        self.date = date
        self.total_amount = total_amount

    def __eq__(self, other):
        if not isinstance(other, FakeBill):
            return False
        return (
            self.id == other.id
            and self.user_id == other.user_id
            and self.date == other.date
            and float(self.total_amount) == float(other.total_amount)
        )

    def __repr__(self):
        return f"FakeBill(id={self.id}, user_id={self.user_id})"


class DummyBill:
    """
    Another stand-in for your Bill model, used in service tests.
    """

    def __init__(self, id, user_id, date, total_amount):
        self.id = id
        self.user_id = user_id
        self.date = date
        self.total_amount = total_amount

    def __eq__(self, other):
        return (
            isinstance(other, DummyBill)
            and self.id == other.id
            and self.user_id == other.user_id
            and self.date == other.date
            and float(self.total_amount) == float(other.total_amount)
        )

    def __repr__(self):
        return f"DummyBill(id={self.id}, user_id={self.user_id})"
