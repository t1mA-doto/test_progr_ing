from io import BytesIO
from PyQt5.QtWidgets import QDialog, QFileDialog
from models.category import Category
from ui.CategoryDialog import Ui_CategoryDialog


class CategoryDialog(Ui_CategoryDialog, QDialog):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.setupUi(self)
        self.choiceFileButton.clicked.connect(self.choice_file)
        self._image = None

    def choice_file(self):
        self._image = QFileDialog.getOpenFileName(self, 'Open file', filter="Image files (*.jpg *.png)")
        self.choisenFIleName.setText(self._image[0])

    def accept(self) -> None:
        category = Category(None, self.nameEdit.text(), self.textEdit.toPlainText(), self._image)
        if category.is_valid:
            category.save()
            super().accept()
