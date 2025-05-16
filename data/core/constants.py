from enum import Enum, auto

class EquationType(Enum):
    EQUILIBRIUM = auto()
    NON_EQUILIBRIUM = auto()

class PotentialType(Enum):
    LENNARD_JONES = "LJ"
    HARD_SPHERE = "HS"

class SolutionMethod(Enum):
    NUMERICAL_INTEGRATION = "Численное интегрирование"
    FOURIER_TRANSFORM = "Фурье-преобразование"
    LM_METHOD = "LM-метод"

class ClosureType(Enum):
    PY = auto()
    HNC = auto()
    MHNC = auto()
    MS = auto()
    MS_MOD = auto()
    RY = auto()

KB = 1.380649e-23
NA = 6.02214076e23