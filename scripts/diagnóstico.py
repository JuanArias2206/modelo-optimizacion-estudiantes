import pandas as pd

PATH_XLSX = "data/Plantilla_V3_FacSalud.xlsx"

cupos = pd.read_excel(PATH_XLSX, sheet_name="02_Oferta_x_Programa")
costos = pd.read_excel(PATH_XLSX, sheet_name="04_Costo_del_Sitio")

print("=== CUPOS DISPONIBLES ===")
print("\nSemestres únicos en cupos:")
print(cupos["Semestre (AAAA-S)"].unique())

print("\nProgramas únicos en cupos:")
print(cupos["Programa"].unique())

print("\nTipos de estudiante en cupos:")
print(cupos["Tipo_Estudiante (Pregrado/Posgrado)"].unique())

# Filtrar para 2026-1 y Medicina
print("\n=== CUPOS 2026-1 MEDICINA ===")
med_cupos = cupos[(cupos["Semestre (AAAA-S)"] == "2026-1") & (cupos["Programa"] == "Medicina")]
print(f"Registros encontrados: {len(med_cupos)}")
print(med_cupos[["ID_Institucion", "Programa", "Tipo_Estudiante (Pregrado/Posgrado)", "Cupo_Estimado_Semestral"]])

print("\n=== COSTOS DISPONIBLES ===")
print("\nSemestres únicos en costos:")
print(costos["Semestre_Vigencia (AAAA-S)"].unique())

print("\nTipos de práctica en costos:")
print(costos["Tipo_Practica_Costo"].unique())

# Filtrar para 2026-1 y Medicina
print("\n=== COSTOS 2026-1 MEDICINA ===")
kostos_med = costos[(costos["Semestre_Vigencia (AAAA-S)"] == "2026-1") & ((costos["Programa_Costo"] == "Medicina") | (costos["Programa_Costo"] == "Todos"))]
print(f"Registros encontrados: {len(kostos_med)}")
if len(kostos_med) > 0:
    print(kostos_med[["ID_Institucion", "Programa_Costo", "Tipo_Estudiante_Costo", "Tipo_Practica_Costo"]])
