from typing import Union

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget

from models.category import Category
from models.product import Product
from ui.ChoicePile import Ui_Pile


class ChoicePile(Ui_Pile, QWidget):
    clicked = pyqtSignal()

    def __init__(self, title: str, image: str, obj: Union[Category, Product]):
        self.obj = obj
        super().__init__()
        self.setupUi(self)
        self.pileTitle.setText(title)
        stylesheet = f'''background-image: url({image});
                        background-repeat: no-repeat;
                        background-position: center;'''
        self.imageFrame.setStyleSheet(stylesheet)
        self.pileTitle.setStyleSheet('background: #1212ce; color: #ffffff;')

    def mousePressEvent(self, a0):
        self.clicked.emit()
