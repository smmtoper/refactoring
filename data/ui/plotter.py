from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


class Plotter(QWidget):
    def __init__(self):
        super().__init__()
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, 1)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.line_g, = self.ax1.plot([], [], 'b-', label='g(r)')
        self.line_h, = self.ax2.plot([], [], 'r-', label='h(r)')
        self.setup_axes()

    def setup_axes(self):
        """Настройка осей"""
        for ax in [self.ax1, self.ax2]:
            ax.grid(True)
            ax.set_xlabel('r')
        self.ax1.set_ylabel('g(r)')
        self.ax2.set_ylabel('h(r)')
        self.ax1.legend()
        self.ax2.legend()
        self.figure.tight_layout()

    def update_plot(self, r, g, h):
        """Обновление данных на графике"""
        self.line_g.set_data(r, g)
        self.line_h.set_data(r, h)

        # Автомасштабирование
        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()

        self.canvas.draw()