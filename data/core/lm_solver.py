import numpy as np
from scipy.fftpack import dst, idst
from numba import njit
from .constants import ClosureType


class LMSolver:
    def __init__(self, solver):
        self.solver = solver
        self.Na = 48  # Число гармоник
        self.initialize_arrays()

    def initialize_arrays(self):
        N = self.solver.N
        self.FM = np.zeros(N)
        self.Ri = np.arange(1, N + 1) * self.solver.d_R
        self.Gi0 = np.zeros(N)
        self.NewGi0 = np.zeros(N)
        self.Gj0 = np.zeros(N)
        self.Omega = np.zeros(N)
        self.Ci0 = np.zeros(N)
        self.Cj0 = np.zeros(N)
        self.gCj0 = np.zeros(N)
        self.gnt = np.zeros(N)
        self.dC = np.zeros(N)
        self.dgt = np.zeros(N)
        self.P = np.zeros(2 * self.Na + 1)
        self.Pjj = np.zeros(2 * self.Na + 1)
        self.dif = np.zeros(self.Na)

    def fourier_transform(self, arr):
        """Дискретное синус-преобразование"""
        return dst(arr, type=2)

    def inverse_fourier_transform(self, arr):
        """Обратное дискретное синус-преобразование"""
        return idst(arr, type=2) / (2 * self.solver.N)

    def recount_fm(self):
        """Пересчет массива FM для текущей температуры"""
        if self.solver.potential_type == 'LJ':
            for i in range(self.solver.N):
                delta = 1 / self.Ri[i]
                delta6 = delta ** 6
                Fi = 4 * (delta6 ** 2 - delta6) / self.solver.Temperature
                self.FM[i] = np.exp(-Fi) - 1 if Fi < 60 else -1
        else:  # HS потенциал
            self.FM = np.where(self.Ri < 1, -1, 0)

    def solve(self):
        """Основная процедура решения методом LM"""
        self.recount_fm()

        # Прямое Фурье-преобразование
        self.Gj0 = self.fourier_transform(self.Gi0 / self.Ri) * 4 * np.pi * self.solver.d_R

        # Основные итерации
        for direct_iter in range(300):
            # Вычисление Omega(i)
            self.calculate_omega()

            # Вычисление Ci0
            self.Ci0 = ((self.FM + 1) * np.exp(self.Omega) - self.Gi0 / self.Ri - 1) * self.Ri

            # Фурье-преобразование Ci0
            self.Cj0 = self.fourier_transform(self.Ci0) * 4 * np.pi * self.solver.d_R

            # Вычисление gnt(j)
            tj = np.arange(1, self.solver.N + 1) * np.pi / (self.solver.N * self.solver.d_R)
            self.gnt = self.solver.Density * self.Cj0 ** 2 / (tj - self.solver.Density * self.Cj0)

            # Итерации Ньютона
            for newton_iter in range(100):
                self.newton_iteration()
                if self.check_convergence():
                    break

            # Обновление Gj0
            self.Gj0[:self.Na] += self.dgt
            self.Gj0[self.Na:] = self.gnt[self.Na:]

            # Обратное преобразование
            self.NewGi0 = self.inverse_fourier_transform(self.Gj0) * np.pi / (2 * np.pi ** 2)

            # Проверка сходимости
            if self.check_convergence():
                break

        # Обновление результатов в основном решателе
        self.solver.new_g = self.NewGi0 / self.Ri
        self.solver.g = self.Gi0 / self.Ri
        self.Gi0 = self.NewGi0.copy()

    # ... (остальные методы класса)