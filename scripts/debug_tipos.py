import pandas as pd

PATH_XLSX = "data/Plantilla_V3_FacSalud.xlsx"

oferta = pd.read_excel(PATH_XLSX, sheet_name="01_Oferta")
base = oferta[["ID_Institucion"]].drop_duplicates()

print("=== TIPO Y VALOR DE ID_INSTITUCIÓN ===")
print(f"Tipo en oferta: {base['ID_Institucion'].dtype}")
print(f"Primeros 3 valores: {base['ID_Institucion'].head(3).tolist()}")
print(f"Tipo del primer valor: {type(base['ID_Institucion'].iloc[0])}")

# Verificar string vs int
v1 = 7600103715
v2 = "7600103715"
print(f"\n{v1} (int) == {v2} (str): {v1 == v2}")
print(f"str({v1}) == {v2}: {str(v1) == v2}")

# Ahora verificar el lookup
cap_dict = {}
cap_dict[(7600103715, "Medicina", "Pregrado", "2026-1")] = 15

print(f"\n=== LOOKUP TEST ===")
print(f"Cap con int: {cap_dict.get((7600103715, 'Medicina', 'Pregrado', '2026-1'), 0)}")
print(f"Cap con str: {cap_dict.get(('7600103715', 'Medicina', 'Pregrado', '2026-1'), 0)}")
