import numpy as np
import json
from pathlib import Path

def load_bridg(density: float, data_dir="data/bridg_func") -> np.ndarray:
    """Загрузка бридж-функций для MHNC"""
    try:
        density_int = int(round(density * 1000))
        filename = Path(data_dir) / f"{density_int:04d}.txt"
        return np.loadtxt(filename)
    except (FileNotFoundError, ValueError):
        return np.zeros(10000)

def save_results(results: dict, filename: str):
    """Сохранение результатов в JSON"""
    with open(filename, 'w') as f:
        json.dump(results, f, indent=4)

def load_config(filename: str) -> dict:
    """Загрузка конфигурации из файла"""
    with open(filename) as f:
        return json.load(f)