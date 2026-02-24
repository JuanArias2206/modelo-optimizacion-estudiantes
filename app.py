"""
Aplicación principal Streamlit
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from io import BytesIO
from typing import Optional, Dict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Imports locales
from src.core import DataLoader
from src.utils import setup_logging
from src.visualization import (
    render_header, render_upload_section, render_config_section,
    render_results_summary, render_asignaciones_table, render_capacidad_chart,
    render_demanda_vs_asignacion, render_debug_info
)
from scripts.modelo_v1 import ejecutar_modelo

# Configurar logging
logger = setup_logging("logs", "debug_logs")

# Configurar estado de sesión
if "results" not in st.session_state:
    st.session_state.results = None


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
    semestre: str,
    total_estudiantes: int,
    programa_manual: str,
    tipo_est_manual: str,
    tipo_practica_manual: str,
) -> Optional[Dict]:
    """Delega la ejecución del modelo al módulo scripts/modelo_v1.py."""
    try:
        return ejecutar_modelo(
            loader=loader,
            semestre=semestre,
            total_estudiantes=total_estudiantes,
            programa_manual=programa_manual,
            tipo_est_manual=tipo_est_manual,
            tipo_practica_manual=tipo_practica_manual,
            status_callback=st.write,
        )
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
