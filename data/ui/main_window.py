import sys
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTabWidget, QStatusBar, QGroupBox,
    QFormLayout, QDoubleSpinBox, QSpinBox, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import QThread, Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from core.solver import LiquidSolver
from core.constants import ClosureType, SolutionMethod, PotentialType, EquationType
from .worker import Worker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlotterWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        self.ax1 = self.figure.add_subplot(211)
        self.ax2 = self.figure.add_subplot(212)

        self.ax1.set_title("Radial Distribution Function g(r)")
        self.ax1.set_xlabel("Distance r")
        self.ax1.set_ylabel("g(r)")
        self.ax1.grid(True)

        self.ax2.set_title("Total Correlation Function h(r)")
        self.ax2.set_xlabel("Distance r")
        self.ax2.set_ylabel("h(r)")
        self.ax2.grid(True)

        self.line_g, = self.ax1.plot([], [], 'b-')
        self.line_h, = self.ax2.plot([], [], 'r-')

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.figure.tight_layout()

    def update_plot(self, r, g, h):
        self.line_g.set_data(r, g)
        self.line_h.set_data(r, h)
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()
        self.canvas.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Liquid Structure Solver")
        self.setGeometry(100, 100, 1400, 900)

        self.solver = LiquidSolver()
        self.worker_thread = None
        self.worker = None

        self.init_ui()
        self.setup_connections()
        self.update_initial_plot()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Левая панель - параметры
        left_panel = QVBoxLayout()

        # Группа параметров системы
        system_group = QGroupBox("System Parameters")
        system_layout = QFormLayout()

        self.eq_type_combo = QComboBox()
        self.eq_type_combo.addItems([et.name for et in EquationType])
        system_layout.addRow("Equation Type:", self.eq_type_combo)

        self.potential_combo = QComboBox()
        self.potential_combo.addItems([pt.name for pt in PotentialType])
        system_layout.addRow("Potential:", self.potential_combo)

        self.method_combo = QComboBox()
        self.method_combo.addItems([sm.value for sm in SolutionMethod])
        system_layout.addRow("Solution Method:", self.method_combo)

        self.closure_combo = QComboBox()
        self.closure_combo.addItems([ct.name for ct in ClosureType])
        system_layout.addRow("Closure Type:", self.closure_combo)

        system_group.setLayout(system_layout)
        left_panel.addWidget(system_group)

        # Группа параметров сетки
        grid_group = QGroupBox("Grid Parameters")
        grid_layout = QFormLayout()

        self.L_spin = QDoubleSpinBox()
        self.L_spin.setRange(1.0, 100.0)
        self.L_spin.setValue(10.0)
        grid_layout.addRow("System Size (L):", self.L_spin)

        self.Nd_spin = QSpinBox()
        self.Nd_spin.setRange(100, 10000)
        self.Nd_spin.setValue(500)
        grid_layout.addRow("Grid Points (Nd):", self.Nd_spin)

        grid_group.setLayout(grid_layout)
        left_panel.addWidget(grid_group)

        # Группа температурных параметров
        temp_group = QGroupBox("Temperature Parameters")
        temp_layout = QFormLayout()

        self.T0_spin = QDoubleSpinBox()
        self.T0_spin.setRange(0.01, 10.0)
        self.T0_spin.setValue(0.5)
        temp_layout.addRow("Start Temp (T0):", self.T0_spin)

        self.Tk_spin = QDoubleSpinBox()
        self.Tk_spin.setRange(0.01, 10.0)
        self.Tk_spin.setValue(2.0)
        temp_layout.addRow("End Temp (Tk):", self.Tk_spin)

        self.dT_spin = QDoubleSpinBox()
        self.dT_spin.setRange(0.01, 1.0)
        self.dT_spin.setValue(0.1)
        temp_layout.addRow("Temp Step (dT):", self.dT_spin)

        temp_group.setLayout(temp_layout)
        left_panel.addWidget(temp_group)

        # Группа параметров плотности
        rho_group = QGroupBox("Density Parameters")
        rho_layout = QFormLayout()

        self.rho0_spin = QDoubleSpinBox()
        self.rho0_spin.setRange(0.01, 1.5)
        self.rho0_spin.setValue(0.1)
        rho_layout.addRow("Start Density (ρ0):", self.rho0_spin)

        self.rhok_spin = QDoubleSpinBox()
        self.rhok_spin.setRange(0.01, 1.5)
        self.rhok_spin.setValue(0.9)
        rho_layout.addRow("End Density (ρk):", self.rhok_spin)

        self.drho_spin = QDoubleSpinBox()
        self.drho_spin.setRange(0.01, 0.2)
        self.drho_spin.setValue(0.05)
        rho_layout.addRow("Density Step (dρ):", self.drho_spin)

        rho_group.setLayout(rho_layout)
        left_panel.addWidget(rho_group)

        # Группа параметров сходимости
        conv_group = QGroupBox("Convergence Parameters")
        conv_layout = QFormLayout()

        self.conv_spin = QDoubleSpinBox()
        self.conv_spin.setDecimals(8)
        self.conv_spin.setRange(1e-10, 1e-3)
        self.conv_spin.setValue(1e-5)
        conv_layout.addRow("Convergence (Δg/g):", self.conv_spin)

        self.max_iter_spin = QSpinBox()
        self.max_iter_spin.setRange(10, 10000)
        self.max_iter_spin.setValue(1000)
        conv_layout.addRow("Max Iterations:", self.max_iter_spin)

        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.1, 2.0)
        self.alpha_spin.setValue(1.0)
        conv_layout.addRow("Alpha (RY only):", self.alpha_spin)

        conv_group.setLayout(conv_layout)
        left_panel.addWidget(conv_group)

        # Группа управления
        control_group = QGroupBox("Control")
        control_layout = QVBoxLayout()

        self.btn_start = QPushButton("Start")
        self.btn_stop = QPushButton("Stop")
        self.btn_reset = QPushButton("Reset")

        self.btn_stop.setEnabled(False)

        control_layout.addWidget(self.btn_start)
        control_layout.addWidget(self.btn_stop)
        control_layout.addWidget(self.btn_reset)

        control_group.setLayout(control_layout)
        left_panel.addWidget(control_group)

        left_panel.addStretch()
        main_layout.addLayout(left_panel, 1)

        # Правая панель - графики и результаты
        right_panel = QVBoxLayout()

        self.tabs = QTabWidget()

        self.plotter = PlotterWidget()

        self.results_table = QTableWidget(0, 8)
        self.results_table.setHorizontalHeaderLabels([
            "T", "ρ", "Iter", "Δg/g", "g(max)", "h(max)", "Pressure", "Energy"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.tabs.addTab(self.plotter, "Plots")
        self.tabs.addTab(self.results_table, "Results")
        right_panel.addWidget(self.tabs)
        main_layout.addLayout(right_panel, 2)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.statusBar().addPermanentWidget(self.progress_bar)
        self.progress_bar.hide()

    def update_initial_plot(self):
        self.plotter.update_plot(
            self.solver.R_dist,
            self.solver.g,
            self.solver.h
        )

    def setup_connections(self):
        self.btn_start.clicked.connect(self.start_calculation)
        self.btn_stop.clicked.connect(self.stop_calculation)
        self.btn_reset.clicked.connect(self.reset_calculation)

    def start_calculation(self):
        if self.worker_thread and self.worker_thread.isRunning():
            return

        try:
            # Обновляем параметры решателя
            self.solver.equation_type = EquationType[self.eq_type_combo.currentText()]
            self.solver.potential_type = PotentialType[self.potential_combo.currentText()]
            self.solver.solution_method = list(SolutionMethod)[self.method_combo.currentIndex()]
            self.solver.closure = ClosureType[self.closure_combo.currentText()]

            self.solver.L = self.L_spin.value()
            self.solver.Nd = self.Nd_spin.value()
            self.solver.At = self.solver.L / self.solver.Nd

            self.solver.T0 = self.T0_spin.value()
            self.solver.Tk = self.Tk_spin.value()
            self.solver.dT = self.dT_spin.value()

            self.solver.rho0 = self.rho0_spin.value()
            self.solver.rhok = self.rhok_spin.value()
            self.solver.drho = self.drho_spin.value()

            self.solver.convergence_dg = self.conv_spin.value()
            self.solver.max_iterations = self.max_iter_spin.value()
            self.solver.alpha = self.alpha_spin.value()

            self.solver.Temperature = self.solver.T0
            self.solver.Density = self.solver.rho0
            self.solver._initialize_arrays()

            # Настраиваем worker и поток
            self.worker_thread = QThread()
            self.worker = Worker(self.solver)
            self.worker.moveToThread(self.worker_thread)

            # Подключаем сигналы
            self.worker_thread.started.connect(self.worker.run)
            self.worker.progress.connect(self.progress_bar.setValue)
            self.worker.result.connect(self.update_results)
            self.worker.error.connect(self.show_error)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.worker_thread.finished.connect(self.worker_thread.deleteLater)
            self.worker_thread.finished.connect(self.calculation_finished)

            # Обновляем UI
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.progress_bar.show()
            self.statusBar().showMessage("Calculation started...")

            # Запускаем поток
            self.worker_thread.start()

        except Exception as e:
            self.show_error(str(e))

    def update_results(self, data):
        # Обновляем графики
        self.plotter.update_plot(data['r'], data['g'], data['h'])

        # Обновляем таблицу результатов
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)

        items = [
            f"{self.solver.Temperature:.2f}",  # T
            f"{data['ρ']:.3f}",  # ρ
            str(data['iteration']),  # Итерации
            f"{np.max(np.abs(data['g'] - data['h'])):.2e}",  # Разница g(r) и h(r)
            f"{data['g_max']:.4f}",  # g(max)
            f"{data['h_max']:.4f}",  # h(max)
            f"{data.get('pressure', 0):.4f}",  # Давление
            f"{data.get('energy', 0):.4f}"  # Энергия
        ]

        for col, text in enumerate(items):
            self.results_table.setItem(row, col, QTableWidgetItem(text))

        self.results_table.scrollToBottom()

    def stop_calculation(self):
        if self.worker:
            self.worker.stop()
        self.statusBar().showMessage("Calculation stopped")

    def reset_calculation(self):
        self.stop_calculation()

        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        self.solver = LiquidSolver()
        self.plotter.update_plot(self.solver.R_dist, self.solver.g, self.solver.h)
        self.results_table.setRowCount(0)
        self.statusBar().showMessage("System reset")

    def calculation_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.progress_bar.hide()
        self.statusBar().showMessage("Calculation finished")

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)
        self.calculation_finished()

    def closeEvent(self, event):
        self.stop_calculation()
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        event.accept()