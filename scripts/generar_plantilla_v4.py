import sys
sys.path.insert(0, ".")

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from scripts.parse_mapa_practica import parse_mapa_practica

PLANTILLA_ORIGEN = "data/Plantilla_V3_FacSalud (1) (2).xlsx"
MAPA_PRACTICA = "data/info_reunion_refinacion_modelo/Mapa de practica general Medicina 2025-1.xlsx"
SALIDA = "data/Plantilla_V4_Refinada.xlsx"

print("Generando Plantilla V4 Refinada...")

wb_origen = load_workbook(PLANTILLA_ORIGEN)
wb_origen.save(SALIDA)
print(f"✓ Copiadas hojas: {wb_origen.sheetnames}")

rotaciones = parse_mapa_practica(MAPA_PRACTICA)
rotaciones = rotaciones[rotaciones["Semestre_plan"].between(5, 10)].copy()
rotaciones = rotaciones.rename(columns={
    "Semestre_plan": "Semestre_Plan",
    "ID_Institucion": "ID_Institucion",
    "Institucion": "Institucion",
    "Sede": "Sede",
    "Asignatura": "Asignatura",
    "Rotacion": "Rotacion",
    "Cupo": "Cupo_Maximo",
})
rotaciones = rotaciones[["Semestre_Plan", "Asignatura", "Rotacion", "ID_Institucion", "Institucion", "Sede", "Cupo_Maximo"]]

print(f"✓ Rotaciones 5to-10mo: {len(rotaciones)} registros")

demanda_data = []
for sem in [5, 6, 7, 8, 9, 10]:
    demanda_data.append({
        "Semestre_Plan": sem,
        "Programa": "Medicina",
        "Tipo_Estudiante": "Pregrado",
        "Demanda_Estudiantes": 60,
        "Grupo_Min": 4 if sem <= 8 else 3,
        "Grupo_Max": 7 if sem <= 8 else 5,
        "Techo_Max": 75,
        "Observaciones": ""
    })
demanda = pd.DataFrame(demanda_data)

print(f"✓ Demanda: {len(demanda)} semestres")

with pd.ExcelWriter(SALIDA, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
    rotaciones.to_excel(writer, sheet_name="06_Rotaciones", index=False)
    demanda.to_excel(writer, sheet_name="07_Demanda_Semestres", index=False)

print(f"✓ Hojas nuevas agregadas: 06_Rotaciones, 07_Demanda_Semestres")

wb = load_workbook(SALIDA)

header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
header_font = Font(bold=True, color="FFFFFF", size=11)

for sheet_name in ["06_Rotaciones", "07_Demanda_Semestres"]:
    ws = wb[sheet_name]
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 35)

    ws.freeze_panes = "A2"

wb.save(SALIDA)
print(f"\n✅ Archivo generado: {SALIDA}")

print("\n=== ESTRUCTURA DEL ARCHIVO ===")
for sheet in wb.sheetnames:
    ws = wb[sheet]
    print(f"  {sheet}: {ws.max_row} filas × {ws.max_column} columnas")

print("\n=== HOJA 06_Rotaciones (primeras 5 filas) ===")
print(rotaciones.head().to_string(index=False))

print("\n=== HOJA 07_Demanda_Semestres ===")
print(demanda.to_string(index=False))
