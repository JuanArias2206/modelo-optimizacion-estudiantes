"""
Cargador de datos desde plantilla Excel
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Carga y valida datos desde plantilla Excel V3"""
    
    def __init__(self, excel_path: str, set_id: str = "SET001", semestre: str = "2026-1"):
        self.excel_path = excel_path
        self.set_id = set_id
        self.semestre = semestre
        
        # Cargar datos
        self.oferta = None
        self.calidad = None
        self.cupos = None
        self.costos = None
        self.ponderaciones = None
        self.demanda = None

    @staticmethod
    def _to_float(series: pd.Series) -> pd.Series:
        """Convierte texto numérico a float soportando coma decimal."""
        if series is None:
            return pd.Series(dtype=float)
        return pd.to_numeric(
            series.astype(str).str.replace(",", ".", regex=False),
            errors="coerce"
        )
        
    def load_all(self) -> bool:
        """Carga todos los datos necesarios. Retorna True si está completo."""
        try:
            logger.info(f"Cargando datos desde: {self.excel_path}")
            
            # Cargar hojas
            self.oferta = pd.read_excel(self.excel_path, sheet_name="01_Oferta")
            self.calidad = pd.read_excel(self.excel_path, sheet_name="03_Calidad")
            self.cupos = pd.read_excel(self.excel_path, sheet_name="02_Oferta_x_Programa")
            self.costos = pd.read_excel(self.excel_path, sheet_name="04_Costo_del_Sitio")
            self.ponderaciones = pd.read_excel(self.excel_path, sheet_name="05_Ponderaciones", header=4)
            
            # Intentar cargar demanda (opcional)
            try:
                self.demanda = pd.read_excel(self.excel_path, sheet_name="Demanda Pregrado/Posgrado")
                logger.info(f"✓ Demanda cargada: {len(self.demanda)} grupos")
            except:
                logger.warning("⚠ Demanda no encontrada - usando placeholder")
                self.demanda = None
            
            logger.info(f"✓ 01_Oferta: {self.oferta.shape[0]} instituciones")
            logger.info(f"✓ 03_Calidad: {self.calidad.shape[0]} registros")
            logger.info(f"✓ 02_Oferta_x_Programa: {self.cupos.shape[0]} cupos")
            logger.info(f"✓ 04_Costo_del_Sitio: {self.costos.shape[0]} registros")
            logger.info(f"✓ 05_Ponderaciones: {self.ponderaciones.shape[0]} criterios")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            raise
    
    def validate_pesas(self) -> float:
        """Valida que los pesos sumen 1.0. Retorna la suma."""
        pond = self.ponderaciones[
            self.ponderaciones["Set_ID"].astype(str).str.strip() == self.set_id
        ].copy()
        pond = pond[pond["Activo (0/1)"].fillna(0).astype(int) == 1].copy()
        pond = pond[pond["Semestre_Vigencia (AAAA-S)"].astype(str).str.strip() == self.semestre].copy()
        
        pond["Peso (0-1)"] = self._to_float(pond["Peso (0-1)"]).fillna(0.0)
        suma = pond["Peso (0-1)"].sum()
        
        logger.info(f"Suma de pesos activos: {suma:.4f}")
        
        if abs(suma - 1.0) > 1e-6:
            raise ValueError(f"Pesos no suman 1.0: {suma:.4f}")
        
        return suma
    
    def get_ponderaciones_dict(self) -> Tuple[Dict, Dict]:
        """Retorna (pesos, tipos) de criterios para set_id y semestre."""
        pond = self.ponderaciones[
            self.ponderaciones["Set_ID"].astype(str).str.strip() == self.set_id
        ].copy()
        pond = pond[pond["Activo (0/1)"].fillna(0).astype(int) == 1].copy()
        pond = pond[pond["Semestre_Vigencia (AAAA-S)"].astype(str).str.strip() == self.semestre].copy()
        
        pond["Peso (0-1)"] = self._to_float(pond["Peso (0-1)"]).fillna(0.0)
        
        weights = dict(zip(pond["Criterio_Codigo"], pond["Peso (0-1)"]))
        crit_type = dict(zip(pond["Criterio_Codigo"], pond["Tipo (Beneficio/Costo)"]))
        
        return weights, crit_type

    def get_available_set_ids(self) -> list:
        """Retorna Set_ID disponibles en la hoja de ponderaciones."""
        if self.ponderaciones is None or "Set_ID" not in self.ponderaciones.columns:
            return []
        vals = (
            self.ponderaciones["Set_ID"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )
        return sorted([v for v in vals if v])

    def get_available_semestres(self) -> list:
        """Retorna semestres disponibles en ponderaciones."""
        if self.ponderaciones is None or "Semestre_Vigencia (AAAA-S)" not in self.ponderaciones.columns:
            return []
        vals = (
            self.ponderaciones["Semestre_Vigencia (AAAA-S)"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
            .tolist()
        )
        return sorted([v for v in vals if v])
    
    def has_cupos_data(self) -> bool:
        """Verifica si hay datos reales en cupos."""
        self.cupos["Cupo_Estimado_Semestral"] = pd.to_numeric(
            self.cupos["Cupo_Estimado_Semestral"], errors="coerce"
        ).fillna(0).astype(int)
        return (self.cupos["Cupo_Estimado_Semestral"] > 0).sum() > 0
    
    def has_costos_data(self) -> bool:
        """Verifica si hay datos reales en costos."""
        costos_copy = self.costos.copy()
        costos_copy["pct_contra"] = pd.to_numeric(
            costos_copy["%_Contraprestacion_Matricula (0-100)"], errors="coerce"
        )
        return costos_copy["pct_contra"].notna().sum() > 0
