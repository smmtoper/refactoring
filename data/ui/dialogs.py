from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDialogButtonBox
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки расчета")

        layout = QVBoxLayout()
        form = QFormLayout()

        # Поля ввода
        self.temp_start = QLineEdit("1.0")
        self.temp_stop = QLineEdit("2.0")
        self.density = QLineEdit("0.5")
        self.closure = QComboBox()
        self.closure.addItems(["MS", "MS Modified", "HNC", "PY", "MHNC"])

        form.addRow("Начальная температура:", self.temp_start)
        form.addRow("Конечная температура:", self.temp_stop)
        form.addRow("Плотность:", self.density)
        form.addRow("Метод замыкания:", self.closure)

        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_settings(self):
        return {
            'temp_start': float(self.temp_start.text()),
            'temp_stop': float(self.temp_stop.text()),
            'density': float(self.density.text()),
            'closure': self.closure.currentText()
        }


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        # ... (реализация диалога "О программе")