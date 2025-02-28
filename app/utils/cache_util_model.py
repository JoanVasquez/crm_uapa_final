from dataclasses import dataclass


@dataclass
class CacheModel:
    key: str
    expiration: int
