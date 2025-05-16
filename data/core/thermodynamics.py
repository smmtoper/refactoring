import numpy as np
from typing import Dict, Any
from .constants import KB, NA


def calculate_all_thermodynamics(solver) -> Dict[str, Any]:
    """Расчет всех термодинамических параметров"""
    # Расчет давления
    integral_p = np.sum(solver.h * solver.R_dist ** 2 * solver.d_R)
    pressure = solver.Density * solver.Temperature * (1 + 2 * np.pi * solver.Density * integral_p)

    # Расчет энергии
    if solver.potential_type == 'LJ':
        U = np.sum(solver.F2 * solver.Temperature * (solver.h + 1) * solver.R_dist ** 2 * solver.d_R)
        energy = 2 * np.pi * solver.Density * U
    else:
        energy = 0.0

    # Расчет химического потенциала
    him_pot = 0.0
    for i in range(solver.N):
        omega = solver.w[i] - (solver.Density * solver.F2[i] / solver.Temperature)
        if solver.closure == 'MS_mod':
            mbr1 = -(1 / 6) * omega ** 2
        c2 = solver.h[i] - solver.w[i] - 0.5 * solver.h[i] * (solver.w[i] + mbr1)
        him_pot += c2 * solver.R_dist[i] ** 2 * solver.d_R

    him_pot = (np.log(solver.Density) - him_pot * 4 * np.pi * solver.Density) * solver.Temperature

    return {
        'pressure': pressure,
        'energy': energy,
        'chemical_potential': him_pot,
        'temperature': solver.Temperature,
        'density': solver.Density
    }


# Добавляем алиас для обратной совместимости
calculate_thermodynamics = calculate_all_thermodynamics