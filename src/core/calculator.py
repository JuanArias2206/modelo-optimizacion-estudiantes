"""
Calculador de scores normalizados para criterios
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class ScoreCalculator:
    """Calcula scores normalizados de criterios"""
    
    @staticmethod
    def norm_1_5(x):
        """Normaliza escala 1-5 a 0-1"""
        return (x - 1.0) / 4.0
    
    @staticmethod
    def norm_0_5(x):
        """Normaliza escala 0-5 a 0-1"""
        return x / 5.0
    
    @staticmethod
    def norm_pct(x):
        """Normaliza porcentaje 0-100 a 0-1"""
        return x / 100.0
    
    @staticmethod
    def minmax_cost(series):
        """Normaliza costo: menor es mejor"""
        mn, mx = series.min(), series.max()
        if pd.isna(mn) or pd.isna(mx) or abs(mx - mn) < 1e-9:
            return pd.Series([1.0] * len(series), index=series.index)
        return (mx - series) / (mx - mn)
    
    @staticmethod
    def minmax_benefit(series):
        """Normaliza beneficio: mayor es mejor"""
        mn, mx = series.min(), series.max()
        if pd.isna(mn) or pd.isna(mx) or abs(mx - mn) < 1e-9:
            return pd.Series([1.0] * len(series), index=series.index)
        return (series - mn) / (mx - mn)
    
    @classmethod
    def normalize_criteria(cls, base_df: pd.DataFrame) -> pd.DataFrame:
        """Normaliza todos los criterios en el dataframe"""
        S = base_df.set_index("ID_Institucion").copy()
        S.index = S.index.astype(str)
        
        # Beneficios
        if "Acceso_Transporte_Publico" in S:
            S["Acceso_Transporte_Publico_norm"] = cls.norm_1_5(
                pd.to_numeric(S["Acceso_Transporte_Publico"], errors="coerce")
            )
        
        if "MisionVisionProposito_AlineacionDocencia" in S:
            S["MisionVisionProposito_AlineacionDocencia_norm"] = cls.norm_1_5(
                pd.to_numeric(S["MisionVisionProposito_AlineacionDocencia"], errors="coerce")
            )
        
        if "Evalua_Estudiantes_Profesores" in S:
            S["Evalua_Estudiantes_Profesores_norm"] = cls.norm_0_5(
                pd.to_numeric(S["Evalua_Estudiantes_Profesores"], errors="coerce")
            )
        
        if "Vinculacion_Planta_Especialistas_%" in S:
            S["Vinculacion_Planta_Especialistas_%_norm"] = cls.norm_pct(
                pd.to_numeric(S["Vinculacion_Planta_Especialistas_%"], errors="coerce")
            )
        
        # UCI_UCIN: OR logic
        if "Servicios_UCI" in S and "Servicios_UCIN" in S:
            uci = pd.to_numeric(S["Servicios_UCI"], errors="coerce").fillna(0).astype(int)
            ucin = pd.to_numeric(S["Servicios_UCIN"], errors="coerce").fillna(0).astype(int)
            S["Servicios_UCI_UCIN_norm"] = np.maximum(uci, ucin).clip(0, 1).astype(float)
        
        # Servicios binarios
        for svc in ["Servicios_Pediatricos", "Servicios_Obstetricia"]:
            if svc in S:
                S[f"{svc}_norm"] = pd.to_numeric(S[svc], errors="coerce").fillna(0).clip(0, 1)
        
        # Costos (inversión)
        if "Nro_Universidades_Comparten" in S:
            S["Nro_Universidades_Comparten_norm"] = cls.minmax_cost(
                pd.to_numeric(S["Nro_Universidades_Comparten"], errors="coerce").fillna(0)
            )
        
        return S
