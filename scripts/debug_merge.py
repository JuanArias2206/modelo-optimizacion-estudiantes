import pandas as pd
import numpy as np

PATH_XLSX = "data/Plantilla_V3_FacSalud.xlsx"

oferta = pd.read_excel(PATH_XLSX, sheet_name="01_Oferta")
calidad = pd.read_excel(PATH_XLSX, sheet_name="03_Calidad")

print("=== MERGE DEBUG ===")
print(f"Oferta shape: {oferta.shape}")
print(f"Oferta IDs: {oferta['ID_Institucion'].nunique()} únicas")
print(f"\nCalidad shape: {calidad.shape}")
print(f"Calidad IDs: {calidad['ID_Institucion'].nunique()} únicas")

base = oferta.merge(calidad, on="ID_Institucion", how="left", suffixes=("", "_cal"))
print(f"\nBase (después merge) shape: {base.shape}")
print(f"Base IDs únicas: {base['ID_Institucion'].nunique()}")

inst_list = base["ID_Institucion"].dropna().unique().tolist()
print(f"\nInstituciones en base después dropna: {len(inst_list)}")
print(f"Primeras 10: {inst_list[:10]}")

# Verificar si hay datos en las columnas de cupos generados
cupos_gen = pd.DataFrame([
    {"ID_Institucion": inst, "Programa": "Medicina", "Tipo_Estudiante (Pregrado/Posgrado)": "Pregrado", "Semestre (AAAA-S)": "2026-1", "Cupo_Estimado_Semestral": 15}
    for inst in ["7600103715", "500102104", "7600102541", "7600103359", "7600108077"]
])

print(f"\n=== FACTIBILIDAD TEST ===")
cap_dict = {}
for _, r in cupos_gen.iterrows():
    cap_dict[(r["ID_Institucion"], r["Programa"], r["Tipo_Estudiante (Pregrado/Posgrado)"], r["Semestre (AAAA-S)"])] = int(r["Cupo_Estimado_Semestral"])

group_test = ("Medicina", "Pregrado", "Rotación pregrado", "2026-1")
print(f"\nVerificando grupo: {group_test}")

for j in inst_list[:3]:
    p, n, t, s = group_test
    cap = cap_dict.get((j, p, n, s), 0)
    feasible = (cap > 0)
    print(f"  {j}: cap={cap}, factible={feasible}")
