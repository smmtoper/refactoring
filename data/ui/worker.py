from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
from numba import njit
import time


class Worker(QObject):
    progress = pyqtSignal(int)
    result = pyqtSignal(dict)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, solver):
        super().__init__()
        self.solver = solver
        self._is_running = False

    def run(self):
        try:
            self._is_running = True

            rho0 = self.solver.rho0
            rhok = self.solver.rhok
            drho = self.solver.drho

            for rho in np.arange(rho0, rhok + drho, drho):
                if not self._is_running:
                    break

                self.solver.Density = rho
                self.solver._initialize_arrays()

                for iteration in range(self.solver.max_iterations):
                    if not self._is_running:
                        break

                    self.solver.make_iteration()
                    dg = np.max(np.abs(self.solver.g - self.solver.g_prev)) / np.mean(np.abs(self.solver.g))

                    progress = int((rho - rho0) / (rhok - rho0) * 100)
                    self.progress.emit(progress)

                    if dg < self.solver.convergence_dg:
                        break

                # Добавляем расчет h(r) = g(r) - 1
                h_r = self.solver.g - 1

                self.result.emit({
                    'r': self.solver.R_dist,
                    'g': self.solver.g,
                    'h': h_r,  # Теперь передаем h(r)
                    'ρ': rho,
                    'iteration': iteration + 1,
                    'h_max': np.max(h_r),  # Максимальное значение h(r)
                    'g_max': np.max(self.solver.g)  # Максимальное значение g(r)
                })

        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()