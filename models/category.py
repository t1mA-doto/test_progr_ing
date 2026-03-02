from dataclasses import dataclass

from models import BaseModel, Image


@dataclass
class Category(BaseModel):
    """Категория блюд

    Args:
        label (str): Заголовок
        text (str): Описание
        image (Image): Путь к изображению
    """
    label: str
    text: str
    image: Image

    @classmethod
    @property
    def _name(cls):
        return 'Категория'
