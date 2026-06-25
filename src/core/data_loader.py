"""
Cargador de datos desde plantilla Excel
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

_ROTACION_DEFAULT = "Práctica General"


class DataLoader:
    """Carga y valida datos desde plantilla Excel V4"""

    def __init__(self, excel_path: str, set_id: str = "SET001", semestre: str = "2026-1"):
        self.excel_path = excel_path
        self.set_id = set_id
        self.semestre = semestre

        self.oferta = None
        self.calidad = None
        self.cupos = None
        self.costos = None
        self.ponderaciones = None
        self.demanda = None
        self.rotaciones = None
        self.demanda_semestres = None

    @staticmethod
    def _to_float(series: pd.Series) -> pd.Series:
        """Convierte texto numérico a float soportando coma decimal."""
        if series is None:
            return pd.Series(dtype=float)
        return pd.to_numeric(
            series.astype(str).str.replace(",", ".", regex=False),
            errors="coerce",
        )

    def load_all(self) -> bool:
        """Carga todos los datos necesarios. Retorna True si está completo."""
        try:
            logger.info(f"Cargando datos desde: {self.excel_path}")

            self.oferta = pd.read_excel(self.excel_path, sheet_name="01_Oferta")
            self.calidad = pd.read_excel(self.excel_path, sheet_name="03_Calidad")
            self.cupos = pd.read_excel(self.excel_path, sheet_name="02_Oferta_x_Programa")
            self.costos = pd.read_excel(self.excel_path, sheet_name="04_Costo_del_Sitio")
            self.ponderaciones = pd.read_excel(self.excel_path, sheet_name="05_Ponderaciones", header=4)

            try:
                self.demanda = pd.read_excel(self.excel_path, sheet_name="Demanda Pregrado/Posgrado")
                logger.info(f"✓ Demanda cargada: {len(self.demanda)} grupos")
            except Exception:
                logger.warning("⚠ Demanda no encontrada - usando placeholder")
                self.demanda = None

            try:
                rot_raw = pd.read_excel(self.excel_path, sheet_name="06_Rotaciones")
                rot_raw = rot_raw.rename(columns={
                    "Semestre_Plan": "Semestre_plan",
                    "Cupo_Maximo": "Cupo",
                })

                if "Semestre_plan" in rot_raw.columns:
                    rot_raw["Semestre_plan"] = pd.to_numeric(rot_raw["Semestre_plan"], errors="coerce")
                    rot_raw = rot_raw.dropna(subset=["Semestre_plan"])
                    rot_raw["Semestre_plan"] = rot_raw["Semestre_plan"].astype(int)

                if "Cupo" in rot_raw.columns:
                    rot_raw["Cupo"] = pd.to_numeric(rot_raw["Cupo"], errors="coerce").fillna(0).astype(int)

                # Normalizar ID: NaN → "0" primero, luego excluimos los "0"
                if "ID_Institucion" in rot_raw.columns:
                    rot_raw["ID_Institucion"] = (
                        pd.to_numeric(rot_raw["ID_Institucion"], errors="coerce")
                        .fillna(0)
                        .astype(int)
                        .astype(str)
                    )

                # Excluir filas con ID vacío (quedó como "0")
                n_antes = len(rot_raw)
                rot_raw = rot_raw[rot_raw["ID_Institucion"] != "0"].copy()
                discardados_id = n_antes - len(rot_raw)
                if discardados_id > 0:
                    logger.warning(
                        f"⚠ 06_Rotaciones: {discardados_id} filas descartadas por ID_Institucion vacío"
                    )

                # Excluir filas con Asignatura vacía
                if "Asignatura" in rot_raw.columns:
                    n_antes = len(rot_raw)
                    rot_raw = rot_raw[rot_raw["Asignatura"].notna() & (rot_raw["Asignatura"].astype(str).str.strip() != "")]
                    d = n_antes - len(rot_raw)
                    if d > 0:
                        logger.warning(f"⚠ 06_Rotaciones: {d} filas descartadas por Asignatura vacía")

                # Excluir filas con Cupo ≤ 0
                if "Cupo" in rot_raw.columns:
                    n_antes = len(rot_raw)
                    rot_raw = rot_raw[rot_raw["Cupo"] > 0]
                    d = n_antes - len(rot_raw)
                    if d > 0:
                        logger.warning(f"⚠ 06_Rotaciones: {d} filas descartadas por Cupo ≤ 0")

                # Rellenar Rotacion NaN con valor por defecto
                if "Rotacion" in rot_raw.columns:
                    n_nan_rot = rot_raw["Rotacion"].isna().sum()
                    if n_nan_rot > 0:
                        rot_raw["Rotacion"] = rot_raw["Rotacion"].fillna(_ROTACION_DEFAULT)
                        logger.info(
                            f"ℹ 06_Rotaciones: {n_nan_rot} rotaciones vacías rellenadas con '{_ROTACION_DEFAULT}'"
                        )

                self.rotaciones = rot_raw.reset_index(drop=True)
                logger.info(f"✓ 06_Rotaciones: {len(self.rotaciones)} registros válidos")

            except Exception as exc:
                logger.warning(f"⚠ 06_Rotaciones no encontrada: {exc}")
                self.rotaciones = None

            try:
                self.demanda_semestres = pd.read_excel(
                    self.excel_path, sheet_name="07_Demanda_Semestres"
                )
                if "Semestre_Plan" in self.demanda_semestres.columns:
                    self.demanda_semestres["Semestre_Plan"] = pd.to_numeric(
                        self.demanda_semestres["Semestre_Plan"], errors="coerce"
                    ).astype(int)
                logger.info(
                    f"✓ 07_Demanda_Semestres: {len(self.demanda_semestres)} semestres"
                )
            except Exception:
                logger.warning("⚠ 07_Demanda_Semestres no encontrada")
                self.demanda_semestres = None

            logger.info(f"✓ 01_Oferta: {self.oferta.shape[0]} instituciones")
            logger.info(f"✓ 03_Calidad: {self.calidad.shape[0]} registros")
            logger.info(f"✓ 02_Oferta_x_Programa: {self.cupos.shape[0]} cupos")
            logger.info(f"✓ 04_Costo_del_Sitio: {self.costos.shape[0]} registros")
            logger.info(f"✓ 05_Ponderaciones: {self.ponderaciones.shape[0]} criterios")

            return True

        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            raise

    # ------------------------------------------------------------------
    # Validación de pesos
    # ------------------------------------------------------------------
    def validate_pesas(self, set_id: Optional[str] = None) -> float:
        """Valida que los pesos sumen 1.0. Retorna la suma. set_id opcional para multi-set."""
        sid = set_id if set_id is not None else self.set_id
        pond = self.ponderaciones[
            self.ponderaciones["Set_ID"].astype(str).str.strip() == sid
        ].copy()
        pond = pond[pond["Activo (0/1)"].fillna(0).astype(int) == 1].copy()
        pond = pond[
            pond["Semestre_Vigencia (AAAA-S)"].astype(str).str.strip() == self.semestre
        ].copy()

        pond["Peso (0-1)"] = self._to_float(pond["Peso (0-1)"]).fillna(0.0)
        suma = pond["Peso (0-1)"].sum()

        logger.info(f"Suma de pesos activos ({sid}): {suma:.4f}")

        if abs(suma - 1.0) > 1e-6:
            raise ValueError(f"Pesos del set '{sid}' no suman 1.0: {suma:.4f}")

        return suma

    def get_ponderaciones_dict(self, set_id: Optional[str] = None) -> Tuple[Dict, Dict]:
        """Retorna (pesos, tipos) de criterios para set_id y semestre. set_id opcional."""
        sid = set_id if set_id is not None else self.set_id
        pond = self.ponderaciones[
            self.ponderaciones["Set_ID"].astype(str).str.strip() == sid
        ].copy()
        pond = pond[pond["Activo (0/1)"].fillna(0).astype(int) == 1].copy()
        pond = pond[
            pond["Semestre_Vigencia (AAAA-S)"].astype(str).str.strip() == self.semestre
        ].copy()

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

    def load_rotaciones(self, rotaciones_df: pd.DataFrame) -> None:
        """Carga datos de rotaciones desde DataFrame parseado del Mapa de Práctica."""
        self.rotaciones = rotaciones_df.copy()
        self.rotaciones["ID_Institucion"] = self.rotaciones["ID_Institucion"].astype(str)
        logger.info(
            f"Rotaciones cargadas: {len(self.rotaciones)} registros, "
            f"semestres {sorted(self.rotaciones['Semestre_plan'].unique())}"
        )

    # ------------------------------------------------------------------
    # Métodos de consulta de rotaciones
    # ------------------------------------------------------------------

    def get_asignaturas_por_semestre(self, semestre_plan: int) -> List[str]:
        """Retorna lista de asignaturas únicas y ordenadas para un semestre plan."""
        if self.rotaciones is None or self.rotaciones.empty:
            return []
        df = self.rotaciones[self.rotaciones["Semestre_plan"] == semestre_plan].copy()
        asigs = (
            df["Asignatura"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", np.nan)
            .dropna()
            .unique()
            .tolist()
        )
        return sorted(asigs)

    def get_demanda_semestre(self, semestre_plan: int) -> Optional[Dict]:
        """Retorna {'demanda': int, 'min_group': int, 'max_group': int, 'techo_max': int} desde 07_Demanda_Semestres."""
        if self.demanda_semestres is None or self.demanda_semestres.empty:
            return None
        row = self.demanda_semestres[
            self.demanda_semestres["Semestre_Plan"] == semestre_plan
        ]
        if row.empty:
            return None
        r = row.iloc[0]
        return {
            "demanda": int(r.get("Demanda_Estudiantes", 0) or 0),
            "min_group": int(r.get("Grupo_Min", 4) or 4),
            "max_group": int(r.get("Grupo_Max", 7) or 7),
            "techo_max": int(r.get("Techo_Max", 75) or 75),
        }

    def get_rotaciones_dict(
        self,
        semestre_plan: int,
        asignaturas_seleccionadas: Optional[List[str]] = None,
    ) -> dict:
        """Retorna {(asignatura, rotacion, id_institucion): cupo} para un semestre.

        Si asignaturas_seleccionadas no es None, filtra solo esas asignaturas.
        Excluye claves con asignatura, rotacion o id_institucion vacíos.
        """
        df = self.rotaciones[self.rotaciones["Semestre_plan"] == semestre_plan].copy()

        if asignaturas_seleccionadas:
            df = df[df["Asignatura"].isin(asignaturas_seleccionadas)]

        cap = {}
        discarded = 0
        for _, r in df.iterrows():
            asig = str(r.get("Asignatura", "")).strip()
            rot = str(r.get("Rotacion", "")).strip()
            id_inst = str(r.get("ID_Institucion", "")).strip()
            cupo = int(r.get("Cupo", 0) or 0)

            if not asig or not rot or not id_inst or id_inst == "0" or cupo <= 0:
                discarded += 1
                continue
            cap[(asig, rot, id_inst)] = cupo

        if discarded:
            logger.warning(
                f"get_rotaciones_dict: {discarded} filas descartadas por datos incompletos"
            )
        return cap

    def get_asignaturas_rotaciones(
        self,
        semestre_plan: int,
        asignaturas_seleccionadas: Optional[List[str]] = None,
    ) -> dict:
        """Retorna {asignatura: [rotaciones]} para un semestre.

        Si asignaturas_seleccionadas no es None, filtra solo esas asignaturas.
        Solo incluye rotaciones con al menos una IPS válida.
        """
        df = self.rotaciones[self.rotaciones["Semestre_plan"] == semestre_plan].copy()

        if asignaturas_seleccionadas:
            df = df[df["Asignatura"].isin(asignaturas_seleccionadas)]

        # Solo filas con ID e IPS válidos
        df = df[
            df["ID_Institucion"].notna()
            & (df["ID_Institucion"].astype(str).str.strip() != "")
            & (df["ID_Institucion"].astype(str).str.strip() != "0")
        ]

        result = {}
        for asig in df["Asignatura"].unique():
            rots = df[df["Asignatura"] == asig]["Rotacion"].dropna().unique().tolist()
            rots = [r for r in rots if str(r).strip() and str(r).strip() != "nan"]
            if rots:
                result[asig] = rots
        return result

    def get_ips_for_rotacion(
        self, semestre_plan: int, asignatura: str, rotacion: str
    ) -> list:
        """Retorna lista de (id_institucion, cupo) para una rotación específica."""
        df = self.rotaciones[
            (self.rotaciones["Semestre_plan"] == semestre_plan)
            & (self.rotaciones["Asignatura"] == asignatura)
            & (self.rotaciones["Rotacion"] == rotacion)
        ].copy()
        return [(str(r["ID_Institucion"]), int(r["Cupo"])) for _, r in df.iterrows()]
