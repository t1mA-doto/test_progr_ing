from dataclasses import dataclass
from decimal import Decimal

from models import BaseModel, Image
from models.category import Category


@dataclass
class Product(BaseModel):
    name: str
    price: Decimal
    image: Image
    category: Category

    @classmethod
    @property
    def _name(cls):
        return 'Блюда'
