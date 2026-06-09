"""
Módulo principal: Corazón del modelo de optimización
"""

from .data_loader import DataLoader
from .optimizer import Optimizer, GroupOptimizer, TemporalGroupOptimizer
from .calculator import ScoreCalculator

__all__ = ["DataLoader", "Optimizer", "GroupOptimizer", "TemporalGroupOptimizer", "ScoreCalculator"]
