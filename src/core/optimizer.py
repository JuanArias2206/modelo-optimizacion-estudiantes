"""
Modelo de optimización MILP para asignación de estudiantes
"""

import pandas as pd
import numpy as np
from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpInteger, PULP_CBC_CMD
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class Optimizer:
    """Ejecuta optimización MILP de asignación"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.model = None
        self.variables = {}
        self.results = None
    
    def optimize(
        self,
        V: Dict,
        demand_dict: Dict,
        cap_dict: Dict,
        instituciones: List[str],
        groups: List[Tuple],
        semestre: str
    ) -> pd.DataFrame:
        """
        Resuelve el problema de optimización.
        
        Parameters:
        -----------
        V : Dict[(j,g)] -> score
        demand_dict : Dict[(p,n,t,s)] -> cantidad
        cap_dict : Dict[(j,p,n,s)] -> cupo
        instituciones : Lista de IDs
        groups : Lista de tuplas (p,n,t,s)
        """
        
        logger.info("Creando modelo MILP...")
        
        self.model = LpProblem("Asignacion_Practicas", LpMaximize)
        
        # Variables de decisión
        for (j, g), score in V.items():
            self.variables[(j, g)] = LpVariable(
                f"x_{j}_{g[0]}_{g[1]}_{g[2]}_{g[3]}",
                lowBound=0,
                cat=LpInteger
            )
        
        logger.info(f"Variables creadas: {len(self.variables)}")
        
        # Función objetivo: maximizar score ponderado
        self.model += lpSum(V[(j, g)] * self.variables[(j, g)] for (j, g) in self.variables)
        
        # Restricción 1: Cumplir demanda
        for g in groups:
            relevant_vars = [self.variables[(j, g)] for j in instituciones if (j, g) in self.variables]
            if relevant_vars:
                self.model += lpSum(relevant_vars) == demand_dict[g], f"Demanda_{g}"
        
        # Restricción 2: Capacidad por (j,p,n,s)
        for (j, p, n, s), cap in cap_dict.items():
            if s != semestre:
                continue
            
            relevant_groups = [g for g in groups if g[0] == p and g[1] == n and g[3] == s]
            relevant_vars = [self.variables[(j, g)] for g in relevant_groups if (j, g) in self.variables]
            
            if relevant_vars:
                self.model += lpSum(relevant_vars) <= cap, f"Cap_{j}_{p}_{n}_{s}"
        
        # Resolver
        logger.info("Resolviendo modelo...")
        solver = PULP_CBC_CMD(msg=self.verbose)
        status = self.model.solve(solver)
        
        logger.info(f"Estado: {status}")
        
        # Extraer resultados
        results = []
        for (j, g), var in self.variables.items():
            if var.value() and var.value() > 0:
                p, n, t, s = g
                results.append({
                    "ID_Institucion": j,
                    "Programa": p,
                    "Tipo_Estudiante": n,
                    "Tipo_Practica": t,
                    "Semestre": s,
                    "Asignados": int(var.value()),
                    "Score_unitario": V[(j, g)]
                })
        
        self.results = pd.DataFrame(results).sort_values(
            ["Programa", "Tipo_Estudiante", "Tipo_Practica", "ID_Institucion"]
        ) if results else pd.DataFrame()
        
        return self.results
    
    def get_objective_value(self) -> float:
        """Retorna el valor óptimo de la función objetivo"""
        return self.model.objective.value() if self.model else None


class GroupOptimizer:
    """Optimización con grupos de tamaño controlado por semestre."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.model = None
        self.results = None

    def optimize(
        self,
        scores: dict,
        cap_dict: dict,
        asignaturas_rotaciones: dict,
        n_estudiantes: int,
        min_group: int,
        max_group: int,
        time_limit: int = 120,
    ) -> pd.DataFrame:
        import math

        g_max = math.ceil(n_estudiantes / min_group)

        ar_pairs = []
        for asig, rots in asignaturas_rotaciones.items():
            for rot in rots:
                ar_pairs.append((asig, rot))

        ips_by_ar = {}
        for (a, r, j) in cap_dict:
            key = (a, r)
            if key not in ips_by_ar:
                ips_by_ar[key] = []
            ips_by_ar[key].append(j)

        self.model = LpProblem("Asignacion_Grupos", LpMaximize)

        t = {}
        z = {}
        for g in range(g_max):
            t[g] = LpVariable(f"t_{g}", lowBound=0, cat=LpInteger)
            z[g] = LpVariable(f"z_{g}", cat="Binary")

        x = {}
        y = {}
        for g in range(g_max):
            for (a, r) in ar_pairs:
                valid_ips = ips_by_ar.get((a, r), [])
                for j in valid_ips:
                    x[(g, a, r, j)] = LpVariable(f"x_{g}_{a}_{r}_{j}", cat="Binary")
                    y[(g, a, r, j)] = LpVariable(f"y_{g}_{a}_{r}_{j}", lowBound=0, cat=LpInteger)

        self.model += lpSum(
            scores.get(j, 0.0) * y[(g, a, r, j)]
            for g in range(g_max)
            for (a, r) in ar_pairs
            for j in ips_by_ar.get((a, r), [])
            if (g, a, r, j) in y
        )

        self.model += lpSum(t[g] for g in range(g_max)) == n_estudiantes, "Total_estudiantes"

        for g in range(g_max):
            self.model += t[g] >= min_group * z[g], f"Min_size_{g}"
            self.model += t[g] <= max_group * z[g], f"Max_size_{g}"

        for g in range(g_max):
            for (a, r) in ar_pairs:
                valid_ips = ips_by_ar.get((a, r), [])
                relevant_x = [x[(g, a, r, j)] for j in valid_ips if (g, a, r, j) in x]
                if relevant_x:
                    self.model += lpSum(relevant_x) == z[g], f"One_IPS_{g}_{a}_{r}"

        for g in range(g_max):
            for (a, r) in ar_pairs:
                valid_ips = ips_by_ar.get((a, r), [])
                for j in valid_ips:
                    if (g, a, r, j) not in y:
                        continue
                    self.model += (
                        y[(g, a, r, j)] <= max_group * x[(g, a, r, j)],
                        f"BigM_upper_{g}_{a}_{r}_{j}",
                    )
                    self.model += (
                        y[(g, a, r, j)] >= t[g] - max_group * (1 - x[(g, a, r, j)]),
                        f"BigM_lower_{g}_{a}_{r}_{j}",
                    )
                    self.model += (
                        y[(g, a, r, j)] <= t[g],
                        f"Y_leq_t_{g}_{a}_{r}_{j}",
                    )

        for (a, r) in ar_pairs:
            valid_ips = ips_by_ar.get((a, r), [])
            for j in valid_ips:
                relevant_y = [
                    y[(g, a, r, j)]
                    for g in range(g_max)
                    if (g, a, r, j) in y
                ]
                if relevant_y:
                    cap = cap_dict.get((a, r, j), 0)
                    self.model += (
                        lpSum(relevant_y) <= cap,
                        f"Cap_{a}_{r}_{j}",
                    )

        solver = PULP_CBC_CMD(msg=self.verbose, timeLimit=time_limit)
        status = self.model.solve(solver)
        logger.info(f"GroupOptimizer status: {status}")

        results = []
        for g in range(g_max):
            if z[g].value() and z[g].value() > 0.5:
                group_size = int(round(t[g].value()))
                for (a, r) in ar_pairs:
                    valid_ips = ips_by_ar.get((a, r), [])
                    for j in valid_ips:
                        if (g, a, r, j) in y and y[(g, a, r, j)].value() and y[(g, a, r, j)].value() > 0:
                            results.append({
                                "Grupo": g + 1,
                                "Tamano_Grupo": group_size,
                                "Asignatura": a,
                                "Rotacion": r,
                                "ID_Institucion": j,
                                "Estudiantes": int(round(y[(g, a, r, j)].value())),
                                "Score_IPS": scores.get(j, 0.0),
                            })

        self.results = pd.DataFrame(results)
        if not self.results.empty:
            self.results = self.results.sort_values(
                ["Grupo", "Asignatura", "Rotacion"]
            ).reset_index(drop=True)

        return self.results

    def get_objective_value(self) -> float:
        return self.model.objective.value() if self.model else None

    def get_groups_summary(self) -> pd.DataFrame:
        if self.results is None or self.results.empty:
            return pd.DataFrame()
        return (
            self.results.groupby("Grupo")["Tamano_Grupo"]
            .first()
            .reset_index()
            .rename(columns={"Tamano_Grupo": "Estudiantes"})
        )


class TemporalGroupOptimizer:
    """Optimización con grupos y calendario: asigna grupos a IPS por rotación y período."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.model = None
        self.results = None
        self.calendario_info = None

    def optimize(
        self,
        scores: dict,
        cap_dict: dict,
        asignaturas_rotaciones: dict,
        n_estudiantes: int,
        min_group: int,
        max_group: int,
        calendario_asignatura: pd.DataFrame,
        time_limit: int = 180,
    ) -> pd.DataFrame:
        """
        calendario_asignatura: DataFrame con columnas Asignatura, Rotacion, Periodo_Num
        para una asignatura específica. Define en qué períodos está disponible cada rotación.
        """
        import math

        g_max = math.ceil(n_estudiantes / min_group)

        ar_pairs = []
        for asig, rots in asignaturas_rotaciones.items():
            for rot in rots:
                ar_pairs.append((asig, rot))

        if calendario_asignatura is None or calendario_asignatura.empty:
            logger.warning("Sin calendario: usando 1 período por defecto")
            periodos_asignatura = {ar[1]: [1] for ar in ar_pairs}
        else:
            periodos_asignatura = {}
            for rot in [r for (a, r) in ar_pairs]:
                perts = calendario_asignatura[
                    calendario_asignatura["Rotacion"] == rot
                ]["Periodo_Num"].unique().tolist()
                periodos_asignatura[rot] = sorted(perts) if len(perts) > 0 else [1]

        self.calendario_info = periodos_asignatura
        logger.info(f"Calendario por rotación: {periodos_asignatura}")

        ips_by_ar = {}
        for (a, r, j) in cap_dict:
            key = (a, r)
            if key not in ips_by_ar:
                ips_by_ar[key] = []
            ips_by_ar[key].append(j)

        all_periods = set()
        for perts in periodos_asignatura.values():
            all_periods.update(perts)
        all_periods = sorted(all_periods)

        self.model = LpProblem("Asignacion_Grupos_Temporal", LpMaximize)

        t = {}
        z = {}
        for g in range(g_max):
            t[g] = LpVariable(f"t_{g}", lowBound=0, cat=LpInteger)
            z[g] = LpVariable(f"z_{g}", cat="Binary")

        x = {}
        y = {}
        for g in range(g_max):
            for (a, r) in ar_pairs:
                for per in periodos_asignatura.get(r, [1]):
                    valid_ips = ips_by_ar.get((a, r), [])
                    for j in valid_ips:
                        x[(g, a, r, per, j)] = LpVariable(
                            f"x_{g}_{a}_{r}_{per}_{j}", cat="Binary"
                        )
                        y[(g, a, r, per, j)] = LpVariable(
                            f"y_{g}_{a}_{r}_{per}_{j}", lowBound=0, cat=LpInteger
                        )

        self.model += lpSum(
            scores.get(j, 0.0) * y[(g, a, r, per, j)]
            for g in range(g_max)
            for (a, r) in ar_pairs
            for per in periodos_asignatura.get(r, [1])
            for j in ips_by_ar.get((a, r), [])
            if (g, a, r, per, j) in y
        )

        self.model += lpSum(t[g] for g in range(g_max)) == n_estudiantes, "Total_estudiantes"

        for g in range(g_max):
            self.model += t[g] >= min_group * z[g], f"Min_size_{g}"
            self.model += t[g] <= max_group * z[g], f"Max_size_{g}"

        for g in range(g_max):
            for (a, r) in ar_pairs:
                for per in periodos_asignatura.get(r, [1]):
                    valid_ips = ips_by_ar.get((a, r), [])
                    relevant_x = [
                        x[(g, a, r, per, j)]
                        for j in valid_ips
                        if (g, a, r, per, j) in x
                    ]
                    if relevant_x:
                        self.model += lpSum(relevant_x) == z[g], f"One_IPS_{g}_{a}_{r}_{per}"

        for g in range(g_max):
            for (a, r) in ar_pairs:
                for per in periodos_asignatura.get(r, [1]):
                    valid_ips = ips_by_ar.get((a, r), [])
                    for j in valid_ips:
                        if (g, a, r, per, j) not in y:
                            continue
                        self.model += (
                            y[(g, a, r, per, j)] <= max_group * x[(g, a, r, per, j)],
                            f"BigM_upper_{g}_{a}_{r}_{per}_{j}",
                        )
                        self.model += (
                            y[(g, a, r, per, j)]
                            >= t[g] - max_group * (1 - x[(g, a, r, per, j)]),
                            f"BigM_lower_{g}_{a}_{r}_{per}_{j}",
                        )
                        self.model += (
                            y[(g, a, r, per, j)] <= t[g],
                            f"Y_leq_t_{g}_{a}_{r}_{per}_{j}",
                        )

        for (a, r) in ar_pairs:
            for per in periodos_asignatura.get(r, [1]):
                valid_ips = ips_by_ar.get((a, r), [])
                for j in valid_ips:
                    relevant_y = [
                        y[(g, a, r, per, j)]
                        for g in range(g_max)
                        if (g, a, r, per, j) in y
                    ]
                    if relevant_y:
                        cap_per = cap_dict.get((a, r, j), 0)
                        self.model += (
                            lpSum(relevant_y) <= cap_per,
                            f"CapPeriodo_{a}_{r}_{per}_{j}",
                        )

        for g in range(g_max):
            all_periods_set = set()
            for perts in periodos_asignatura.values():
                all_periods_set.update(perts)
            same_period_count = {}
            for (a, r) in ar_pairs:
                p_count = len(periodos_asignatura.get(r, []))
                same_period_count[(a, r)] = p_count
            if len(set(same_period_count.values())) > 1:
                for per in sorted(all_periods_set):
                    terms = []
                    for (a, r) in ar_pairs:
                        if per in periodos_asignatura.get(r, []):
                            valid_ips = ips_by_ar.get((a, r), [])
                            for j in valid_ips:
                                if (g, a, r, per, j) in x:
                                    terms.append(x[(g, a, r, per, j)])
                    if terms:
                        self.model += (
                            lpSum(terms) <= 1,
                            f"NoOverlap_g{g}_p{per}",
                        )

        solver = PULP_CBC_CMD(msg=self.verbose, timeLimit=time_limit)
        status = self.model.solve(solver)
        logger.info(f"TemporalGroupOptimizer status: {status}")

        results = []
        for g in range(g_max):
            if z[g].value() and z[g].value() > 0.5:
                group_size = int(round(t[g].value()))
                for (a, r) in ar_pairs:
                    for per in periodos_asignatura.get(r, [1]):
                        valid_ips = ips_by_ar.get((a, r), [])
                        for j in valid_ips:
                            if (g, a, r, per, j) in y and y[(g, a, r, per, j)].value() and y[(g, a, r, per, j)].value() > 0:
                                results.append({
                                    "Grupo": g + 1,
                                    "Tamano_Grupo": group_size,
                                    "Asignatura": a,
                                    "Rotacion": r,
                                    "Periodo": per,
                                    "ID_Institucion": j,
                                    "Estudiantes": int(round(y[(g, a, r, per, j)].value())),
                                    "Score_IPS": scores.get(j, 0.0),
                                })

        self.results = pd.DataFrame(results)
        if not self.results.empty:
            self.results = self.results.sort_values(
                ["Grupo", "Asignatura", "Rotacion", "Periodo"]
            ).reset_index(drop=True)

        return self.results

    def get_objective_value(self) -> float:
        return self.model.objective.value() if self.model else None

    def get_groups_summary(self) -> pd.DataFrame:
        if self.results is None or self.results.empty:
            return pd.DataFrame()
        return (
            self.results.groupby("Grupo")["Tamano_Grupo"]
            .first()
            .reset_index()
            .rename(columns={"Tamano_Grupo": "Estudiantes"})
        )
