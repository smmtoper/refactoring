import numpy as np
from numba import njit
from .constants import *


@njit
def calculate_omega(g, density, f2, temperature, r, closure, alpha=1.0):
    """Расчет бридж-функции с обработкой крайних случаев"""
    if closure == 1:  # PY (Percus-Yevick)
        val = 1.0 + g
        # Добавляем проверку на малые значения
        if np.abs(val - 1.0) < 1e-10:
            return g - 0.5 * g**2  # Разложение Тейлора для log(1+g) при g->0
        return np.log(val) if val > 0 else -1e10

    elif closure == 2:  # HNC (Hypernetted Chain)
        return g

    elif closure == 3:  # MHNC (Modified HNC)
        return g * (1.0 + 0.5 * g)  # Пример модификации

    elif closure == 4:  # MS (Mean Spherical)
        val = 1.0 + 2.0 * g
        # Защита от отрицательных под корнем
        return -1.0 + np.sqrt(val) if val >= 0 else -1.0

    elif closure == 5:  # MS_MOD (Modified MS)
        val = 1.0 + 2.0 * (g - (density * f2 / temperature))
        # Учитываем температуру в f2
        return -1.0 + (density * f2 / temperature) + (np.sqrt(val) if val >= 0 else 0.0)

    elif closure == 6:  # RY (Roger-Young)
        exponent = alpha * (1.0 - r)
        # Защита от переполнения
        exp_term = np.exp(min(exponent, 100.0)) - 1.0
        term = 1.0 + exp_term * g
        return np.log(term) if term > 1e-10 else -1e10

    else:  # По умолчанию (должно вызывать ошибку в отладочном режиме)
        return 0.0
@njit
def calculate_h(r_dist, exp_u, density, temperature, closure_code):
    """Расчет h(r) с обработкой граничных условий"""
    h = np.zeros_like(r_dist)
    for i in range(len(r_dist)):
        if r_dist[i] <= 0:
            h[i] = -1.0  # h(0) = g(0) - 1 = 0 - 1 = -1
            continue

        delta = 1.0 / r_dist[i]
        delta6 = delta ** 6
        f2 = 4.0 * (delta6 ** 2 - delta6) if temperature > 1e-10 else 0

        omega = calculate_omega(
            g=0.0,
            density=density,
            f2=f2 / max(temperature, 1e-10),
            temperature=temperature,
            r=r_dist[i],
            closure=closure_code,
            alpha=1.0
        )
        h[i] = exp_u[i] * np.exp(omega) - 1.0
    return h


class LiquidSolver:
    def __init__(self):
        self.equation_type = EquationType.EQUILIBRIUM
        self.potential_type = PotentialType.LENNARD_JONES
        self.solution_method = SolutionMethod.NUMERICAL_INTEGRATION
        self.closure = ClosureType.PY

        # Параметры системы
        self.L = 10.0
        self.Nd = 500
        self.At = self.L / self.Nd

        # Диапазоны параметров
        self.T0 = 0.5
        self.Tk = 2.0
        self.dT = 0.1
        self.rho0 = 0.1
        self.rhok = 0.9
        self.drho = 0.05

        # Параметры сходимости
        self.convergence_dg = 1e-5
        self.max_iterations = 1000
        self.alpha = 1.0

        # Текущие состояния
        self.Temperature = self.T0
        self.Density = self.rho0

        # Инициализация массивов
        self._initialize_arrays()

    def _initialize_arrays(self):
        """Инициализация массивов с правильной размерностью"""
        self.R_dist = np.linspace(0, self.L, self.Nd)
        self.g = np.zeros(self.Nd)
        self.h = np.zeros(self.Nd)
        self.c = np.zeros(self.Nd)
        self.g_prev = np.zeros(self.Nd)
        self.F2 = np.zeros(self.Nd)

        # Инициализация потенциала с обработкой r=0
        with np.errstate(divide='ignore', invalid='ignore'):
            if self.potential_type == PotentialType.LENNARD_JONES:
                r_safe = np.where(self.R_dist > 0, self.R_dist, np.inf)
                self.ExpU = np.exp(-4 * ((1 / r_safe) ** 12 - (1 / r_safe) ** 6))
                delta = 1.0 / r_safe
                self.F2 = 4.0 * (delta ** 12 - delta ** 6)
            else:  # Hard Sphere
                self.ExpU = np.where(self.R_dist < 1, 0, 1)
                self.F2 = np.zeros(self.Nd)

        # Граничные условия
        self.ExpU[0] = 0
        self.g[0] = 0
        self.h[0] = -1
        self.g[1:] = 1.0
        self.h[1:] = self.ExpU[1:] - 1

    def make_iteration(self):
        self.g_prev = self.g.copy()

        # 1. Расчёт нового h(r) с релаксацией
        new_h = calculate_h(
            r_dist=self.R_dist,
            exp_u=self.ExpU,
            density=self.Density,
            temperature=self.Temperature,
            closure_code=1  # PY
        )
        self.h = 0.3 * new_h + 0.7 * self.h  # Сильная релаксация

        # 2. Интегральная поправка (исправленная версия)
        r_nonzero = np.where(self.R_dist > 0, self.R_dist, 1e-10)
        integral = np.cumsum(self.h[1:] * r_nonzero[1:] ** 2) * self.At
        correction = 2 * np.pi * self.Density * integral / r_nonzero[1:]

        # 3. Обновление g(r) с двойной релаксацией
        new_g = self.h[1:] + 1 - correction
        self.g[1:] = 0.2 * new_g + 0.8 * self.g_prev[1:]  # Очень сильная релаксация
        self.g[0] = 0  # Граничное условие

        # 4. Контроль сходимости
        dg = np.max(np.abs(self.g - self.g_prev)) / (np.mean(np.abs(self.g)) + 1e-10)
        return dg

    def get_total_correlation(self):
        """Возвращает h(r) с гарантией правильной размерности"""
        return self.h

    def calculate_pressure(self):
        """Давление через вириальное разложение"""
        integral = np.sum(self.R_dist[1:] ** 3 * self.h[1:]) * self.At
        return self.Density + (2 * np.pi * self.Density ** 2 / 3) * integral

    def calculate_energy(self):
        """Внутренняя энергия системы"""
        if self.potential_type == PotentialType.LENNARD_JONES:
            U_r = 4 * ((1 / np.where(self.R_dist[1:] > 0, self.R_dist[1:], np.inf)) ** 12 - \
                       (1 / np.where(self.R_dist[1:] > 0, self.R_dist[1:], np.inf)) ** 6)
        else:
            U_r = np.where(self.R_dist[1:] < 1, np.inf, 0)

        integral = np.sum(self.R_dist[1:] ** 2 * self.h[1:] * U_r) * self.At
        return 2 * np.pi * self.Density * integral