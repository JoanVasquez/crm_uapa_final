import unittest
# Replace 'your_module' with the actual module name
from app.utils.deserialize_instance import deserialize_instance

# A dummy model class for testing.


class DummyModel:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    def __eq__(self, other):
        return isinstance(other, DummyModel) and self.id == other.id and self.name == other.name

    def __repr__(self):
        return f"DummyModel(id={self.id}, name={self.name})"


class TestDeserializeInstance(unittest.TestCase):
    def test_deserialize_instance_success(self):
        # Given data for a DummyModel instance.
        data = {"id": 1, "name": "Alice"}
        # When calling deserialize_instance, it should create an instance with the given data.
        instance = deserialize_instance(DummyModel, data)
        self.assertIsInstance(instance, DummyModel)
        self.assertEqual(instance.id, 1)
        self.assertEqual(instance.name, "Alice")

    def test_deserialize_instance_failure_invalid_key(self):
        # If data contains a key that the model does not accept,
        # the constructor should raise a TypeError.
        data = {"id": 1, "invalid_key": "value"}
        with self.assertRaises(TypeError):
            deserialize_instance(DummyModel, data)
