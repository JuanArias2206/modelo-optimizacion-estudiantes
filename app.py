"""
Aplicación principal Streamlit
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from io import BytesIO
import logging
from typing import Optional, Dict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

# Imports locales
from src.core import DataLoader, Optimizer, ScoreCalculator
from src.utils import setup_logging
from src.visualization import (
    render_header, render_upload_section, render_config_section,
    render_results_summary, render_asignaciones_table, render_capacidad_chart,
    render_demanda_vs_asignacion, render_debug_info
)

# Configurar logging
logger = setup_logging("logs", "debug_logs")

# Configurar estado de sesión
if "results" not in st.session_state:
    st.session_state.results = None
if "excel_data" not in st.session_state:
    st.session_state.excel_data = None


def generate_ejemplo_demanda(
    semestre: str = "2026-1",
    total_estudiantes: int = 80,
    programa: str = "Medicina",
    tipo_estudiante: str = "Pregrado",
    tipo_practica: str = "Rotación pregrado"
) -> pd.DataFrame:
    """Genera demanda de ejemplo (grupo único)"""
    return pd.DataFrame([
        {
            "Semestre": semestre,
            "Programa": programa,
            "Tipo_Estudiante": tipo_estudiante,
            "Tipo_Practica": tipo_practica,
            "Demanda_Estudiantes": int(total_estudiantes),
        }
    ])


def get_config_options_from_upload(uploaded_file):
    """Extrae Set_ID y semestres disponibles desde el archivo subido."""
    if uploaded_file is None:
        return [], []
    try:
        content = uploaded_file.getvalue()
        pond = pd.read_excel(BytesIO(content), sheet_name="05_Ponderaciones", header=4)
        set_options = (
            pond["Set_ID"].dropna().astype(str).str.strip().replace("", np.nan).dropna().unique().tolist()
            if "Set_ID" in pond.columns else []
        )
        semestre_options = (
            pond["Semestre_Vigencia (AAAA-S)"].dropna().astype(str).str.strip().replace("", np.nan).dropna().unique().tolist()
            if "Semestre_Vigencia (AAAA-S)" in pond.columns else []
        )
        return sorted(set_options), sorted(semestre_options)
    except Exception:
        return [], []


def preview_capacidad(uploaded_file) -> int:
    """Calcula capacidad total estimada desde 02_Oferta_x_Programa."""
    if uploaded_file is None:
        return 0
    try:
        content = uploaded_file.getvalue()
        cupos = pd.read_excel(BytesIO(content), sheet_name="02_Oferta_x_Programa")
        if "Cupo_Estimado_Semestral" not in cupos.columns:
            return 0
        vals = pd.to_numeric(cupos["Cupo_Estimado_Semestral"], errors="coerce").fillna(0)
        return int(vals.sum())
    except Exception:
        return 0


def generate_ejemplo_cupos(semestre: str = "2026-1") -> pd.DataFrame:
    """Genera cupos de ejemplo"""
    inst_ids = [7600103715, 500102104, 7600102541, 7600103359, 7600108077]
    rows = []
    for inst in inst_ids:
        rows.append({
            "ID_Institucion": inst,
            "Programa": "Medicina",
            "Tipo_Estudiante (Pregrado/Posgrado)": "Pregrado",
            "Semestre (AAAA-S)": semestre,
            "Cupo_Estimado_Semestral": 15
        })
    return pd.DataFrame(rows)


def generate_ejemplo_costos(semestre: str = "2026-1") -> pd.DataFrame:
    """Genera costos de ejemplo"""
    inst_ids = [7600103715, 500102104, 7600102541, 7600103359, 7600108077]
    rows = []
    for inst in inst_ids:
        for tipo_pract in ["Rotación pregrado", "Internado de medicina"]:
            rows.append({
                "ID_Institucion": inst,
                "Programa_Costo": "Medicina",
                "Tipo_Estudiante_Costo": "Pregrado",
                "Tipo_Practica_Costo": tipo_pract,
                "Semestre_Vigencia (AAAA-S)": semestre,
                "%_Contraprestacion_Matricula (0-100)": 30.0,
                "Cobro_EPP (No cobra/Cobra a la Universidad)": "No cobra EPP",
            })
    return pd.DataFrame(rows)


def clean_criterio_codigo(code: str) -> str:
    """Limpia código de criterio removiendo sufijos como '(...)' y espacios extra."""
    text = str(code or "").strip()
    if " (" in text:
        text = text.split(" (", 1)[0]
    return " ".join(text.split())


def to_bool01(x) -> int:
    """Mapea valores comunes Sí/No a 1/0 de forma robusta."""
    if pd.isna(x):
        return 0
    if isinstance(x, (int, float, np.integer, np.floating)):
        return 1 if float(x) > 0 else 0
    value = str(x).strip().lower()
    if value in {"sí", "si", "1", "true", "yes"}:
        return 1
    if value in {"no", "0", "false"}:
        return 0
    return 0


def map_epp_exigidos(x):
    """Mapea EPP_Exigidos a costo numérico: 0 (sin), 0.5 (parcial), 1 (completo)."""
    if pd.isna(x):
        return np.nan
    value = str(x).strip().lower()
    if "sin exigencia" in value:
        return 0.0
    if "parcial" in value:
        return 0.5
    if "completo" in value:
        return 1.0
    return np.nan


def compute_scores_debug(score_rows: list) -> pd.DataFrame:
    """Devuelve score por institución y criterios sk para auditoría."""
    if not score_rows:
        return pd.DataFrame()
    df = pd.DataFrame(score_rows)
    value_cols = [c for c in df.columns if c.startswith("sk_") or c == "score_total"]
    grouped = df.groupby("ID_Institucion", as_index=False)[value_cols].mean(numeric_only=True)
    return grouped


def generar_excel_resultados(results: Dict) -> bytes:
    """
    Genera un Excel bonito con múltiples hojas de resultados
    
    Args:
        results: Diccionario con asignaciones, summary, util, metrics
    
    Returns:
        bytes: Contenido del Excel de descargar
    """
    wb = Workbook()
    
    # Estilos
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")  # Azul oscuro
    header_font = Font(bold=True, color="FFFFFF", size=11)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    # ============= HOJA 1: ASIGNACIONES =============
    ws_asignaciones = wb.active
    ws_asignaciones.title = "Asignaciones"
    
    df_asignaciones = results["asignaciones"]
    
    # Escribir encabezados
    for col_idx, col_name in enumerate(df_asignaciones.columns, start=1):
        cell = ws_asignaciones.cell(row=1, column=col_idx)
        cell.value = col_name
        cell.fill = header_fill
        cell.font = header_font
        cell.border = border
        cell.alignment = center_align
    
    # Escribir datos
    for row_idx, (_, row) in enumerate(df_asignaciones.iterrows(), start=2):
        for col_idx, val in enumerate(row, start=1):
            cell = ws_asignaciones.cell(row=row_idx, column=col_idx)
            cell.value = val
            cell.border = border
            
            # Formatear números
            if isinstance(val, (int, np.integer)) and col_idx == 7:  # Asignados
                cell.alignment = center_align
            elif isinstance(val, (float, np.floating)) and col_idx == 8:  # Score_unitario
                cell.value = round(val, 4)
                cell.number_format = '0.0000'
                cell.alignment = center_align
    
    # Ajustar anchos de columna
    ancho_default = 15
    anchos = {
        0: 13,  # ID_Institucion
        1: 25,  # Institucion
        2: 18,  # Programa
        3: 18,  # Tipo_Estudiante
        4: 22,  # Tipo_Practica
        5: 12,  # Semestre
        6: 12,  # Asignados
        7: 15,  # Score_unitario
    }
    
    for col_idx in range(1, len(df_asignaciones.columns) + 1):
        col_letter = ws_asignaciones.cell(row=1, column=col_idx).column_letter
        ws_asignaciones.column_dimensions[col_letter].width = anchos.get(col_idx - 1, ancho_default)
    
    # Congelar primera fila
    ws_asignaciones.freeze_panes = "A2"
    
    # ============= HOJA 2: RESUMEN =============
    ws_resumen = wb.create_sheet("Resumen")
    
    # Construir metrics a partir de los datos disponibles
    metrics = {
        "demanda_total": results.get("total_demanda", 0),
        "asignados": results.get("total_asignado", 0),
        "brecha": results.get("brecha", 0),
        "cobertura_pct": results.get("tasa_cobertura", 0) * 100,
        "num_instituciones": results["debug"].get("instituciones", 0),
        "pares_factibles": results["debug"].get("pares_factibles", 0),
        "pares_con_costo": results["debug"].get("pares_con_costo", 0),
        "criterios": results["debug"].get("criterios", 0)
    }
    
    # Títulos y valores
    resumen_data = [
        ("Métrica", "Valor"),
        ("Demanda Total (estudiantes)", metrics["demanda_total"]),
        ("Asignados", metrics["asignados"]),
        ("Brecha", metrics["brecha"]),
        ("Cobertura (%)", f"{metrics['cobertura_pct']:.2f}%"),
        ("Número de instituciones", metrics["num_instituciones"]),
        ("Pares factibles", metrics["pares_factibles"]),
        ("Pares con costo", metrics["pares_con_costo"]),
        ("Criterios activos", metrics["criterios"]),
    ]
    
    for row_idx, (metrica, valor) in enumerate(resumen_data, start=1):
        # Columna A - Métrica
        cell_a = ws_resumen.cell(row=row_idx, column=1)
        cell_a.value = metrica
        if row_idx == 1:
            cell_a.fill = header_fill
            cell_a.font = header_font
            cell_a.alignment = center_align
        else:
            cell_a.alignment = Alignment(horizontal="left", vertical="center")
        cell_a.border = border
        
        # Columna B - Valor
        cell_b = ws_resumen.cell(row=row_idx, column=2)
        cell_b.value = valor
        if row_idx == 1:
            cell_b.fill = header_fill
            cell_b.font = header_font
            cell_b.alignment = center_align
        else:
            cell_b.alignment = Alignment(horizontal="right", vertical="center")
        cell_b.border = border
    
    ws_resumen.column_dimensions["A"].width = 35
    ws_resumen.column_dimensions["B"].width = 20
    
    # ============= HOJA 3: UTILIZACIÓN =============
    ws_util = wb.create_sheet("Utilización")
    
    df_util = results["util"]
    
    if df_util is not None and not df_util.empty:
        # Escribir encabezados
        for col_idx, col_name in enumerate(df_util.columns, start=1):
            cell = ws_util.cell(row=1, column=col_idx)
            cell.value = col_name
            cell.fill = header_fill
            cell.font = header_font
            cell.border = border
            cell.alignment = center_align
        
        # Escribir datos
        for row_idx, (_, row) in enumerate(df_util.iterrows(), start=2):
            for col_idx, val in enumerate(row, start=1):
                cell = ws_util.cell(row=row_idx, column=col_idx)
                cell.value = val
                cell.border = border
                cell.alignment = Alignment(horizontal="center", vertical="center")
                
                # Formatear porcentaje
                col_name = df_util.columns[col_idx - 1]
                if col_name == "Utilización_%" and isinstance(val, (int, float)):
                    cell.value = round(val, 2)
                    cell.number_format = '0.00"%"'
        
        # Ajustar anchos
        ws_util.column_dimensions["A"].width = 13
        ws_util.column_dimensions["B"].width = 25
        ws_util.column_dimensions["C"].width = 18
        ws_util.column_dimensions["D"].width = 18
        ws_util.column_dimensions["E"].width = 15
    
    # ============= GUARDAR A BYTES =============
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def procesar_datos(
    loader: DataLoader,
    set_id: str,
    semestre: str,
    total_estudiantes: int,
    programa_manual: str,
    tipo_est_manual: str,
    tipo_practica_manual: str
) -> Optional[Dict]:
    """Procesa datos y ejecuta optimización"""
    
    try:
        # Validar pesos
        loader.validate_pesas()
        
        # Obtener ponderaciones
        weights, crit_type = loader.get_ponderaciones_dict()

        # Validación explícita de suma de pesos activos
        pesos_activos = sum(float(v) for v in weights.values())
        if abs(pesos_activos - 1.0) > 1e-6:
            raise ValueError(
                f"Los pesos activos del set seleccionado deben sumar 1.0; suma actual={pesos_activos:.6f}"
            )
        
        st.write(f"✓ {len(weights)} criterios cargados")
        
        # Preparar cupos
        loader.cupos["Cupo_Estimado_Semestral"] = pd.to_numeric(
            loader.cupos["Cupo_Estimado_Semestral"], errors="coerce"
        ).fillna(0).astype(int)
        
        cupos_llenos = (loader.cupos["Cupo_Estimado_Semestral"] > 0).sum()
        
        # Si no hay cupos, generar ejemplo
        if cupos_llenos == 0:
            st.warning("⚠️ Plantilla sin cupos reales - usando datos de EJEMPLO")
            loader.cupos = generate_ejemplo_cupos(semestre)
            loader.costos = generate_ejemplo_costos(semestre)
        
        # Preparar costos
        loader.costos = loader.costos.copy()
        loader.costos["Cobro_EPP_num"] = loader.costos[
            "Cobro_EPP (No cobra/Cobra a la Universidad)"
        ].map({
            "No cobra EPP": 0,
            "Cobra EPP a la Universidad": 1,
        }).fillna(0)
        
        loader.costos["pct_contra"] = pd.to_numeric(
            loader.costos["%_Contraprestacion_Matricula (0-100)"], errors="coerce"
        )
        
        # Obtener demanda o usar demanda manual
        if loader.demanda is not None and not loader.demanda.empty and "Semestre" in loader.demanda.columns:
            demanda = loader.demanda[loader.demanda["Semestre"].astype(str) == str(semestre)].copy()
        else:
            st.info("ℹ️ Usando demanda manual definida en esta pantalla.")
            demanda = generate_ejemplo_demanda(
                semestre=semestre,
                total_estudiantes=total_estudiantes,
                programa=programa_manual,
                tipo_estudiante=tipo_est_manual,
                tipo_practica=tipo_practica_manual,
            )

        if demanda.empty:
            st.warning("⚠️ No se encontró demanda para el semestre seleccionado. Se aplicará demanda manual.")
            demanda = generate_ejemplo_demanda(
                semestre=semestre,
                total_estudiantes=total_estudiantes,
                programa=programa_manual,
                tipo_estudiante=tipo_est_manual,
                tipo_practica=tipo_practica_manual,
            )
        
        demanda["Demanda_Estudiantes"] = pd.to_numeric(
            demanda["Demanda_Estudiantes"], errors="coerce"
        ).fillna(0).astype(int)
        
        # Construir grupos y diccionarios
        groups = []
        for _, g in demanda.iterrows():
            groups.append((g["Programa"], g["Tipo_Estudiante"], g["Tipo_Practica"], g["Semestre"]))
        
        demand_dict = {
            (g["Programa"], g["Tipo_Estudiante"], g["Tipo_Practica"], g["Semestre"]): int(g["Demanda_Estudiantes"])
            for _, g in demanda.iterrows()
        }
        
        # Preparar cupos dict
        cap_dict = {}
        for _, r in loader.cupos.iterrows():
            inst_id = str(r["ID_Institucion"])
            prog = str(r["Programa"]).strip() if ("Programa" in loader.cupos.columns and pd.notna(r["Programa"])) else ""
            tipo_est = str(r["Tipo_Estudiante (Pregrado/Posgrado)"]).strip() if ("Tipo_Estudiante (Pregrado/Posgrado)" in loader.cupos.columns and pd.notna(r["Tipo_Estudiante (Pregrado/Posgrado)"])) else ""
            sem = str(r["Semestre (AAAA-S)"]).strip() if ("Semestre (AAAA-S)" in loader.cupos.columns and pd.notna(r["Semestre (AAAA-S)"])) else ""

            # fallback cuando vienen vacíos en el Excel
            if not prog:
                prog = programa_manual
            if not tipo_est:
                tipo_est = tipo_est_manual
            if not sem:
                sem = semestre

            cap_dict[(inst_id, prog, tipo_est, sem)] = int(r["Cupo_Estimado_Semestral"])
        
        # Instituciones
        instituciones = [str(j) for j in loader.oferta["ID_Institucion"].dropna().unique().tolist()]
        
        # Merge oferta + calidad (tolerante a columnas faltantes)
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

        # Compatibilidad: columna única UCI_UCIN
        if "Servicios_UCI_UCIN (0/1)" in base_raw.columns:
            base["Servicios_UCI_UCIN"] = base_raw["Servicios_UCI_UCIN (0/1)"]
        
        # Normalizar criterios
        S = ScoreCalculator.normalize_criteria(base)
        s_ids = S.index.astype(str)

        oferta_idx = loader.oferta.copy()
        oferta_idx["ID_Institucion"] = oferta_idx["ID_Institucion"].astype(str)
        oferta_idx = oferta_idx.set_index("ID_Institucion")

        calidad_idx = loader.calidad.copy()
        calidad_idx["ID_Institucion"] = calidad_idx["ID_Institucion"].astype(str)
        calidad_idx = calidad_idx.set_index("ID_Institucion")

        # Criterios adicionales del nuevo set
        if "Es_Hospital_Universitario" in loader.oferta.columns:
            hosp_uni = oferta_idx["Es_Hospital_Universitario"].reindex(s_ids, fill_value=0)
            S["Es_Hospital_Universitario_norm"] = hosp_uni.apply(to_bool01).values

        if "Escenario_Avalado_Practicas" in loader.oferta.columns:
            esc = oferta_idx["Escenario_Avalado_Practicas"].reindex(s_ids, fill_value=0)
            S["Escenario_Avalado_Practicas_norm"] = esc.apply(to_bool01).values

        # Compatibilidad UCI/UCIN/UCI_UCIN
        if "Servicios_UCI_UCIN" in base.columns:
            combo = base.set_index("ID_Institucion")["Servicios_UCI_UCIN"].reindex(s_ids, fill_value=0)
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
        
        # Calcular scores V(j,g)
        def lookup_costo(id_inst, prog, tipo_est, tipo_pract, semestre):
            id_inst = str(id_inst)
            prog = str(prog)
            tipo_est = str(tipo_est)
            tipo_pract = str(tipo_pract)
            semestre = str(semestre)

            c = loader.costos.copy()
            c["ID_Institucion"] = c["ID_Institucion"].astype(str)
            if "Tipo_Estudiante_Costo" in c.columns:
                c["Tipo_Estudiante_Costo"] = c["Tipo_Estudiante_Costo"].astype(str)
            if "Tipo_Practica_Costo" in c.columns:
                c["Tipo_Practica_Costo"] = c["Tipo_Practica_Costo"].astype(str)
            if "Semestre_Vigencia (AAAA-S)" in c.columns:
                c["Semestre_Vigencia (AAAA-S)"] = c["Semestre_Vigencia (AAAA-S)"].astype(str)
            if "Programa_Costo" in c.columns:
                c["Programa_Costo"] = c["Programa_Costo"].astype(str)
            if "EPP_Exigidos_num" not in c.columns and "EPP_Exigidos (Sin exigencia/Parcial/Completo + detalle)" in c.columns:
                c["EPP_Exigidos_num"] = c["EPP_Exigidos (Sin exigencia/Parcial/Completo + detalle)"].apply(map_epp_exigidos)

            # 1) Match estricto
            df = c[c["ID_Institucion"] == id_inst]
            if "Tipo_Estudiante_Costo" in c.columns:
                df = df[df["Tipo_Estudiante_Costo"] == tipo_est]
            if "Tipo_Practica_Costo" in c.columns:
                df = df[df["Tipo_Practica_Costo"] == tipo_pract]
            if "Semestre_Vigencia (AAAA-S)" in c.columns:
                df = df[df["Semestre_Vigencia (AAAA-S)"] == semestre]

            if "Programa_Costo" in c.columns:
                df1 = df[df["Programa_Costo"] == prog]
                df2 = df[df["Programa_Costo"] == "Todos"]
            else:
                df1 = df
                df2 = pd.DataFrame()

            if len(df1) > 0:
                row = df1.iloc[0]
                return row["pct_contra"], row["Cobro_EPP_num"], row.get("EPP_Exigidos_num", np.nan)
            if len(df2) > 0:
                row = df2.iloc[0]
                return row["pct_contra"], row["Cobro_EPP_num"], row.get("EPP_Exigidos_num", np.nan)

            # 2) Fallback sin tipo_practica
            df = c[c["ID_Institucion"] == id_inst]
            if "Tipo_Estudiante_Costo" in c.columns:
                df = df[df["Tipo_Estudiante_Costo"] == tipo_est]
            if "Semestre_Vigencia (AAAA-S)" in c.columns:
                df = df[df["Semestre_Vigencia (AAAA-S)"] == semestre]

            if "Programa_Costo" in c.columns:
                df1 = df[df["Programa_Costo"] == prog]
                df2 = df[df["Programa_Costo"] == "Todos"]
            else:
                df1 = df
                df2 = pd.DataFrame()

            if len(df1) > 0:
                row = df1.iloc[0]
                return row["pct_contra"], row["Cobro_EPP_num"], row.get("EPP_Exigidos_num", np.nan)
            if len(df2) > 0:
                row = df2.iloc[0]
                return row["pct_contra"], row["Cobro_EPP_num"], row.get("EPP_Exigidos_num", np.nan)

            # 3) Fallback por institución (neutral si falta)
            df = c[c["ID_Institucion"] == id_inst]
            if len(df) > 0:
                row = df.iloc[0]
                pct = row["pct_contra"] if pd.notna(row["pct_contra"]) else 50.0
                epp = row["Cobro_EPP_num"] if pd.notna(row["Cobro_EPP_num"]) else 0
                epp_exig = row.get("EPP_Exigidos_num", np.nan)
                return pct, epp, epp_exig

            return 50.0, 0, np.nan
        
        # Normalizar llaves de criterios de forma robusta
        weights_norm = {}
        for k, w in weights.items():
            key = clean_criterio_codigo(k)
            weights_norm[key] = weights_norm.get(key, 0.0) + float(w)

        # Validación explícita de pesos limpios
        pesos_limpios_sum = sum(weights_norm.values())
        if abs(pesos_limpios_sum - 1.0) > 1e-6:
            raise ValueError(
                f"La suma de pesos activos (limpios) debe ser 1.0; suma actual={pesos_limpios_sum:.6f}"
            )

        weights_raw_df = pd.DataFrame(
            {
                "criterio_raw": list(weights.keys()),
                "criterio_clean": [clean_criterio_codigo(k) for k in weights.keys()],
                "peso": list(weights.values()),
                "tipo": [crit_type.get(k) for k in weights.keys()],
            }
        )
        weights_clean_df = weights_raw_df.groupby("criterio_clean", as_index=False)["peso"].sum()

        criteria_status_rows = []
        for k in weights_norm.keys():
            source = "S_norm"
            if k == "%_Contraprestacion_Matricula":
                source = "costo_pct"
            elif k == "Cobro_EPP":
                source = "costo_cobro_epp"
            elif k == "EPP_Exigidos":
                source = "costo_epp_exigidos"
            elif k == "Admiten_Docentes_Externos":
                source = "calidad_bool"
            elif f"{k}_norm" not in S.columns:
                source = "missing"
            criteria_status_rows.append({"criterio": k, "source": source})
        criteria_status_df = pd.DataFrame(criteria_status_rows)

        special_criteria = {
            "%_Contraprestacion_Matricula",
            "Cobro_EPP",
            "EPP_Exigidos",
            "Admiten_Docentes_Externos",
        }

        missing_criteria = set()
        for k in weights_norm.keys():
            if k in special_criteria:
                continue
            if f"{k}_norm" not in S.columns:
                missing_criteria.add(k)

        V = {}
        count_factible = 0
        count_asignado = 0
        pair_score_rows = []
        epp_fallback_pairs = 0
        
        for j in instituciones:
            for g in groups:
                cap = cap_dict.get((j, g[0], g[1], g[3]), 0)
                if cap <= 0:
                    continue
                
                count_factible += 1
                p, n, t, s = g
                
                pct_contra, cobro_epp, epp_exig_val = lookup_costo(j, p, n, t, s)
                
                if pd.isna(pct_contra):
                    continue
                
                count_asignado += 1
                
                contra_norm = 1.0 - float(pct_contra) / 100.0
                cobro_epp_norm = 1.0 - float(cobro_epp)
                if pd.notna(epp_exig_val):
                    epp_exig_norm = 1.0 - float(epp_exig_val)
                else:
                    epp_exig_norm = cobro_epp_norm
                    epp_fallback_pairs += 1
                
                score = 0.0
                score_row = {"ID_Institucion": j}
                for k, w in weights_norm.items():
                    if w <= 0:
                        continue
                    
                    if k == "%_Contraprestacion_Matricula":
                        sk = contra_norm
                    elif k == "Cobro_EPP":
                        sk = cobro_epp_norm
                    elif k == "EPP_Exigidos":
                        sk = epp_exig_norm
                    elif k == "Admiten_Docentes_Externos":
                        sk = S.loc[j, "Admiten_Docentes_Externos_norm"] if "Admiten_Docentes_Externos_norm" in S.columns else 0.0
                    else:
                        sk = S.loc[j, f"{k}_norm"] if f"{k}_norm" in S.columns else 0.0
                        if f"{k}_norm" not in S.columns:
                            missing_criteria.add(k)
                        if pd.isna(sk):
                            sk = 0.0
                    
                    score += w * float(sk)
                    score_row[f"sk_{k}"] = float(sk)
                
                V[(j, g)] = score
                score_row["score_total"] = float(score)
                pair_score_rows.append(score_row)

        score_debug_df = compute_scores_debug(pair_score_rows)
        
        st.write(f"✓ Pares (j,g) para optimización: {len(V)}")
        
        # Optimizar
        optimizer = Optimizer(verbose=False)
        results_df = optimizer.optimize(V, demand_dict, cap_dict, instituciones, groups, semestre)

        # Agregar nombre de institución a resultados
        if not results_df.empty and "Institucion" in loader.oferta.columns:
            oferta_names = loader.oferta[["ID_Institucion", "Institucion"]].copy()
            oferta_names["ID_Institucion"] = oferta_names["ID_Institucion"].astype(str)
            results_df["ID_Institucion"] = results_df["ID_Institucion"].astype(str)
            results_df = results_df.merge(oferta_names, on="ID_Institucion", how="left")
            # Orden de columnas más amigable
            cols = [
                "ID_Institucion", "Institucion", "Programa", "Tipo_Estudiante",
                "Tipo_Practica", "Semestre", "Asignados", "Score_unitario"
            ]
            results_df = results_df[[c for c in cols if c in results_df.columns]]

        if not results_df.empty and "Score_unitario" in results_df.columns:
            results_df["Score_unitario"] = pd.to_numeric(results_df["Score_unitario"], errors="coerce").round(4)
        
        obj_val = optimizer.get_objective_value()

        score_consistency = {
            "max_abs_diff": None,
            "mean_abs_diff": None,
        }
        if not results_df.empty and not score_debug_df.empty:
            compare = results_df[["ID_Institucion", "Score_unitario"]].copy()
            compare["ID_Institucion"] = compare["ID_Institucion"].astype(str)
            score_debug_df["ID_Institucion"] = score_debug_df["ID_Institucion"].astype(str)
            compare = compare.merge(
                score_debug_df[["ID_Institucion", "score_total"]],
                on="ID_Institucion",
                how="left",
            )
            compare["abs_diff"] = (pd.to_numeric(compare["Score_unitario"], errors="coerce") - pd.to_numeric(compare["score_total"], errors="coerce")).abs()
            score_consistency["max_abs_diff"] = float(compare["abs_diff"].max()) if compare["abs_diff"].notna().any() else None
            score_consistency["mean_abs_diff"] = float(compare["abs_diff"].mean()) if compare["abs_diff"].notna().any() else None
        
        # Compilar resultados
        total_demanda = sum(demand_dict.values())
        total_asignado = results_df["Asignados"].sum() if not results_df.empty else 0
        brecha = total_demanda - total_asignado
        tasa_cobertura = (total_asignado / total_demanda * 100) if total_demanda > 0 else 0
        
        # Resumen por grupo
        if not results_df.empty:
            summary = results_df.groupby(["Programa", "Tipo_Estudiante", "Tipo_Practica"])["Asignados"].sum().reset_index()
            summary.columns = ["Programa", "Tipo_Estudiante", "Tipo_Practica", "Asignados"]
            summary["Demanda"] = summary.apply(
                lambda row: demand_dict.get((row["Programa"], row["Tipo_Estudiante"], row["Tipo_Practica"], semestre), 0),
                axis=1
            )
            summary["Gap"] = summary["Demanda"] - summary["Asignados"]
        else:
            summary = pd.DataFrame()
        
        # Utilización
        if not results_df.empty:
            util = results_df.groupby("ID_Institucion")["Asignados"].sum().reset_index()
            util.columns = ["ID_Institucion", "Estudiantes_Asignados"]
            util["Capacidad"] = util["ID_Institucion"].apply(
                lambda j: sum(v for k, v in cap_dict.items() if k[0] == j)
            )
            util["Capacidad"] = pd.to_numeric(util["Capacidad"], errors="coerce").fillna(0)
            util["Utilización_%"] = np.where(
                util["Capacidad"] > 0,
                (util["Estudiantes_Asignados"] / util["Capacidad"] * 100).round(1),
                0.0,
            )
            if "Institucion" in results_df.columns:
                util = util.merge(
                    results_df[["ID_Institucion", "Institucion"]].drop_duplicates(),
                    on="ID_Institucion",
                    how="left",
                )
        else:
            util = pd.DataFrame()

        base_debug_cols = [
            "ID_Institucion",
            "Acceso_Transporte_Publico (1-5)",
            "MisionVisionProposito_AlineacionDocencia (1-5)",
            "Evalua_Estudiantes_Profesores (0-5)",
            "Vinculacion_Planta_Especialistas_%",
            "Servicios_UCI (0/1)",
            "Servicios_UCIN (0/1)",
            "Servicios_UCI_UCIN (0/1)",
            "Servicios_Pediatricos (0/1)",
            "Servicios_Obstetricia (0/1)",
            "Nro_Universidades_Comparten",
            "Es_Hospital_Universitario",
            "Escenario_Avalado_Practicas",
            "Admiten_Docentes_Externos (Sí/No)",
            "Areas_Bienestar (0/1)",
            "Areas_Academicas (0/1)",
        ]
        base_debug = base_raw[[c for c in base_debug_cols if c in base_raw.columns]].copy()

        costos_debug_cols = [
            "ID_Institucion",
            "Programa_Costo",
            "Tipo_Estudiante_Costo",
            "Tipo_Practica_Costo",
            "Semestre_Vigencia (AAAA-S)",
            "%_Contraprestacion_Matricula (0-100)",
            "EPP_Exigidos (Sin exigencia/Parcial/Completo + detalle)",
            "Cobro_EPP (No cobra/Cobra a la Universidad)",
        ]
        costos_debug = loader.costos[[c for c in costos_debug_cols if c in loader.costos.columns]].copy()
        
        return {
            "asignaciones": results_df,
            "summary": summary,
            "util": util,
            "score_debug": score_debug_df,
            "total_demanda": total_demanda,
            "total_asignado": total_asignado,
            "brecha": brecha,
            "tasa_cobertura": tasa_cobertura,
            "obj_value": obj_val,
            "debug": {
                "instituciones": len(instituciones),
                "grupos": len(groups),
                "pares_factibles": count_factible,
                "pares_con_costo": count_asignado,
                "criterios": len(weights_norm),
                "missing_criteria": sorted(list(missing_criteria)),
                "epp_exigidos_fallback_pairs": epp_fallback_pairs,
                "score_consistency": score_consistency,
                "weights_raw": weights_raw_df,
                "weights_clean": weights_clean_df,
                "criteria_status": criteria_status_df,
                "base_debug": base_debug,
                "costos_debug": costos_debug,
                "score_debug": score_debug_df,
                "instituciones_list": instituciones,
                "groups_list": groups,
            }
        }
    
    except Exception as e:
        logger.error(f"Error procesando datos: {e}")
        st.error(f"❌ Error: {str(e)}")
        return None


def main():
    """Función principal"""
    render_header()

    # Sidebar simplificado
    with st.sidebar:
        st.header("🎯 Opciones")
        st.caption("La página muestra Entrada + Resultados en un solo flujo.")

    # Entrada
    uploaded_file = render_upload_section()

    if uploaded_file is None:
        st.info("ℹ️ Carga primero el Excel para ver Set_ID y Semestres disponibles.")
        return

    # Configuración dinámica según el archivo subido
    set_options, semestre_options = get_config_options_from_upload(uploaded_file)
    default_set = "SET-MEDICINA" if "SET-MEDICINA" in set_options else (set_options[0] if set_options else "SET001")
    default_sem = "2026-1" if "2026-1" in semestre_options else (semestre_options[0] if semestre_options else "2026-1")

    (
        set_id,
        semestre,
        total_estudiantes,
        programa_manual,
        tipo_est_manual,
        tipo_practica_manual,
    ) = render_config_section(
        set_options=set_options,
        semestre_options=semestre_options,
        default_set=default_set,
        default_semestre=default_sem,
    )

    # Advertencias dinámicas previas
    capacidad_total = preview_capacidad(uploaded_file)
    c1, c2, c3 = st.columns(3)
    c1.metric("Estudiantes a asignar", int(total_estudiantes))
    c2.metric("Cupos disponibles (estimado)", int(capacidad_total))
    c3.metric("Brecha preliminar", int(total_estudiantes - capacidad_total))

    if capacidad_total <= 0:
        st.error("❌ No se detectaron cupos válidos en 02_Oferta_x_Programa.")
    elif int(total_estudiantes) > int(capacidad_total):
        st.warning("⚠️ La cantidad de estudiantes es mayor que la capacidad total disponible; la cobertura será parcial.")
    else:
        st.success("✅ La capacidad total alcanza para la demanda indicada (a nivel agregado).")

    # Procesar
    if st.button("🚀 Ejecutar Optimización", use_container_width=True, type="primary"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name

        try:
            with st.spinner("⏳ Procesando..."):
                loader = DataLoader(tmp_path, set_id, semestre)
                loader.load_all()

                st.session_state.results = procesar_datos(
                    loader,
                    set_id,
                    semestre,
                    total_estudiantes,
                    programa_manual,
                    tipo_est_manual,
                    tipo_practica_manual,
                )

            if st.session_state.results:
                st.success("✅ Optimización completada")
        finally:
            Path(tmp_path).unlink()

    # Resultados en la misma página
    if st.session_state.results:
        st.markdown("---")
        st.header("📊 Resultados")
        results = st.session_state.results

        render_results_summary(results)

        if results["asignaciones"].empty:
            st.error("❌ No hubo asignaciones en esta corrida.")
            st.info(
                "Revisa el panel de debug: si `pares_factibles` es 0, suele indicar desalineación entre cupos y configuración manual; "
                "si `pares_con_costo` es muy bajo, faltan costos por institución o tipo de práctica."
            )
        else:
            st.success("✅ Se encontraron asignaciones factibles y se muestran abajo.")

        col1, col2 = st.columns(2)
        with col1:
            render_asignaciones_table(results["asignaciones"])
        with col2:
            render_demanda_vs_asignacion(results["summary"])

        render_capacidad_chart(results["util"])
        render_debug_info(results["debug"])

        st.header("📥 Descargar Resultados")
        excel_bytes = generar_excel_resultados(results)
        st.download_button(
            label="📊 Descargar resultados (Excel)",
            data=excel_bytes,
            file_name="asignaciones_optimizacion.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Ayuda siempre disponible abajo
    st.markdown("---")
    st.header("❓ Ayuda")

    with st.expander("🧮 Modelo matemático (MILP)"):
        st.markdown(
            r"""
            ### 1) Tipo de problema
            Este problema se modela como un **MILP de asignación/transportación** con múltiples criterios.

            ### 2) Conjuntos e índices
            - $J$: conjunto de instituciones (IPS/escenarios).
            - $G$: conjunto de grupos de demanda (combinación de programa, tipo de estudiante, tipo de práctica, semestre).
            - $K$: conjunto de criterios activos en el Set seleccionado.

            ### 3) Parámetros
            - $D_g$: estudiantes a asignar en el grupo $g\in G$.
            - $Cap_{j,p,n,s}$: cupo disponible en institución $j$ para programa $p$, nivel $n$, semestre $s$.
            - $w_k$: peso del criterio $k\in K$, con condición $\sum_{k\in K} w_k = 1$.
            - $s_{j,g,k}\in[0,1]$: score normalizado del criterio $k$ para el par $(j,g)$.
            - $V_{j,g}$: score agregado de asignar grupo $g$ a institución $j$.

            ### 4) Construcción del score multicriterio
            Primero se normalizan variables de distinta escala a $[0,1]$:
            - Escala 1–5: $s=(x-1)/4$
            - Escala 0–5: $s=x/5$
            - Porcentaje 0–100: $s=x/100$
            - Binarios: se usan como 0/1

            Para criterios de costo se invierte el sentido (menor costo = mayor score), p. ej.:
            $$
            s^{costo}=1-\frac{x}{100}
            $$

            El score final por par es:
            $$
            V_{j,g}=\sum_{k\in K} w_k\,s_{j,g,k}
            $$

            ### 5) Variable de decisión
            $$
            x_{j,g}\in\mathbb{Z}_{\ge 0}
            $$
            donde $x_{j,g}$ = número de estudiantes del grupo $g$ asignados a la institución $j$.

            ### 6) Función objetivo
            $$
            \max \sum_{g\in G}\sum_{j\in J} V_{j,g}\,x_{j,g}
            $$
            Se maximiza la utilidad total ponderada de la asignación.

            ### 7) Restricciones
            **(a) Satisfacción de demanda por grupo**
            $$
            \sum_{j\in J} x_{j,g} = D_g\qquad \forall g\in G
            $$

            **(b) Capacidad institucional**
            $$
            \sum_{g\in G(p,n,s)} x_{j,g} \le Cap_{j,p,n,s}
            \qquad \forall (j,p,n,s)
            $$

            **(c) Integralidad y no negatividad**
            $$
            x_{j,g}\in\mathbb{Z}_{\ge0}
            $$

            ### 8) Consideraciones prácticas implementadas
            - Si en cupos faltan programa/tipo/semestre, la app aplica fallback con la configuración manual.
            - Si faltan costos para una combinación exacta, se usan reglas de fallback para no perder factibilidad innecesariamente.
            - Si el Set activo no suma 1.0 en pesos, el modelo se bloquea por consistencia metodológica.

            ### 9) Extensiones OR recomendadas (futuras)
            - Límite de fragmentación por grupo: $\sum_j y_{j,g}\le L_g$.
            - Penalización por sobreconcentración en pocas instituciones.
            - Restricciones de equidad (balance entre IPS o entre subgrupos).
            - Frontera eficiencia costo-calidad (análisis multiobjetivo).
            """
        )

    with st.expander("📖 ¿Cómo usar la aplicación?"):
        st.markdown("""
        1. **Cargar archivo**: Sube tu plantilla V3 en Excel
        2. **Configurar**: Selecciona Set_ID, semestre y demanda manual
        3. **Ejecutar**: Haz clic en "Ejecutar Optimización"
        4. **Ver resultados**: Aparecen justo debajo, en esta misma pantalla
        """)

    with st.expander("📋 Estructura de la Plantilla"):
        st.markdown("""
        - **01_Oferta**: Instituciones, servicios y ubicación
        - **02_Oferta_x_Programa**: Cupos disponibles
        - **03_Calidad**: Criterios de calidad
        - **04_Costo_del_Sitio**: Contraprestación y EPP
        - **05_Ponderaciones**: Pesos de criterios
        - **Demanda Pregrado/Posgrado**: Estudiantes a ubicar (opcional)
        """)

    with st.expander("🎯 Criterios Disponibles"):
        criteria = [
            "Es_Hospital_Universitario",
            "Escenario_Avalado_Practicas",
            "Servicios_Pediatricos",
            "Servicios_Obstetricia",
            "MisionVisionProposito_AlineacionDocencia",
            "Admiten_Docentes_Externos",
            "Areas_Bienestar",
            "Areas_Academicas",
            "%_Contraprestacion_Matricula",
            "EPP_Exigidos / Cobro_EPP",
        ]
        for c in criteria:
            st.write(f"• {c}")
if __name__ == "__main__":
    main()
