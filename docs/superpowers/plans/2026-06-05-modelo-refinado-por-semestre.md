# Modelo Refinado por Semestre — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modificar el modelo de optimización para que asigne estudiantes por semestre, formando grupos de tamaño controlado y distribuyéndolos por asignatura/rotación/IPS.

**Architecture:** Se agrega un `GroupOptimizer` que decide cuántos grupos formar (con tamaño min/max) y a qué IPS asignar cada grupo en cada rotación. El `DataLoader` se extiende para cargar la estructura del Mapa de Práctica (semestre → asignatura → rotación → IPS con cupo). La app Streamlit ofrece un modo "refinado" donde el usuario selecciona semestre y cantidad de estudiantes.

**Tech Stack:** Python 3.13, PuLP (MILP), Pandas, Streamlit, openpyxl

---

## Estructura de archivos

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `scripts/parse_mapa_practica.py` | Crear | Parsea el Mapa de Práctica Excel → DataFrame limpio |
| `src/core/data_loader.py` | Modificar | Agregar `load_rotaciones()` y `get_rotaciones_dict()` |
| `src/core/optimizer.py` | Modificar | Agregar clase `GroupOptimizer` con MILP de grupos |
| `app.py` | Modificar | Agregar modo "refinado" con selector de semestre y N estudiantes |
| `src/visualization/__init__.py` | Modificar | Agregar `render_grupos_table()`, `render_asignaciones_rotacion()` |

---

### Task 1: Parser del Mapa de Práctica

**Files:**
- Create: `scripts/parse_mapa_practica.py`

- [ ] **Step 1: Crear el script parser**

```python
"""
Parser del Mapa de Práctica general Medicina → estructura para el modelo refinado.
Lee el Excel del Mapa y produce un DataFrame limpio con:
  Semestre_plan, Asignatura, Rotacion, ID_Institucion, Institucion, Sede, Cupo
"""

import pandas as pd
import re
from pathlib import Path


PERIODO_MAP = {
    "Segundo": 2, "Tercero": 3, "Cuarto": 4, "Quinto": 5,
    "Sexto": 6, "Séptimo": 7, "Octavo": 8, "Noveno": 9,
    "Décimo": 10, "Undécimo": 11, "Duodécimo": 12,
}

GROUP_CONSTRAINTS = {
    5: {"min": 4, "max": 7}, 6: {"min": 4, "max": 7},
    7: {"min": 4, "max": 7}, 8: {"min": 4, "max": 7},
    9: {"min": 3, "max": 5}, 10: {"min": 3, "max": 5},
    11: {"min": 3, "max": 5}, 12: {"min": 3, "max": 5},
}


def parse_mapa_practica(excel_path: str) -> pd.DataFrame:
    df = pd.read_excel(excel_path, sheet_name="Hoja1", header=None)

    records = []
    current_periodo = None
    current_asignatura = None
    current_rotacion = None
    current_max = None

    for idx, row in df.iterrows():
        if idx < 2:
            continue

        if pd.notna(row[0]):
            current_periodo = str(row[0]).strip()
            if pd.notna(row[5]):
                current_max = int(row[5])

        if pd.notna(row[1]):
            current_asignatura = str(row[1]).strip()

        if pd.notna(row[2]):
            current_rotacion = str(row[2]).strip()

        if pd.notna(row[3]):
            escenario_raw = str(row[3]).strip()
            estudiantes = int(row[4]) if pd.notna(row[4]) else None

            id_match = re.search(r"(\d{9,10})\s*-\s*\d{2}", escenario_raw)
            id_inst = id_match.group(1) if id_match else None

            parts = escenario_raw.split("/")
            inst_name = parts[0].strip().replace("\n", " ") if parts else escenario_raw
            sede = parts[1].strip().replace("\n", " ") if len(parts) > 1 else None

            sem_plan = PERIODO_MAP.get(current_periodo)
            if sem_plan is None:
                continue

            records.append({
                "Semestre_plan": sem_plan,
                "Asignatura": current_asignatura,
                "Rotacion": current_rotacion,
                "ID_Institucion": id_inst,
                "Institucion": inst_name,
                "Sede": sede,
                "Cupo": estudiantes,
                "Max_estudiantes_periodo": current_max,
            })

    result = pd.DataFrame(records)
    result = result[result["Cupo"].notna()].copy()
    result["Cupo"] = result["Cupo"].astype(int)
    return result


def get_group_constraints(semestre_plan: int) -> dict:
    return GROUP_CONSTRAINTS.get(semestre_plan, {"min": 4, "max": 7})


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else (
        Path(__file__).resolve().parent.parent
        / "data" / "info_reunion_refinacion_modelo"
        / "Mapa de practica general Medicina 2025-1.xlsx"
    )

    df = parse_mapa_practica(str(path))
    print(f"Total registros: {len(df)}")
    print(f"Semestres: {sorted(df['Semestre_plan'].unique())}")
    print(f"Asignaturas: {df['Asignatura'].nunique()}")
    print(f"IPS únicas: {df['ID_Institucion'].dropna().nunique()}")
    print()
    print(df[df["Semestre_plan"].between(5, 10)].to_string(index=False))
```

- [ ] **Step 2: Ejecutar el parser y verificar output**

Run: `python scripts/parse_mapa_practica.py`
Expected: DataFrame con ~84 registros para semestres 5-10, columnas correctas.

- [ ] **Step 3: Commit**

```bash
git add scripts/parse_mapa_practica.py
git commit -m "feat: add Mapa de Práctica parser for refined model"
```

---

### Task 2: Extender DataLoader para estructura de rotaciones

**Files:**
- Modify: `src/core/data_loader.py`

- [ ] **Step 1: Agregar método `load_rotaciones()`**

Agregar al final de la clase `DataLoader` (después de `has_costos_data`):

```python
    def load_rotaciones(self, rotaciones_df: pd.DataFrame) -> None:
        """Carga datos de rotaciones desde DataFrame parseado del Mapa de Práctica."""
        self.rotaciones = rotaciones_df.copy()
        self.rotaciones["ID_Institucion"] = self.rotaciones["ID_Institucion"].astype(str)
        logger.info(
            f"✓ Rotaciones cargadas: {len(self.rotaciones)} registros, "
            f"semestres {sorted(self.rotaciones['Semestre_plan'].unique())}"
        )

    def get_rotaciones_dict(self, semestre_plan: int) -> dict:
        """Retorna {(asignatura, rotacion, id_institucion): cupo} para un semestre."""
        df = self.rotaciones[self.rotaciones["Semestre_plan"] == semestre_plan].copy()
        cap = {}
        for _, r in df.iterrows():
            key = (r["Asignatura"], r["Rotacion"], str(r["ID_Institucion"]))
            cap[key] = int(r["Cupo"])
        return cap

    def get_asignaturas_rotaciones(self, semestre_plan: int) -> dict:
        """Retorna {asignatura: [rotaciones]} para un semestre."""
        df = self.rotaciones[self.rotaciones["Semestre_plan"] == semestre_plan].copy()
        result = {}
        for asig in df["Asignatura"].unique():
            rots = df[df["Asignatura"] == asig]["Rotacion"].unique().tolist()
            result[asig] = rots
        return result

    def get_ips_for_rotacion(self, semestre_plan: int, asignatura: str, rotacion: str) -> list:
        """Retorna lista de (id_institucion, cupo) para una rotación específica."""
        df = self.rotaciones[
            (self.rotaciones["Semestre_plan"] == semestre_plan)
            & (self.rotaciones["Asignatura"] == asignatura)
            & (self.rotaciones["Rotacion"] == rotacion)
        ].copy()
        return [(str(r["ID_Institucion"]), int(r["Cupo"])) for _, r in df.iterrows()]
```

- [ ] **Step 2: Verificar que no rompe carga existente**

Run: `python -c "from src.core import DataLoader; dl = DataLoader('data/Plantilla_V3_FacSalud (1) (2).xlsx'); dl.load_all(); print('OK')"`
Expected: `OK` sin errores.

- [ ] **Step 3: Commit**

```bash
git add src/core/data_loader.py
git commit -m "feat: add rotaciones loading methods to DataLoader"
```

---

### Task 3: GroupOptimizer — MILP con grupos

**Files:**
- Modify: `src/core/optimizer.py`

- [ ] **Step 1: Agregar clase `GroupOptimizer` al final de `optimizer.py`**

```python
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
    ) -> pd.DataFrame:
        """
        Parameters
        ----------
        scores : Dict[id_institucion -> float]
            Score ponderado por IPS.
        cap_dict : Dict[(asignatura, rotacion, id_inst) -> int]
            Cupo por rotación en cada IPS.
        asignaturas_rotaciones : Dict[asignatura -> [rotaciones]]
            Estructura de asignaturas y sus rotaciones.
        n_estudiantes : int
            Total de estudiantes a distribuir.
        min_group, max_group : int
            Tamaño mínimo y máximo de grupo.
        """
        import math

        g_max = math.ceil(n_estudiantes / min_group)

        all_ips = set()
        for (a, r, j) in cap_dict:
            all_ips.add(j)
        ips_list = sorted(all_ips)

        ar_pairs = []
        for asig, rots in asignaturas_rotaciones.items():
            for rot in rots:
                ar_pairs.append((asig, rot))

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
                valid_ips = [j for (aa, rr, j) in cap_dict if aa == a and rr == r]
                for j in valid_ips:
                    x[(g, a, r, j)] = LpVariable(f"x_{g}_{a}_{r}_{j}", cat="Binary")
                    y[(g, a, r, j)] = LpVariable(f"y_{g}_{a}_{r}_{j}", lowBound=0, cat=LpInteger)

        self.model += lpSum(
            scores.get(j, 0.0) * y[(g, a, r, j)]
            for g in range(g_max)
            for (a, r) in ar_pairs
            for j in [jj for (aa, rr, jj) in cap_dict if aa == a and rr == r]
            if (g, a, r, j) in y
        )

        self.model += lpSum(t[g] for g in range(g_max)) == n_estudiantes, "Total_estudiantes"

        for g in range(g_max):
            self.model += t[g] >= min_group * z[g], f"Min_size_{g}"
            self.model += t[g] <= max_group * z[g], f"Max_size_{g}"

        for g in range(g_max):
            for (a, r) in ar_pairs:
                valid_ips = [j for (aa, rr, j) in cap_dict if aa == a and rr == r]
                relevant_x = [x[(g, a, r, j)] for j in valid_ips if (g, a, r, j) in x]
                if relevant_x:
                    self.model += lpSum(relevant_x) == z[g], f"One_IPS_{g}_{a}_{r}"

        for g in range(g_max):
            for (a, r) in ar_pairs:
                valid_ips = [j for (aa, rr, j) in cap_dict if aa == a and rr == r]
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
            valid_ips = [j for (aa, rr, j) in cap_dict if aa == a and rr == r]
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

        solver = PULP_CBC_CMD(msg=self.verbose)
        status = self.model.solve(solver)
        logger.info(f"GroupOptimizer status: {status}")

        results = []
        for g in range(g_max):
            if z[g].value() and z[g].value() > 0.5:
                group_size = int(round(t[g].value()))
                for (a, r) in ar_pairs:
                    valid_ips = [j for (aa, rr, j) in cap_dict if aa == a and rr == r]
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
```

- [ ] **Step 2: Verificar importación**

Run: `python -c "from src.core.optimizer import GroupOptimizer; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/core/optimizer.py
git commit -m "feat: add GroupOptimizer MILP with group size constraints"
```

---

### Task 4: Integración en app.py — Modo Refinado

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Agregar import del parser y GroupOptimizer**

Al inicio de `app.py`, después de los imports existentes, agregar:

```python
from src.core.optimizer import GroupOptimizer
from scripts.parse_mapa_practica import parse_mapa_practica, get_group_constraints
```

- [ ] **Step 2: Agregar función `procesar_refinado()`**

Agregar antes de `def main()`:

```python
def procesar_refinado(
    loader: DataLoader,
    rotaciones_df: pd.DataFrame,
    semestre_plan: int,
    n_estudiantes: int,
    set_id: str,
    semestre_vigencia: str,
) -> dict:
    """Ejecuta optimización refinada por semestre con grupos."""

    loader.load_rotaciones(rotaciones_df)

    weights, crit_type = loader.get_ponderaciones_dict()

    weights_norm = {}
    for k, w in weights.items():
        key = clean_criterio_codigo(k)
        weights_norm[key] = weights_norm.get(key, 0.0) + float(w)

    cap_dict = loader.get_rotaciones_dict(semestre_plan)
    ar_dict = loader.get_asignaturas_rotaciones(semestre_plan)

    constraints = get_group_constraints(semestre_plan)
    min_g = constraints["min"]
    max_g = constraints["max"]

    if n_estudiantes < min_g:
        st.error(f"Se necesitan al menos {min_g} estudiantes para formar un grupo.")
        return None

    base_raw = loader.oferta.merge(loader.calidad, on="ID_Institucion", how="left", suffixes=("", "_cal"))
    base = pd.DataFrame({"ID_Institucion": base_raw["ID_Institucion"]})

    rename_map = {
        "Acceso_Transporte_Publico (1-5)": "Acceso_Transporte_Publico",
        "MisionVisionProposito_AlineacionDocencia (1-5)": "MisionVisionProposito_AlineacionDocencia",
        "Evalua_Estudiantes_Profesores (0-5)": "Evalua_Estudiantes_Profesores",
        "Vinculacion_Planta_Especialistas_%": "Vinculacion_Planta_Especialistas_%",
        "Servicios_UCI (0/1)": "Servicios_UCI",
        "Servicios_UCIN (0/1)": "Servicios_UCIN",
        "Servicios_Pediatricos (0/1)": "Servicios_Pediatricos",
        "Servicios_Obstetricia (0/1)": "Servicios_Obstetricia",
        "Nro_Universidades_Comparten": "Nro_Universidades_Comparten",
    }
    for raw_col, norm_col in rename_map.items():
        if raw_col in base_raw.columns:
            base[norm_col] = base_raw[raw_col]

    S = ScoreCalculator.normalize_criteria(base)
    s_ids = S.index.astype(str)

    oferta_idx = loader.oferta.copy()
    oferta_idx["ID_Institucion"] = oferta_idx["ID_Institucion"].astype(str)
    oferta_idx = oferta_idx.set_index("ID_Institucion")

    calidad_idx = loader.calidad.copy()
    calidad_idx["ID_Institucion"] = calidad_idx["ID_Institucion"].astype(str)
    calidad_idx = calidad_idx.set_index("ID_Institucion")

    if "Es_Hospital_Universitario" in loader.oferta.columns:
        hosp_uni = oferta_idx["Es_Hospital_Universitario"].reindex(s_ids, fill_value=0)
        S["Es_Hospital_Universitario_norm"] = hosp_uni.apply(to_bool01).values

    if "Escenario_Avalado_Practicas" in loader.oferta.columns:
        esc = oferta_idx["Escenario_Avalado_Practicas"].reindex(s_ids, fill_value=0)
        S["Escenario_Avalado_Practicas_norm"] = esc.apply(to_bool01).values

    if "Servicios_UCI_UCIN (0/1)" in base_raw.columns:
        combo = base.set_index("ID_Institucion")["Servicios_UCI_UCIN (0/1)"].reindex(s_ids, fill_value=0)
        S["Servicios_UCI_UCIN_norm"] = combo.apply(to_bool01).astype(float).values
    elif "Servicios_UCI" in base.columns or "Servicios_UCIN" in base.columns:
        uci = base.set_index("ID_Institucion").get("Servicios_UCI", pd.Series(index=s_ids, data=0)).reindex(s_ids, fill_value=0)
        ucin = base.set_index("ID_Institucion").get("Servicios_UCIN", pd.Series(index=s_ids, data=0)).reindex(s_ids, fill_value=0)
        S["Servicios_UCI_UCIN_norm"] = np.maximum(
            uci.apply(to_bool01).astype(float),
            ucin.apply(to_bool01).astype(float),
        )

    if "Admiten_Docentes_Externos (Sí/No)" in loader.calidad.columns:
        adm = calidad_idx["Admiten_Docentes_Externos (Sí/No)"].reindex(s_ids, fill_value="No")
        adm_num = adm.astype(str).str.strip().str.lower().map({"sí": 1, "si": 1, "yes": 1, "1": 1, "true": 1}).fillna(0)
        S["Admiten_Docentes_Externos_norm"] = adm_num.values

    for col_raw, col_norm in [
        ("Areas_Bienestar (0/1)", "Areas_Bienestar_norm"),
        ("Areas_Academicas (0/1)", "Areas_Academicas_norm"),
    ]:
        if col_raw in loader.calidad.columns:
            col_s = calidad_idx[col_raw].reindex(s_ids, fill_value=0)
            S[col_norm] = pd.to_numeric(col_s, errors="coerce").fillna(0).clip(0, 1).values

    loader.costos = loader.costos.copy()
    loader.costos["Cobro_EPP_num"] = loader.costos[
        "Cobro_EPP (No cobra/Cobra a la Universidad)"
    ].map({"No cobra EPP": 0, "Cobra EPP a la Universidad": 1}).fillna(0)
    loader.costos["pct_contra"] = pd.to_numeric(
        loader.costos["%_Contraprestacion_Matricula (0-100)"], errors="coerce"
    )
    if "EPP_Exigidos (Sin exigencia/Parcial/Completo + detalle)" in loader.costos.columns:
        loader.costos["EPP_Exigidos_num"] = loader.costos[
            "EPP_Exigidos (Sin exigencia/Parcial/Completo + detalle)"
        ].apply(map_epp_exigidos)

    all_ips_in_rotaciones = set()
    for (a, r, j) in cap_dict:
        all_ips_in_rotaciones.add(j)

    scores = {}
    for j in all_ips_in_rotaciones:
        if j not in s_ids:
            scores[j] = 0.0
            continue

        score = 0.0
        for k, w in weights_norm.items():
            if w <= 0:
                continue
            if k == "%_Contraprestacion_Matricula":
                c = loader.costos.copy()
                c["ID_Institucion"] = c["ID_Institucion"].astype(str)
                df_c = c[c["ID_Institucion"] == j]
                if len(df_c) > 0:
                    pct = df_c["pct_contra"].iloc[0]
                    sk = 1.0 - float(pct) / 100.0 if pd.notna(pct) else 0.5
                else:
                    sk = 0.5
            elif k == "Cobro_EPP":
                c = loader.costos.copy()
                c["ID_Institucion"] = c["ID_Institucion"].astype(str)
                df_c = c[c["ID_Institucion"] == j]
                if len(df_c) > 0:
                    sk = 1.0 - float(df_c["Cobro_EPP_num"].iloc[0])
                else:
                    sk = 1.0
            elif k == "EPP_Exigidos":
                c = loader.costos.copy()
                c["ID_Institucion"] = c["ID_Institucion"].astype(str)
                df_c = c[c["ID_Institucion"] == j]
                if len(df_c) > 0 and "EPP_Exigidos_num" in df_c.columns:
                    val = df_c["EPP_Exigidos_num"].iloc[0]
                    sk = 1.0 - float(val) if pd.notna(val) else 0.5
                else:
                    sk = 0.5
            elif k == "Admiten_Docentes_Externos":
                sk = S.loc[j, "Admiten_Docentes_Externos_norm"] if "Admiten_Docentes_Externos_norm" in S.columns else 0.0
            else:
                col = f"{k}_norm"
                sk = S.loc[j, col] if col in S.columns else 0.0
                if pd.isna(sk):
                    sk = 0.0
            score += w * float(sk)
        scores[j] = round(score, 4)

    optimizer = GroupOptimizer(verbose=False)
    results_df = optimizer.optimize(
        scores=scores,
        cap_dict=cap_dict,
        asignaturas_rotaciones=ar_dict,
        n_estudiantes=n_estudiantes,
        min_group=min_g,
        max_group=max_g,
    )

    if not results_df.empty and "Institucion" in loader.oferta.columns:
        oferta_names = loader.oferta[["ID_Institucion", "Institucion"]].copy()
        oferta_names["ID_Institucion"] = oferta_names["ID_Institucion"].astype(str)
        results_df["ID_Institucion"] = results_df["ID_Institucion"].astype(str)
        results_df = results_df.merge(oferta_names, on="ID_Institucion", how="left")

    groups_summary = optimizer.get_groups_summary()
    total_asignado = results_df["Estudiantes"].sum() if not results_df.empty else 0

    return {
        "asignaciones": results_df,
        "grupos": groups_summary,
        "total_estudiantes": n_estudiantes,
        "total_asignado": int(total_asignado),
        "n_grupos": len(groups_summary),
        "min_group": min_g,
        "max_group": max_g,
        "semestre_plan": semestre_plan,
        "asignaturas": list(ar_dict.keys()),
        "obj_value": optimizer.get_objective_value(),
        "scores": scores,
    }
```

- [ ] **Step 3: Agregar UI de modo refinado en `main()`**

En `main()`, después de la sección de configuración existente y antes del botón "Ejecutar Optimización", agregar un selector de modo. Reemplazar la lógica del botón para soportar ambos modos.

Agregar después de `render_config_section`:

```python
    st.markdown("---")
    modo = st.radio(
        "Modo de optimización",
        ["Agregado (actual)", "Refinado por semestre"],
        horizontal=True,
        help="Agregado: modelo original sin grupos. Refinado: distribuye por semestre con grupos de tamaño controlado."
    )
```

Cuando `modo == "Refinado por semestre"`, mostrar:

```python
    if modo == "Refinado por semestre":
        st.subheader("Configuración Refinada")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            semestre_plan = st.selectbox(
                "Semestre del plan de estudios",
                options=[5, 6, 7, 8, 9, 10],
                index=0,
            )
        with col_r2:
            constraints = get_group_constraints(semestre_plan)
            n_estudiantes = st.number_input(
                f"Estudiantes en semestre {semestre_plan}",
                min_value=constraints["min"],
                max_value=75,
                value=60,
                step=1,
                help=f"Grupos de {constraints['min']} a {constraints['max']} estudiantes. Techo: 75."
            )
        st.caption(f"Restricción de grupos: {constraints['min']}-{constraints['max']} estudiantes por grupo")
```

- [ ] **Step 4: Modificar el botón de ejecución para soportar ambos modos**

Reemplazar el bloque del botón y procesamiento:

```python
    if st.button("Ejecutar Optimización", use_container_width=True, type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        try:
            with st.spinner("Procesando..."):
                loader = DataLoader(tmp_path, set_id, semestre)
                loader.load_all()

                if modo == "Refinado por semestre":
                    mapa_path = Path(__file__).parent / "data" / "info_reunion_refinacion_modelo" / "Mapa de practica general Medicina 2025-1.xlsx"
                    rotaciones_df = parse_mapa_practica(str(mapa_path))

                    st.session_state.results = procesar_refinado(
                        loader, rotaciones_df, semestre_plan, int(n_estudiantes),
                        set_id, semestre,
                    )
                    st.session_state.modo_resultado = "refinado"
                else:
                    st.session_state.results = procesar_datos(
                        loader, set_id, semestre, total_estudiantes,
                        programa_manual, tipo_est_manual, tipo_practica_manual,
                    )
                    st.session_state.modo_resultado = "agregado"

            if st.session_state.results:
                st.success("Optimización completada")
        finally:
            Path(tmp_path).unlink()
```

- [ ] **Step 5: Agregar renderizado de resultados refinados**

Después del bloque de resultados existentes, agregar condición para modo refinado:

```python
    if st.session_state.results:
        st.markdown("---")
        results = st.session_state.results
        modo_res = st.session_state.get("modo_resultado", "agregado")

        if modo_res == "refinado":
            st.header("Resultados — Modelo Refinado")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Semestre", results["semestre_plan"])
            col2.metric("Estudiantes", results["total_estudiantes"])
            col3.metric("Grupos formados", results["n_grupos"])
            col4.metric("Asignaturas", len(results["asignaturas"]))

            st.subheader("Grupos formados")
            st.dataframe(results["grupos"], use_container_width=True, hide_index=True)

            st.subheader("Asignaciones por grupo, asignatura y rotación")
            df_asig = results["asignaciones"]
            if not df_asig.empty:
                display_cols = ["Grupo", "Tamano_Grupo", "Asignatura", "Rotacion", "ID_Institucion", "Institucion", "Estudiantes", "Score_IPS"]
                display_cols = [c for c in display_cols if c in df_asig.columns]
                st.dataframe(df_asig[display_cols], use_container_width=True, hide_index=True)

                for asig in results["asignaturas"]:
                    st.markdown(f"**{asig}**")
                    df_a = df_asig[df_asig["Asignatura"] == asig]
                    if not df_a.empty:
                        fig = px.bar(
                            df_a,
                            x="Institucion" if "Institucion" in df_a.columns else "ID_Institucion",
                            y="Estudiantes",
                            color="Grupo",
                            barmode="stack",
                            title=f"Distribución en {asig}",
                        )
                        st.plotly_chart(fig, use_container_width=True)
        else:
            # ... (código existente para modo agregado, sin cambios)
```

- [ ] **Step 6: Verificar que la app corre sin errores**

Run: `streamlit run app.py`
Expected: La app carga, se puede seleccionar modo "Refinado por semestre", elegir semestre 5 con 60 estudiantes, y ejecutar.

- [ ] **Step 7: Commit**

```bash
git add app.py src/core/optimizer.py src/core/data_loader.py
git commit -m "feat: integrate refined mode with group optimizer into Streamlit app"
```

---

### Task 5: Agregar visualizaciones para modo refinado

**Files:**
- Modify: `src/visualization/__init__.py`

- [ ] **Step 1: Agregar función `render_grupos_table()`**

```python
def render_grupos_table(df_grupos):
    """Renderiza tabla resumen de grupos formados."""
    st.subheader("Grupos Formados")
    if df_grupos.empty:
        st.warning("No se formaron grupos")
        return
    st.dataframe(df_grupos, use_container_width=True, hide_index=True)
```

- [ ] **Step 2: Agregar función `render_asignaciones_rotacion()`**

```python
def render_asignaciones_rotacion(df_asignaciones, asignaturas):
    """Renderiza asignaciones desglosadas por asignatura y rotación."""
    st.subheader("Asignaciones por Asignatura y Rotación")
    if df_asignaciones.empty:
        st.warning("No hay asignaciones")
        return

    for asig in asignaturas:
        df_a = df_asignaciones[df_asignaciones["Asignatura"] == asig]
        if df_a.empty:
            continue

        st.markdown(f"**{asig}**")
        for rot in df_a["Rotacion"].unique():
            df_r = df_a[df_a["Rotacion"] == rot]
            st.caption(f"Rotación: {rot}")
            display_cols = ["Grupo", "Tamano_Grupo", "ID_Institucion", "Institucion", "Estudiantes", "Score_IPS"]
            display_cols = [c for c in display_cols if c in df_r.columns]
            st.dataframe(df_r[display_cols], use_container_width=True, hide_index=True)
```

- [ ] **Step 3: Commit**

```bash
git add src/visualization/__init__.py
git commit -m "feat: add visualization components for refined model results"
```

---

### Task 6: Verificación end-to-end

- [ ] **Step 1: Correr el modelo refinado para semestre 5 con 60 estudiantes**

Run: `streamlit run app.py` → seleccionar "Refinado por semestre" → semestre 5 → 60 estudiantes → Ejecutar

Expected:
- Se forman entre 9 y 15 grupos (60/7 = 9 mínimo, 60/4 = 15 máximo)
- Cada grupo tiene entre 4 y 7 estudiantes
- La suma de tamaños = 60
- Cada grupo tiene asignación para cada rotación de cada asignatura
- Ninguna IPS excede su cupo en ninguna rotación

- [ ] **Step 2: Verificar restricciones de capacidad**

```python
# Verificar que ninguna IPS excede cupo
for (a, r, j), cap in cap_dict.items():
    asignados = results[(results["Asignatura"]==a) & (results["Rotacion"]==r) & (results["ID_Institucion"]==j)]["Estudiantes"].sum()
    assert asignados <= cap, f"Exceso en {a}/{r}/{j}: {asignados} > {cap}"
```

- [ ] **Step 3: Probar con diferentes cantidades de estudiantes**

Probar con: 40, 50, 60, 70, 75 estudiantes en semestre 5.
Verificar que el modelo siempre encuentra solución factible y respeta restricciones.

- [ ] **Step 4: Commit final**

```bash
git add -A
git commit -m "feat: complete refined model with group-based optimization"
```
