from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
from PyQt5.QtCore import Qt


class ResultsPlotter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Создание таблицы
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Температура", "Плотность", "g(max)", "h(max)", "Давление", "Энергия"
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        # Компоновка
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def add_results(self, results):
        """Добавление строки с результатами"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0,
                           QTableWidgetItem(f"{results['Temperature']:.2f}"))
        self.table.setItem(row, 1,
                           QTableWidgetItem(f"{results['Density']:.4f}"))
        self.table.setItem(row, 2,
                           QTableWidgetItem(f"{results['g_max']:.4f}"))
        self.table.setItem(row, 3,
                           QTableWidgetItem(f"{results['h_max']:.4f}"))

        # Прокрутка к последней строке
        self.table.scrollToBottom()