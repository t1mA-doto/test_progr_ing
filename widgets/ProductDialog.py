from decimal import Decimal

from PyQt5.QtWidgets import QDialog, QFileDialog

from models.category import Category
from models.product import Product
from ui.ProductDialog import Ui_ProductDialog


class ProductDialog(Ui_ProductDialog, QDialog):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.choiceFileButton.clicked.connect(self.choice_file)
        self._image = None
        self._categories = Category.fetch_all()
        for category in self._categories:
            self.categoryComboBox.addItem(category.label, category)

    def choice_file(self):
        self._image = QFileDialog.getOpenFileName(self, 'Open file', filter="Image files (*.jpg *.png)")
        self.choisenFIleName.setText(self._image[0])

    def accept(self) -> None:
        product = Product(None, self.nameEdit.text(), Decimal(self.priceSpinBox.text()), self._image, self.categoryComboBox.currentData())
        if product.is_valid:
            product.save()
            super().accept()
