from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from models import BaseModel
from models.product import Product


@dataclass
class Order(BaseModel):
    created_at: datetime
    total: Decimal

    @classmethod
    @property
    def _name(cls):
        return 'Заказ'


@dataclass
class OrderProduct(BaseModel):
    product: Product
    price: Decimal
    count: int
    order: Order

    @classmethod
    @property
    def _name(cls):
        return 'Блюда в заказе'
