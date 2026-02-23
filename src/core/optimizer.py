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
