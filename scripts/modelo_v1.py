import pandas as pd
import numpy as np
from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpInteger, PULP_CBC_CMD

print("=" * 80)
print("MODELO DE OPTIMIZACIÓN DE ASIGNACIÓN DE ESTUDIANTES A ESCENARIOS")
print("=" * 80)
print()

# -----------------------
# 1) Cargar datos
# -----------------------
PATH_XLSX = "data/Plantilla_V3_FacSalud.xlsx"
SET_ID = "SET001"
SEMESTRE = "2026-1"

print(f"Cargando datos desde: {PATH_XLSX}")
print(f"Set de ponderaciones: {SET_ID}")
print(f"Semestre: {SEMESTRE}")
print()

try:
    oferta   = pd.read_excel(PATH_XLSX, sheet_name="01_Oferta")
    calidad  = pd.read_excel(PATH_XLSX, sheet_name="03_Calidad")
    cupos    = pd.read_excel(PATH_XLSX, sheet_name="02_Oferta_x_Programa")
    costos   = pd.read_excel(PATH_XLSX, sheet_name="04_Costo_del_Sitio")
    
    # OJO: si tu hoja 05_Ponderaciones tiene panel arriba (4 filas),
    # el header real está en la fila 5 -> header=4 (indexado desde 0)
    pond = pd.read_excel(PATH_XLSX, sheet_name="05_Ponderaciones", header=4)
    
    print(f"✓ 01_Oferta: {oferta.shape[0]} instituciones")
    print(f"✓ 03_Calidad: {calidad.shape[0]} registros")
    print(f"✓ 02_Oferta_x_Programa: {cupos.shape[0]} cupos")
    print(f"✓ 04_Costo_del_Sitio: {costos.shape[0]} registros de costo")
    print(f"✓ 05_Ponderaciones: {pond.shape[0]} criterios")
    print()
except Exception as e:
    print(f"ERROR al cargar Excel: {e}")
    raise

# -----------------------
# 2) Construir DEMANDA (ejemplo placeholder)
# -----------------------
# IMPORTANTE: En tu caso esto debe salir de "Demanda Pregrado/Posgrado"
# Por ahora usaremos datos hardcodeados. Cuando tengas la hoja de demanda, 
# aquí harás un pd.read_excel() para cargar desde Excel

print("=== NOTA: Demanda usada es PLACEHOLDER ===")
print("Próximo paso: agregar hoja 'Demanda Pregrado/Posgrado' al Excel")
print()

demanda = pd.DataFrame([
    {"Semestre": "2026-1", "Programa": "Medicina", "Tipo_Estudiante": "Pregrado", "Tipo_Practica": "Rotación pregrado", "Demanda_Estudiantes": 40},
    {"Semestre": "2026-1", "Programa": "Medicina", "Tipo_Estudiante": "Pregrado", "Tipo_Practica": "Internado de medicina", "Demanda_Estudiantes": 25},
    {"Semestre": "2026-1", "Programa": "Medicina", "Tipo_Estudiante": "Posgrado", "Tipo_Practica": "Residencia Medicina", "Demanda_Estudiantes": 15},
])

print("Grupos de demanda:")
print(demanda)
print()

# -----------------------
# 3) Pesos: filtrar Set_ID, semestre y activos
# -----------------------
print("=== PONDERACIONES Y PESOS ===")

pond = pond[pond["Set_ID"].astype(str).str.strip() == SET_ID].copy()
print(f"Criterios para Set_ID={SET_ID}: {len(pond)}")

pond = pond[pond["Activo (0/1)"].fillna(0).astype(int) == 1].copy()
print(f"Criterios activos: {len(pond)}")

pond = pond[pond["Semestre_Vigencia (AAAA-S)"].astype(str).str.strip() == SEMESTRE].copy()
print(f"Criterios para semestre {SEMESTRE}: {len(pond)}")
print()

# Si Peso está vacío -> 0
pond["Peso (0-1)"] = pd.to_numeric(pond["Peso (0-1)"], errors="coerce").fillna(0.0)

peso_sum = pond["Peso (0-1)"].sum()
print("Criterios cargados:")
for _, r in pond.iterrows():
    print(f"  - {r['Criterio_Codigo']}: peso={r['Peso (0-1)']:.2f}, tipo={r['Tipo (Beneficio/Costo)']}")
print(f"\nSuma de pesos: {peso_sum:.4f}")

if abs(peso_sum - 1.0) > 1e-6:
    raise ValueError(f"Los pesos activos del Set_ID={SET_ID} para {SEMESTRE} deben sumar 1.0. Actualmente suman {peso_sum:.4f}")

weights = dict(zip(pond["Criterio_Codigo"], pond["Peso (0-1)"]))
crit_type = dict(zip(pond["Criterio_Codigo"], pond["Tipo (Beneficio/Costo)"]))

print(f"✓ Pesos validados (suma = {peso_sum:.4f})")
print()

# -----------------------
# 4) Armar tabla base de criterios por IPS
# -----------------------
# Merge Oferta + Calidad
base = oferta.merge(calidad, on="ID_Institucion", how="left", suffixes=("", "_cal"))

# Selección de columnas que existen en las hojas reales
# (verificar nombres exactos con inspect anterior)
crit_cols = [
    "ID_Institucion",
    "Acceso_Transporte_Publico (1-5)",
    "MisionVisionProposito_AlineacionDocencia (1-5)",
    "Evalua_Estudiantes_Profesores (0-5)",
    "Vinculacion_Planta_Especialistas_%",
    "Servicios_UCI (0/1)",           # UCI separado
    "Servicios_UCIN (0/1)",          # UCIN separado
    "Servicios_Pediatricos (0/1)",
    "Servicios_Obstetricia (0/1)",
    "Nro_Universidades_Comparten",
]

# Renombrar a los códigos de criterios usados en 05_Ponderaciones
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
base = base[crit_cols].rename(columns=rename_map)

# -----------------------
# 5) Funciones de normalización
# -----------------------
def norm_1_5(x):  # 1..5 -> 0..1
    return (x - 1.0) / 4.0

def norm_0_5(x):  # 0..5 -> 0..1
    return x / 5.0

def norm_pct(x):  # 0..100 -> 0..1
    return x / 100.0

def minmax_cost(series):
    # costo: menor es mejor
    mn, mx = series.min(), series.max()
    if pd.isna(mn) or pd.isna(mx) or abs(mx - mn) < 1e-9:
        return pd.Series([1.0] * len(series), index=series.index)  # si todo igual, no discrimina
    return (mx - series) / (mx - mn)

def minmax_benefit(series):
    mn, mx = series.min(), series.max()
    if pd.isna(mn) or pd.isna(mx) or abs(mx - mn) < 1e-9:
        return pd.Series([1.0] * len(series), index=series.index)
    return (series - mn) / (mx - mn)

# -----------------------
# 6) Preparar COSTOS por combinación (j,g)
# -----------------------
# Normalizar valores del costo: Cobro_EPP a 0/1
# (Si no se hizo en la sección anterior, hacerlo ahora)
costos = costos.copy()
if "Cobro_EPP_num" not in costos.columns:
    costos["Cobro_EPP_num"] = costos["Cobro_EPP (No cobra/Cobra a la Universidad)"].map({
        "No cobra EPP": 0,
        "Cobra EPP a la Universidad": 1,
    }).fillna(0)
if "pct_contra" not in costos.columns:
    costos["pct_contra"] = pd.to_numeric(costos["%_Contraprestacion_Matricula (0-100)"], errors="coerce")

# Función de lookup con fallback (Programa_Costo=Todos)
def lookup_costo(id_inst, prog, tipo_est, tipo_pract, semestre):
    # Convertir todo a string para comparación consistente
    id_inst = str(id_inst)
    prog = str(prog)
    tipo_est = str(tipo_est)
    tipo_pract = str(tipo_pract)
    semestre = str(semestre)
    
    # Convertir ID_Institucion en costos a string para comparación
    df = costos[
        (costos["ID_Institucion"].astype(str) == id_inst) &
        (costos["Tipo_Estudiante_Costo"].astype(str) == tipo_est) &
        (costos["Tipo_Practica_Costo"].astype(str) == tipo_pract) &
        (costos["Semestre_Vigencia (AAAA-S)"].astype(str) == semestre)
    ]
    df1 = df[df["Programa_Costo"].astype(str) == prog]
    if len(df1) > 0:
        row = df1.iloc[0]
        return row["pct_contra"], row["Cobro_EPP_num"]
    df2 = df[df["Programa_Costo"].astype(str) == "Todos"]
    if len(df2) > 0:
        row = df2.iloc[0]
        return row["pct_contra"], row["Cobro_EPP_num"]
    return np.nan, np.nan  # sin dato -> luego decides si penalizas o lo haces no factible

print("=== VALIDACIÓN DE DATOS ===")
print()

# Validar cupos
cupos["Cupo_Estimado_Semestral"] = pd.to_numeric(cupos["Cupo_Estimado_Semestral"], errors="coerce").fillna(0).astype(int)
cupos_lleños = cupos[cupos["Cupo_Estimado_Semestral"] > 0]
print(f"Registros de cupo con datos: {len(cupos_lleños)} / {len(cupos)}")

# Validar costos
costos["pct_contra"] = pd.to_numeric(costos["%_Contraprestacion_Matricula (0-100)"], errors="coerce")
costos_llenos = costos[costos["pct_contra"].notna()]
print(f"Registros de costo con datos: {len(costos_llenos)} / {len(costos)}")
print()

# Si no hay datos suficientes, generar datos de ejemplo
if len(cupos_lleños) == 0 or len(costos_llenos) == 0:
    print("⚠ PLANTILLA VACÍA: Generando datos de EJEMPLO para demostración...")
    print()
    
    # Generar cupos de ejemplo
    inst_ids = [7600103715, 500102104, 7600102541, 7600103359, 7600108077]
    cupos_ejemplo = []
    for inst in inst_ids:
        cupos_ejemplo.append({
            "ID_Institucion": inst,
            "Programa": "Medicina",
            "Tipo_Estudiante (Pregrado/Posgrado)": "Pregrado",
            "Semestre (AAAA-S)": "2026-1",
            "Cupo_Estimado_Semestral": 15
        })
    cupos = pd.DataFrame(cupos_ejemplo)
    print(f"✓ Cupos generados: {len(cupos)} registros")
    
    # Generar costos de ejemplo
    costos_ejemplo = []
    for inst in inst_ids:
        for tipo_pract in ["Rotación pregrado", "Internado de medicina"]:
            costos_ejemplo.append({
                "ID_Institucion": inst,
                "Programa_Costo": "Medicina",
                "Tipo_Estudiante_Costo": "Pregrado",
                "Tipo_Practica_Costo": tipo_pract,
                "Semestre_Vigencia (AAAA-S)": "2026-1",
                "%_Contraprestacion_Matricula (0-100)": 30.0,
                "Cobro_EPP (No cobra/Cobra a la Universidad)": "No cobra EPP",
            })
    costos = pd.DataFrame(costos_ejemplo)
    costos["Cobro_EPP_num"] = 0
    costos["pct_contra"] = costos["%_Contraprestacion_Matricula (0-100)"]
    print(f"✓ Costos generados: {len(costos)} registros")
    print()
    print("NOTA: Los datos de ejemplo se usan SOLO para esta demostración.")
    print("      En producción, llena 02_Oferta_x_Programa y 04_Costo_del_Sitio")
    print()
else:
    print("✓ Datos reales encontrados en el Excel")
    print()
    
    # Normalizar valores del costo si no lo hicimos ya
    costos = costos.copy()
    costos["Cobro_EPP_num"] = costos["Cobro_EPP (No cobra/Cobra a la Universidad)"].map({
        "No cobra EPP": 0,
        "Cobra EPP a la Universidad": 1,
    }).fillna(0)
    costos["pct_contra"] = pd.to_numeric(costos["%_Contraprestacion_Matricula (0-100)"], errors="coerce")

# -----------------------
# 7) Construir grupos G y pares factibles (j,g)
# -----------------------
# Cupos (capacidad) -> key (j, prog, tipo_est, semestre)
if "Cupo_Estimado_Semestral" not in cupos.columns:
    cupos["Cupo_Estimado_Semestral"] = 0
cupos["Cupo_Estimado_Semestral"] = pd.to_numeric(cupos["Cupo_Estimado_Semestral"], errors="coerce").fillna(0).astype(int)

cap_dict = {}
for _, r in cupos.iterrows():
    inst_id = str(r["ID_Institucion"])  # Convertir a string para consistencia
    prog = str(r["Programa"]) if pd.notna(r["Programa"]) else None
    tipo_est = str(r["Tipo_Estudiante (Pregrado/Posgrado)"]) if pd.notna(r["Tipo_Estudiante (Pregrado/Posgrado)"]) else None
    sem = str(r["Semestre (AAAA-S)"]) if pd.notna(r["Semestre (AAAA-S)"]) else None
    
    if all([prog, tipo_est, sem]):
        cap_dict[(inst_id, prog, tipo_est, sem)] = int(r["Cupo_Estimado_Semestral"])

# Demanda -> lista de grupos
demanda = demanda[demanda["Semestre"] == SEMESTRE].copy()
demanda["Demanda_Estudiantes"] = pd.to_numeric(demanda["Demanda_Estudiantes"], errors="coerce").fillna(0).astype(int)

groups = []
for _, g in demanda.iterrows():
    groups.append((g["Programa"], g["Tipo_Estudiante"], g["Tipo_Practica"], g["Semestre"]))

demand_dict = { (g["Programa"], g["Tipo_Estudiante"], g["Tipo_Practica"], g["Semestre"]): int(g["Demanda_Estudiantes"])
                for _, g in demanda.iterrows() }

instituciones = base["ID_Institucion"].dropna().unique().tolist()
# Convertir instituciones a string para consistencia
instituciones = [str(j) for j in instituciones]

# Feasibility: existe cupo (j,prog,tipo_est,semestre) > 0
feasible = {}
for j in instituciones:
    for (p, n, t, s) in groups:
        cap = cap_dict.get((j, p, n, s), 0)
        feasible[(j, (p,n,t,s))] = (cap > 0)

# -----------------------
# 8) Calcular V_{j,g}
# -----------------------
# Primero normalizar criterios "base" por IPS
S = base.set_index("ID_Institucion").copy()
# Convertir índice a string para consistencia
S.index = S.index.astype(str)

# Normalizaciones por tipo
# (ajusta si cambias códigos/columnas)
if "Acceso_Transporte_Publico" in S:
    S["Acceso_Transporte_Publico_norm"] = norm_1_5(pd.to_numeric(S["Acceso_Transporte_Publico"], errors="coerce"))
if "MisionVisionProposito_AlineacionDocencia" in S:
    S["MisionVisionProposito_AlineacionDocencia_norm"] = norm_1_5(pd.to_numeric(S["MisionVisionProposito_AlineacionDocencia"], errors="coerce"))
if "Evalua_Estudiantes_Profesores" in S:
    S["Evalua_Estudiantes_Profesores_norm"] = norm_0_5(pd.to_numeric(S["Evalua_Estudiantes_Profesores"], errors="coerce"))
if "Vinculacion_Planta_Especialistas_%" in S:
    S["Vinculacion_Planta_Especialistas_%_norm"] = norm_pct(pd.to_numeric(S["Vinculacion_Planta_Especialistas_%"], errors="coerce"))

# Servicios_UCI_UCIN: combina UCI + UCIN con lógica OR (si tiene uno u otro, vale 1)
if "Servicios_UCI" in S and "Servicios_UCIN" in S:
    uci = pd.to_numeric(S["Servicios_UCI"], errors="coerce").fillna(0).astype(int)
    ucin = pd.to_numeric(S["Servicios_UCIN"], errors="coerce").fillna(0).astype(int)
    S["Servicios_UCI_UCIN_norm"] = np.maximum(uci, ucin).clip(0, 1).astype(float)

# Otros servicios binarios
for b in ["Servicios_Pediatricos","Servicios_Obstetricia"]:
    if b in S:
        S[f"{b}_norm"] = pd.to_numeric(S[b], errors="coerce").fillna(0).clip(0,1)

# Nro_Universidades_Comparten es COSTO: normalizar como penalidad
if "Nro_Universidades_Comparten" in S:
    S["Nro_Universidades_Comparten_norm"] = minmax_cost(pd.to_numeric(S["Nro_Universidades_Comparten"], errors="coerce").fillna(0))

# Construir V(j,g)
V = {}
for j in instituciones:
    for g in groups:
        if not feasible[(j,g)]:
            continue
        p,n,t,s = g

        # costos por grupo
        pct_contra, cobro_epp = lookup_costo(j, p, n, t, s)

        # si falta costo, puedes: (1) hacerlo no factible o (2) penalizar
        if pd.isna(pct_contra):
            continue  # versión estricta: si no hay costo, no se asigna

        # normalizar costos: %
        contra_norm = 1.0 - float(pct_contra)/100.0  # mayor mejor
        epp_norm = 1.0 - float(cobro_epp)            # mayor mejor (no cobra=1)

# Construir V(j,g)
print("=== CÁLCULO DE SCORES ===")
V = {}
count_factible = 0
count_asignado = 0

for j in instituciones:
    for g in groups:
        if not feasible[(j,g)]:
            continue
        count_factible += 1
        
        p,n,t,s = g

        # costos por grupo
        pct_contra, cobro_epp = lookup_costo(j, p, n, t, s)

        # si falta costo, puedes: (1) hacerlo no factible o (2) penalizar
        if pd.isna(pct_contra):
            continue  # versión estricta: si no hay costo, no se asigna

        count_asignado += 1
        
        # normalizar costos: %
        contra_norm = 1.0 - float(pct_contra)/100.0  # mayor mejor
        epp_norm = 1.0 - float(cobro_epp)            # mayor mejor (no cobra=1)

        # armar score con pesos
        score = 0.0
        for k, w in weights.items():
            if w <= 0:
                continue
            if k == "%_Contraprestacion_Matricula":
                sk = contra_norm
            elif k == "Cobro_EPP":
                sk = epp_norm
            else:
                sk = S.loc[j, f"{k}_norm"] if f"{k}_norm" in S.columns else 0.0
                if pd.isna(sk):
                    sk = 0.0
            score += w * float(sk)

        V[(j,g)] = score

print(f"Pares (j,g) factibles: {count_factible}")
print(f"Pares (j,g) con costo asignado: {count_asignado}")
print(f"Pares (j,g) para optimizar: {len(V)}")
print()

# -----------------------
# 9) Optimización MILP (base)
# -----------------------
print("=== OPTIMIZACIÓN ===")
model = LpProblem("Asignacion_Practicas", LpMaximize)

x = {}
for (j,g), val in V.items():
    x[(j,g)] = LpVariable(f"x_{j}_{g[0]}_{g[1]}_{g[2]}_{g[3]}", lowBound=0, cat=LpInteger)

# Objetivo
model += lpSum(V[(j,g)] * x[(j,g)] for (j,g) in x)

# Demanda
for g in groups:
    model += lpSum(x[(j,g)] for j in instituciones if (j,g) in x) == demand_dict[g], f"Demanda_{g}"

# Capacidad agregada por (j,p,n,s)
# sum_t x <= cupo
for (j,p,n,s), cap in cap_dict.items():
    if s != SEMESTRE:
        continue
    relevant_groups = [g for g in groups if g[0]==p and g[1]==n and g[3]==s]
    if not relevant_groups:
        continue
    model += lpSum(x[(j,g)] for g in relevant_groups if (j,g) in x) <= cap, f"Cap_{j}_{p}_{n}_{s}"

# Resolver
solver = PULP_CBC_CMD(msg=True)
status = model.solve(solver)

print()
print("=== RESULTADOS ===")
print(f"Estado: {status}")
if hasattr(model, 'status'):
    obj_val = model.objective.value() if model.objective.value() else 0
    print(f"Valor óptimo: {obj_val:.4f}")
    
    # Validaciones de demanda vs asignaciones
    total_demanda = sum(demand_dict.values())
print()

# Resultados
rows = []
for (j,g), var in x.items():
    if var.value() and var.value() > 0:
        p,n,t,s = g
        rows.append({"ID_Institucion": j, "Programa": p, "Tipo_Estudiante": n, "Tipo_Practica": t, "Semestre": s,
                     "Asignados": int(var.value()), "Score_unitario": V[(j,g)]})

if rows:
    res = pd.DataFrame(rows).sort_values(["Programa","Tipo_Estudiante","Tipo_Practica","ID_Institucion"])
    print("Asignaciones realizadas:")
    print(res.to_string(index=False))
    print()
    
    # Resumen por grupo
    print("Resumen por grupo de demanda:")
    summary = res.groupby(["Programa", "Tipo_Estudiante", "Tipo_Practica"])["Asignados"].sum().reset_index()
    summary.columns = ["Programa", "Tipo_Estudiante", "Tipo_Practica", "Asignados"]
    
    # Agregar columna de demanda para comparación
    summary["Demanda"] = summary.apply(
        lambda row: demand_dict.get((row["Programa"], row["Tipo_Estudiante"], row["Tipo_Practica"], "2026-1"), 0),
        axis=1
    )
    summary["Gap"] = summary["Demanda"] - summary["Asignados"]
    print(summary.to_string(index=False))
    print()
    
    # Resumen de capacidad
    print("Utilización de capacidad por institución:")
    util = res.groupby("ID_Institucion")["Asignados"].sum().reset_index()
    util.columns = ["ID_Institucion", "Estudiantes_Asignados"]
    util["Capacidad"] = util["ID_Institucion"].apply(lambda j: sum(v for k, v in cap_dict.items() if k[0] == j))
    util["Utilización_%"] = (util["Estudiantes_Asignados"] / util["Capacidad"] * 100).round(1)
    print(util.to_string(index=False))
    
    # Resumen final
    print()
    print("=" * 80)
    print("RESUMEN EJECUTIVO")
    print("=" * 80)
    total_asignado = summary["Asignados"].sum()
    print(f"Total de estudiantes demandados: {total_demanda}")
    print(f"Total de estudiantes asignados: {total_asignado}")
    print(f"Brecha (no asignados): {total_demanda - total_asignado}")
    print(f"Tasa de cobertura: {total_asignado / total_demanda * 100:.1f}%")
    print()
    
    if total_asignado < total_demanda:
        print("⚠ PROBLEMA: La capacidad total es INSUFICIENTE")
        print(f"  Capacidad disponible: {sum(cap_dict.values())} cupos")
        print(f"  Demanda total: {total_demanda} estudiantes")
        print(f"  Déficit: {total_demanda - sum(cap_dict.values())} estudiantes")
        print()
        print("RECOMENDACIONES:")
        print("  1. Aumentar cupos en escenarios existentes")
        print("  2. Agregar nuevas instituciones/escenarios")
        print("  3. Ajustar demanda de estudiantes")

else:
    print("⚠ No se realizaron asignaciones. Verificar demanda, cupos y costos.")
    print()
    print("DEBUG INFO:")
    print(f"  Total demanda: {total_demanda}")
    print(f"  Total grupos: {len(groups)}")
    print(f"  Total instituciones: {len(instituciones)}")
    print(f"  Pares factibles: {count_factible}")
    print(f"  Pares con costo: {count_asignado}")
    print(f"  Pares para optimizar: {len(V)}")

