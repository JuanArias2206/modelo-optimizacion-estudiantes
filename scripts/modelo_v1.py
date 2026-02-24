"""Lógica central del modelo de optimización (único punto de ajuste del modelo)."""

from __future__ import annotations

from typing import Callable, Dict, Optional

import numpy as np
import pandas as pd

from src.core import Optimizer, ScoreCalculator


CRITERIA_REQUIRED_NORM_COLUMNS = {
    "Acceso_Transporte_Publico": "Acceso_Transporte_Publico_norm",
    "MisionVisionProposito_AlineacionDocencia": "MisionVisionProposito_AlineacionDocencia_norm",
    "Evalua_Estudiantes_Profesores": "Evalua_Estudiantes_Profesores_norm",
    "Vinculacion_Planta_Especialistas_%": "Vinculacion_Planta_Especialistas_%_norm",
    "Servicios_Pediatricos": "Servicios_Pediatricos_norm",
    "Servicios_Obstetricia": "Servicios_Obstetricia_norm",
    "Nro_Universidades_Comparten": "Nro_Universidades_Comparten_norm",
    "Es_Hospital_Universitario": "Es_Hospital_Universitario_norm",
    "Escenario_Avalado_Practicas": "Escenario_Avalado_Practicas_norm",
    "Admiten_Docentes_Externos": "Admiten_Docentes_Externos_norm",
    "Areas_Bienestar": "Areas_Bienestar_norm",
    "Areas_Academicas": "Areas_Academicas_norm",
}


def _notify(status_callback: Optional[Callable[[str], None]], message: str) -> None:
    if status_callback:
        status_callback(message)


def generate_ejemplo_demanda(
    semestre: str,
    total_estudiantes: int,
    programa: str,
    tipo_estudiante: str,
    tipo_practica: str,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Semestre": semestre,
                "Programa": programa,
                "Tipo_Estudiante": tipo_estudiante,
                "Tipo_Practica": tipo_practica,
                "Demanda_Estudiantes": int(total_estudiantes),
            }
        ]
    )


def generate_ejemplo_cupos(semestre: str) -> pd.DataFrame:
    inst_ids = [7600103715, 500102104, 7600102541, 7600103359, 7600108077]
    rows = []
    for inst in inst_ids:
        rows.append(
            {
                "ID_Institucion": inst,
                "Programa": "Medicina",
                "Tipo_Estudiante (Pregrado/Posgrado)": "Pregrado",
                "Semestre (AAAA-S)": semestre,
                "Cupo_Estimado_Semestral": 15,
            }
        )
    return pd.DataFrame(rows)


def generate_ejemplo_costos(semestre: str) -> pd.DataFrame:
    inst_ids = [7600103715, 500102104, 7600102541, 7600103359, 7600108077]
    rows = []
    for inst in inst_ids:
        for tipo_pract in ["Rotación pregrado", "Internado de medicina"]:
            rows.append(
                {
                    "ID_Institucion": inst,
                    "Programa_Costo": "Medicina",
                    "Tipo_Estudiante_Costo": "Pregrado",
                    "Tipo_Practica_Costo": tipo_pract,
                    "Semestre_Vigencia (AAAA-S)": semestre,
                    "%_Contraprestacion_Matricula (0-100)": 30.0,
                    "Cobro_EPP (No cobra/Cobra a la Universidad)": "No cobra EPP",
                }
            )
    return pd.DataFrame(rows)


def _normalize_weight_key(raw_key: str) -> str:
    key = str(raw_key).strip()
    if "(" in key and key.endswith(")"):
        key = key[: key.rfind("(")].strip()
    return key


def _has_column(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns


def _require_columns(df: pd.DataFrame, cols: list[str], sheet_name: str) -> None:
    missing = [col for col in cols if col not in df.columns]
    if missing:
        raise ValueError(f"En {sheet_name} faltan columnas requeridas: {missing}")


def _lookup_costo(
    costos: pd.DataFrame,
    id_inst: str,
    prog: str,
    tipo_est: str,
    tipo_pract: str,
    semestre: str,
) -> tuple[float, float]:
    c = costos.copy()
    c["ID_Institucion"] = c["ID_Institucion"].astype(str)
    if _has_column(c, "Tipo_Estudiante_Costo"):
        c["Tipo_Estudiante_Costo"] = c["Tipo_Estudiante_Costo"].astype(str)
    if _has_column(c, "Tipo_Practica_Costo"):
        c["Tipo_Practica_Costo"] = c["Tipo_Practica_Costo"].astype(str)
    if _has_column(c, "Semestre_Vigencia (AAAA-S)"):
        c["Semestre_Vigencia (AAAA-S)"] = c["Semestre_Vigencia (AAAA-S)"].astype(str)
    if _has_column(c, "Programa_Costo"):
        c["Programa_Costo"] = c["Programa_Costo"].astype(str)

    strict = c[c["ID_Institucion"] == str(id_inst)]
    if _has_column(c, "Tipo_Estudiante_Costo"):
        strict = strict[strict["Tipo_Estudiante_Costo"] == str(tipo_est)]
    if _has_column(c, "Tipo_Practica_Costo"):
        strict = strict[strict["Tipo_Practica_Costo"] == str(tipo_pract)]
    if _has_column(c, "Semestre_Vigencia (AAAA-S)"):
        strict = strict[strict["Semestre_Vigencia (AAAA-S)"] == str(semestre)]

    strict_prog = strict[strict["Programa_Costo"] == str(prog)] if _has_column(c, "Programa_Costo") else strict
    if not strict_prog.empty:
        row = strict_prog.iloc[0]
        return float(row["pct_contra"]), float(row["Cobro_EPP_num"])

    strict_todos = strict[strict["Programa_Costo"] == "Todos"] if _has_column(c, "Programa_Costo") else pd.DataFrame()
    if not strict_todos.empty:
        row = strict_todos.iloc[0]
        return float(row["pct_contra"]), float(row["Cobro_EPP_num"])

    semi = c[c["ID_Institucion"] == str(id_inst)]
    if _has_column(c, "Tipo_Estudiante_Costo"):
        semi = semi[semi["Tipo_Estudiante_Costo"] == str(tipo_est)]
    if _has_column(c, "Semestre_Vigencia (AAAA-S)"):
        semi = semi[semi["Semestre_Vigencia (AAAA-S)"] == str(semestre)]

    semi_prog = semi[semi["Programa_Costo"] == str(prog)] if _has_column(c, "Programa_Costo") else semi
    if not semi_prog.empty:
        row = semi_prog.iloc[0]
        return float(row["pct_contra"]), float(row["Cobro_EPP_num"])

    semi_todos = semi[semi["Programa_Costo"] == "Todos"] if _has_column(c, "Programa_Costo") else pd.DataFrame()
    if not semi_todos.empty:
        row = semi_todos.iloc[0]
        return float(row["pct_contra"]), float(row["Cobro_EPP_num"])

    by_inst = c[c["ID_Institucion"] == str(id_inst)]
    if not by_inst.empty:
        row = by_inst.iloc[0]
        pct = row["pct_contra"] if pd.notna(row["pct_contra"]) else 50.0
        epp = row["Cobro_EPP_num"] if pd.notna(row["Cobro_EPP_num"]) else 0
        return float(pct), float(epp)

    return 50.0, 0.0


def ejecutar_modelo(
    loader,
    semestre: str,
    total_estudiantes: int,
    programa_manual: str,
    tipo_est_manual: str,
    tipo_practica_manual: str,
    status_callback: Optional[Callable[[str], None]] = None,
) -> Dict:
    loader.validate_pesas()
    weights, _ = loader.get_ponderaciones_dict()
    _notify(status_callback, f"✓ {len(weights)} criterios cargados")

    _require_columns(loader.oferta, ["ID_Institucion"], "01_Oferta")
    _require_columns(loader.calidad, ["ID_Institucion"], "03_Calidad")
    _require_columns(loader.cupos, ["ID_Institucion", "Cupo_Estimado_Semestral"], "02_Oferta_x_Programa")
    _require_columns(
        loader.costos,
        ["ID_Institucion", "%_Contraprestacion_Matricula (0-100)", "Cobro_EPP (No cobra/Cobra a la Universidad)"],
        "04_Costo_del_Sitio",
    )

    loader.cupos["Cupo_Estimado_Semestral"] = pd.to_numeric(
        loader.cupos["Cupo_Estimado_Semestral"], errors="coerce"
    ).fillna(0).astype(int)

    if (loader.cupos["Cupo_Estimado_Semestral"] > 0).sum() == 0:
        _notify(status_callback, "⚠️ Plantilla sin cupos reales - usando datos de EJEMPLO")
        loader.cupos = generate_ejemplo_cupos(semestre)
        loader.costos = generate_ejemplo_costos(semestre)

    loader.costos = loader.costos.copy()
    loader.costos["Cobro_EPP_num"] = loader.costos[
        "Cobro_EPP (No cobra/Cobra a la Universidad)"
    ].map({"No cobra EPP": 0, "Cobra EPP a la Universidad": 1}).fillna(0)
    loader.costos["pct_contra"] = pd.to_numeric(
        loader.costos["%_Contraprestacion_Matricula (0-100)"], errors="coerce"
    )

    if loader.demanda is not None and not loader.demanda.empty and "Semestre" in loader.demanda.columns:
        demanda = loader.demanda[loader.demanda["Semestre"].astype(str) == str(semestre)].copy()
    else:
        demanda = generate_ejemplo_demanda(
            semestre=semestre,
            total_estudiantes=total_estudiantes,
            programa=programa_manual,
            tipo_estudiante=tipo_est_manual,
            tipo_practica=tipo_practica_manual,
        )

    if demanda.empty:
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

    groups = [
        (g["Programa"], g["Tipo_Estudiante"], g["Tipo_Practica"], g["Semestre"])
        for _, g in demanda.iterrows()
    ]
    demand_dict = {
        (g["Programa"], g["Tipo_Estudiante"], g["Tipo_Practica"], g["Semestre"]): int(g["Demanda_Estudiantes"])
        for _, g in demanda.iterrows()
    }

    cap_dict = {}
    for _, r in loader.cupos.iterrows():
        inst_id = str(r["ID_Institucion"])
        prog = str(r["Programa"]).strip() if ("Programa" in loader.cupos.columns and pd.notna(r["Programa"])) else ""
        tipo_est = str(r["Tipo_Estudiante (Pregrado/Posgrado)"]).strip() if ("Tipo_Estudiante (Pregrado/Posgrado)" in loader.cupos.columns and pd.notna(r["Tipo_Estudiante (Pregrado/Posgrado)"])) else ""
        sem = str(r["Semestre (AAAA-S)"]).strip() if ("Semestre (AAAA-S)" in loader.cupos.columns and pd.notna(r["Semestre (AAAA-S)"])) else ""

        cap_dict[(inst_id, prog or programa_manual, tipo_est or tipo_est_manual, sem or semestre)] = int(r["Cupo_Estimado_Semestral"])

    instituciones = [str(j) for j in loader.oferta["ID_Institucion"].dropna().unique().tolist()]

    base_raw = loader.oferta.merge(loader.calidad, on="ID_Institucion", how="left", suffixes=("", "_cal"))
    base = pd.DataFrame({"ID_Institucion": base_raw["ID_Institucion"]})
    rename_pairs = {
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
    for raw_col, norm_col in rename_pairs.items():
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
        S["Es_Hospital_Universitario_norm"] = pd.to_numeric(hosp_uni, errors="coerce").fillna(0).clip(0, 1).values

    if "Escenario_Avalado_Practicas" in loader.oferta.columns:
        esc = oferta_idx["Escenario_Avalado_Practicas"].reindex(s_ids, fill_value=0)
        S["Escenario_Avalado_Practicas_norm"] = pd.to_numeric(esc, errors="coerce").fillna(0).clip(0, 1).values

    if "Admiten_Docentes_Externos (Sí/No)" in loader.calidad.columns:
        adm = calidad_idx["Admiten_Docentes_Externos (Sí/No)"].reindex(s_ids, fill_value="No")
        adm_num = adm.astype(str).str.strip().str.lower().map({"sí": 1, "si": 1, "yes": 1, "1": 1, "true": 1}).fillna(0)
        S["Admiten_Docentes_Externos_norm"] = adm_num.values

    for col_raw, col_norm in [("Areas_Bienestar (0/1)", "Areas_Bienestar_norm"), ("Areas_Academicas (0/1)", "Areas_Academicas_norm")]:
        if col_raw in loader.calidad.columns:
            col_s = calidad_idx[col_raw].reindex(s_ids, fill_value=0)
            S[col_norm] = pd.to_numeric(col_s, errors="coerce").fillna(0).clip(0, 1).values

    weights_norm = {_normalize_weight_key(k): float(w) for k, w in weights.items()}

    missing_active_criteria = []
    for k in weights_norm.keys():
        if k in ["%_Contraprestacion_Matricula", "Cobro_EPP", "EPP_Exigidos"]:
            continue
        required_col = CRITERIA_REQUIRED_NORM_COLUMNS.get(k, f"{k}_norm")
        if required_col not in S.columns:
            missing_active_criteria.append(k)

    if missing_active_criteria:
        raise ValueError(
            "Faltan columnas fuente para criterios activos en 05_Ponderaciones: "
            f"{missing_active_criteria}. Ajusta ponderaciones o incluye esas columnas en 01_Oferta/03_Calidad."
        )

    V = {}
    count_factible = 0
    count_asignado = 0
    for j in instituciones:
        for g in groups:
            cap = cap_dict.get((j, g[0], g[1], g[3]), 0)
            if cap <= 0:
                continue
            count_factible += 1

            pct_contra, cobro_epp = _lookup_costo(loader.costos, j, g[0], g[1], g[2], g[3])
            count_asignado += 1

            contra_norm = 1.0 - float(pct_contra) / 100.0
            epp_norm = 1.0 - float(cobro_epp)

            score = 0.0
            for k, w in weights_norm.items():
                if w <= 0:
                    continue
                if k == "%_Contraprestacion_Matricula":
                    sk = contra_norm
                elif k in ["Cobro_EPP", "EPP_Exigidos"]:
                    sk = epp_norm
                elif k == "Admiten_Docentes_Externos":
                    sk = S.loc[j, "Admiten_Docentes_Externos_norm"] if "Admiten_Docentes_Externos_norm" in S.columns else 0.0
                else:
                    norm_col = f"{k}_norm"
                    sk = S.loc[j, norm_col] if norm_col in S.columns else 0.0
                    if pd.isna(sk):
                        sk = 0.0
                score += w * float(sk)
            V[(j, g)] = score

    _notify(status_callback, f"✓ Pares (j,g) para optimización: {len(V)}")

    optimizer = Optimizer(verbose=False)
    results_df = optimizer.optimize(V, demand_dict, cap_dict, instituciones, groups, semestre)

    if not results_df.empty and "Institucion" in loader.oferta.columns:
        oferta_names = loader.oferta[["ID_Institucion", "Institucion"]].copy()
        oferta_names["ID_Institucion"] = oferta_names["ID_Institucion"].astype(str)
        results_df["ID_Institucion"] = results_df["ID_Institucion"].astype(str)
        results_df = results_df.merge(oferta_names, on="ID_Institucion", how="left")
        friendly_cols = [
            "ID_Institucion",
            "Institucion",
            "Programa",
            "Tipo_Estudiante",
            "Tipo_Practica",
            "Semestre",
            "Asignados",
            "Score_unitario",
        ]
        results_df = results_df[[c for c in friendly_cols if c in results_df.columns]]

    if not results_df.empty and "Score_unitario" in results_df.columns:
        results_df["Score_unitario"] = pd.to_numeric(results_df["Score_unitario"], errors="coerce").round(4)

    total_demanda = int(sum(demand_dict.values()))
    total_asignado = int(results_df["Asignados"].sum()) if not results_df.empty else 0
    brecha = total_demanda - total_asignado
    tasa_cobertura = (total_asignado / total_demanda * 100) if total_demanda > 0 else 0.0

    if not results_df.empty:
        summary = results_df.groupby(["Programa", "Tipo_Estudiante", "Tipo_Practica"])["Asignados"].sum().reset_index()
        summary.columns = ["Programa", "Tipo_Estudiante", "Tipo_Practica", "Asignados"]
        summary["Demanda"] = summary.apply(
            lambda row: demand_dict.get((row["Programa"], row["Tipo_Estudiante"], row["Tipo_Practica"], semestre), 0),
            axis=1,
        )
        summary["Gap"] = summary["Demanda"] - summary["Asignados"]

        util = results_df.groupby("ID_Institucion")["Asignados"].sum().reset_index()
        util.columns = ["ID_Institucion", "Estudiantes_Asignados"]
        util["Capacidad"] = util["ID_Institucion"].apply(lambda jid: sum(v for k, v in cap_dict.items() if k[0] == jid))
        util["Capacidad"] = pd.to_numeric(util["Capacidad"], errors="coerce").fillna(0)
        util["Utilización_%"] = np.where(
            util["Capacidad"] > 0,
            (util["Estudiantes_Asignados"] / util["Capacidad"] * 100).round(1),
            0.0,
        )
        if "Institucion" in results_df.columns:
            util = util.merge(results_df[["ID_Institucion", "Institucion"]].drop_duplicates(), on="ID_Institucion", how="left")
    else:
        summary = pd.DataFrame()
        util = pd.DataFrame()

    return {
        "asignaciones": results_df,
        "summary": summary,
        "util": util,
        "total_demanda": total_demanda,
        "total_asignado": total_asignado,
        "brecha": brecha,
        "tasa_cobertura": tasa_cobertura,
        "obj_value": optimizer.get_objective_value(),
        "debug": {
            "instituciones": len(instituciones),
            "grupos": len(groups),
            "pares_factibles": count_factible,
            "pares_con_costo": count_asignado,
            "criterios": len(weights_norm),
        },
    }
