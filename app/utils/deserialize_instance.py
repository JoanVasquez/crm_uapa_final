from typing import Any, Dict, Type, TypeVar

T = TypeVar("T")


def deserialize_instance(model: Type[T], data: Dict[str, Any]) -> T:
    """
    Recreate a SQLAlchemy model instance from a dictionary.
    Note: This creates a new instance but does not attach it to a session.
    """
    return model(**data)
