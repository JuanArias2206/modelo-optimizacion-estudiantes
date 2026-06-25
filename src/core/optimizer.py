"""
Modelo de optimización MILP para asignación de estudiantes
"""

import pandas as pd
import numpy as np
from pulp import (
    LpProblem, LpVariable, LpMaximize, lpSum, LpInteger, PULP_CBC_CMD,
    value as pulp_value, LpStatus,
)
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
        self._score_optimo = None

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

        # Score por (asignatura, IPS) si está disponible; si no, por IPS (compat.)
        def _score(a, j):
            if (a, j) in scores:
                return scores[(a, j)]
            return scores.get(j, 0.0)

        # Expresión de calidad (objetivo primario): maximizar score ponderado
        score_expr = lpSum(
            _score(a, j) * y[(g, a, r, j)]
            for g in range(g_max)
            for (a, r) in ar_pairs
            for j in ips_by_ar.get((a, r), [])
            if (g, a, r, j) in y
        )
        self.model += score_expr

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

        # ===========================================================
        # OPTIMIZACIÓN LEXICOGRÁFICA EN DOS FASES
        # -----------------------------------------------------------
        # Fase 1: maximizar la calidad total (score).
        # Fase 2: manteniendo la calidad óptima, MINIMIZAR el número de
        #         grupos activos. Esto evita la fragmentación degenerada
        #         (p.ej. 3 grupos de 4-6 en vez de 2 grupos de 7 para
        #         una IPS con 14 cupos): a igual calidad, el modelo
        #         prefiere llenar los grupos hasta max_group.
        # ===========================================================
        solver = PULP_CBC_CMD(msg=self.verbose, timeLimit=time_limit)

        # ---- Fase 1: calidad ----
        status = self.model.solve(solver)
        logger.info(f"GroupOptimizer fase 1 (calidad) status: {LpStatus[status]}")

        # ---- Fase 2: consolidación de grupos ----
        if LpStatus[status] == "Optimal":
            p_star = pulp_value(score_expr)
            # Piso de calidad: no perder más que una tolerancia numérica
            tol = max(1e-4, abs(p_star) * 1e-6) if p_star is not None else 1e-4
            self.model += (score_expr >= p_star - tol, "Lex_piso_calidad")
            # Nuevo objetivo: minimizar grupos activos (maximizar su negativo)
            self.model.setObjective(-lpSum(z[g] for g in range(g_max)))
            status2 = self.model.solve(solver)
            logger.info(
                f"GroupOptimizer fase 2 (consolidación) status: {LpStatus[status2]} | "
                f"calidad={p_star:.4f} | grupos={int(round(-pulp_value(self.model.objective)))}"
            )
            # Guardar la calidad óptima para reportes
            self._score_optimo = p_star
        else:
            self._score_optimo = pulp_value(score_expr)

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
                                "Score_IPS": _score(a, j),
                            })

        self.results = pd.DataFrame(results)
        if not self.results.empty:
            self.results = self.results.sort_values(
                ["Grupo", "Asignatura", "Rotacion"]
            ).reset_index(drop=True)

        return self.results

    def get_objective_value(self) -> float:
        # Tras la fase 2 el objetivo del modelo es -Σz (nº de grupos),
        # por lo que devolvemos la calidad óptima guardada en fase 1.
        return getattr(self, "_score_optimo", None)

    def get_groups_summary(self) -> pd.DataFrame:
        if self.results is None or self.results.empty:
            return pd.DataFrame()
        return (
            self.results.groupby("Grupo")["Tamano_Grupo"]
            .first()
            .reset_index()
            .rename(columns={"Tamano_Grupo": "Estudiantes"})
        )

