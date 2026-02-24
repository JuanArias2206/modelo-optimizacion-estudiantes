"""
Componentes de visualización para Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


def render_header():
    """Renderiza encabezado de la aplicación"""
    st.set_page_config(
        page_title="Modelo de Optimización - Prácticas",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 Modelo de Optimización")
        st.markdown("#### Asignación de Estudiantes a Escenarios de Práctica")
    with col2:
        st.write("")  # Espaciado


def render_upload_section():
    """Renderiza sección de upload"""
    st.header("📁 Cargar Plantilla")
    
    uploaded_file = st.file_uploader(
        "Selecciona tu archivo Excel (Plantilla V3)",
        type=["xlsx", "xls"],
        help="Archivo debe contener: Oferta, Calidad, Cupos, Costos, Ponderaciones"
    )
    
    return uploaded_file


def render_config_section(
    set_options=None,
    semestre_options=None,
    default_set="SET001",
    default_semestre="2026-1"
):
    """Renderiza sección de configuración"""
    st.header("⚙️ Configuración")

    col1, col2 = st.columns(2)

    with col1:
        if set_options:
            idx = set_options.index(default_set) if default_set in set_options else 0
            set_id = st.selectbox(
                "Set de Ponderaciones",
                options=set_options,
                index=idx,
                help="Selecciona el Set_ID desde la hoja 05_Ponderaciones"
            )
        else:
            set_id = st.text_input(
                "Set de Ponderaciones",
                value=default_set,
                help="ID del set de ponderaciones a usar"
            )

    with col2:
        if semestre_options:
            idx = semestre_options.index(default_semestre) if default_semestre in semestre_options else 0
            semestre = st.selectbox(
                "Semestre",
                options=semestre_options,
                index=idx,
                help="Selecciona el semestre vigente"
            )
        else:
            semestre = st.text_input(
                "Semestre",
                value=default_semestre,
                help="Formato: AAAA-S (ej: 2026-1)"
            )

    st.subheader("🎯 Demanda manual")
    col3, col4, col5 = st.columns(3)
    with col3:
        total_estudiantes = st.number_input(
            "Cantidad total de estudiantes a asignar",
            min_value=1,
            value=80,
            step=1,
            help="Si no hay hoja de demanda, el modelo usará este valor"
        )
    with col4:
        programa_manual = st.text_input("Programa (manual)", value="Medicina")
    with col5:
        tipo_est_manual = st.selectbox("Tipo estudiante (manual)", ["Pregrado", "Posgrado"], index=0)

    tipo_practica_manual = st.text_input(
        "Tipo práctica (manual)",
        value="Rotación pregrado",
        help="Grupo único que se usa para la demanda manual"
    )

    st.warning("⚠️ Advertencia: si los pesos activos del Set_ID no suman 1.0, el modelo no se ejecuta.")
    st.warning("⚠️ Advertencia: si cupos/costos faltan por institución, esa institución puede quedar fuera de la asignación.")

    return set_id, semestre, total_estudiantes, programa_manual, tipo_est_manual, tipo_practica_manual


def render_results_summary(results_dict):
    """Renderiza resumen de resultados"""
    if not results_dict:
        st.warning("No hay resultados para mostrar")
        return
    
    st.header("📊 Resumen Ejecutivo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Demanda Total",
            results_dict.get("total_demanda", 0),
            delta=None
        )
    
    with col2:
        st.metric(
            "Asignados",
            results_dict.get("total_asignado", 0),
            delta=None
        )
    
    with col3:
        st.metric(
            "Brecha",
            results_dict.get("brecha", 0),
            delta=None
        )
    
    with col4:
        cobertura = results_dict.get("tasa_cobertura", 0)
        st.metric(
            "Cobertura %",
            f"{cobertura:.1f}%",
            delta=None
        )


def render_asignaciones_table(df_asignaciones):
    """Renderiza tabla de asignaciones"""
    st.header("📋 Asignaciones Realizadas")
    
    if df_asignaciones.empty:
        st.warning("No hay asignaciones")
        return
    
    st.dataframe(
        df_asignaciones,
        use_container_width=True,
        hide_index=True
    )


def render_capacidad_chart(df_util):
    """Renderiza gráfico de utilización de capacidad"""
    st.header("📈 Utilización de Capacidad")
    
    if df_util.empty:
        st.warning("No hay datos de utilización")
        return
    
    df_plot = df_util.copy()
    if "Institucion" in df_plot.columns:
        df_plot["Etiqueta_Institucion"] = df_plot["Institucion"].astype(str)
    else:
        df_plot["Etiqueta_Institucion"] = df_plot["ID_Institucion"].astype(str)

    fig = px.bar(
        df_plot,
        x="Etiqueta_Institucion",
        y="Utilización_%",
        title="Utilización de Capacidad por Institución",
        hover_data=["Estudiantes_Asignados", "Capacidad"],
        color="Utilización_%",
        color_continuous_scale="RdYlGn"
    )

    fig.add_hline(y=100, line_dash="dash", line_color="red", annotation_text="Capacidad límite")
    fig.update_layout(
        xaxis_title="Institución",
        yaxis_title="Utilización (%)",
        xaxis={"type": "category"},
    )
    fig.update_xaxes(tickangle=45)

    st.caption("Eje X: nombre de la institución. Línea roja: 100% de capacidad.")
    st.plotly_chart(fig, use_container_width=True)


def render_demanda_vs_asignacion(df_summary):
    """Renderiza comparación demanda vs asignación"""
    st.header("🎯 Demanda vs Asignación por Grupo")
    
    if df_summary.empty:
        st.warning("No hay datos de demanda")
        return
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df_summary["Tipo_Practica"],
        y=df_summary["Demanda"],
        name="Demanda",
        marker_color="lightblue"
    ))
    
    fig.add_trace(go.Bar(
        x=df_summary["Tipo_Practica"],
        y=df_summary["Asignados"],
        name="Asignados",
        marker_color="darkblue"
    ))
    
    fig.update_layout(barmode="group", title="Demanda vs Asignación")
    st.plotly_chart(fig, use_container_width=True)


def render_debug_info(debug_dict):
    """Renderiza información de debug"""
    with st.expander("🔧 Información de Debug"):
        if not debug_dict:
            st.info("No hay datos de debug disponibles")
            return

        st.subheader("Resumen")
        resumen_keys = [
            "instituciones",
            "grupos",
            "pares_factibles",
            "pares_con_costo",
            "criterios",
            "missing_criteria",
            "epp_exigidos_fallback_pairs",
            "score_consistency",
        ]
        resumen = {k: debug_dict.get(k) for k in resumen_keys if k in debug_dict}
        st.json(resumen)

        if "weights_raw" in debug_dict:
            st.subheader("Ponderaciones (raw)")
            st.dataframe(debug_dict["weights_raw"], use_container_width=True, hide_index=True)

        if "weights_clean" in debug_dict:
            st.subheader("Ponderaciones (clean)")
            st.dataframe(debug_dict["weights_clean"], use_container_width=True, hide_index=True)

        if "criteria_status" in debug_dict:
            st.subheader("Estado de criterios activos")
            st.dataframe(debug_dict["criteria_status"], use_container_width=True, hide_index=True)

        inst_list = debug_dict.get("instituciones_list")
        if inst_list:
            st.subheader("Debug por institución")
            inst_sel = st.selectbox("Selecciona ID_Institucion", options=inst_list)

            base_debug = debug_dict.get("base_debug")
            if base_debug is not None and not base_debug.empty:
                st.caption("Base (Oferta + Calidad)")
                st.dataframe(
                    base_debug[base_debug["ID_Institucion"].astype(str) == str(inst_sel)],
                    use_container_width=True,
                    hide_index=True,
                )

            score_debug = debug_dict.get("score_debug")
            if score_debug is not None and not score_debug.empty:
                st.caption("Score por criterio (promedio por institución)")
                st.dataframe(
                    score_debug[score_debug["ID_Institucion"].astype(str) == str(inst_sel)],
                    use_container_width=True,
                    hide_index=True,
                )

            costos_debug = debug_dict.get("costos_debug")
            if costos_debug is not None and not costos_debug.empty:
                st.caption("Costos (filtrado por institución)")
                st.dataframe(
                    costos_debug[costos_debug["ID_Institucion"].astype(str) == str(inst_sel)],
                    use_container_width=True,
                    hide_index=True,
                )

        if "score_debug" in debug_dict and debug_dict["score_debug"] is not None:
            st.subheader("Score Debug Completo")
            st.dataframe(debug_dict["score_debug"], use_container_width=True, hide_index=True)
