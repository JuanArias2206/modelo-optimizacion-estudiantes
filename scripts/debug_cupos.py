import pandas as pd

PATH_XLSX = "data/Plantilla_V3_FacSalud.xlsx"

cupos = pd.read_excel(PATH_XLSX, sheet_name="02_Oferta_x_Programa")

print("=== CUPOS CARGADOS ===")
print(f"Shape: {cupos.shape}")
print("\nColumnas:", cupos.columns.tolist())
print("\nPrimeras filas:")
print(cupos.head(10))

# Generar cupos de ejemplo
inst_ids = ["7600103715", "500102104", "7600102541", "7600103359", "7600108077"]
cupos_ejemplo = []
for inst in inst_ids:
    cupos_ejemplo.append({
        "ID_Institucion": inst,
        "Programa": "Medicina",
        "Tipo_Estudiante (Pregrado/Posgrado)": "Pregrado",
        "Semestre (AAAA-S)": "2026-1",
        "Cupo_Estimado_Semestral": 15
    })
cupos_gen = pd.DataFrame(cupos_ejemplo)

print("\n=== CUPOS GENERADOS ===")
print(cupos_gen)

# Probar cap_dict
cap_dict = {}
for _, r in cupos_gen.iterrows():
    key = (r["ID_Institucion"], r["Programa"], r["Tipo_Estudiante (Pregrado/Posgrado)"], r["Semestre (AAAA-S)"])
    cap_dict[key] = int(r["Cupo_Estimado_Semestral"])

print("\n=== CAP_DICT ===")
for k, v in cap_dict.items():
    print(f"{k}: {v}")

# Probar lookup
print("\n=== LOOKUP PRUEBA ===")
j = "7600103715"
p = "Medicina"
n = "Pregrado"
s = "2026-1"
key = (j, p, n, s)
cap = cap_dict.get(key, 0)
print(f"Buscando {key}: {cap}")
