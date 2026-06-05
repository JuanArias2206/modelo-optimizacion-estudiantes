import re

import pandas as pd

PERIOD_MAP = {
    "Segundo": 2,
    "Tercero": 3,
    "Cuarto": 4,
    "Quinto": 5,
    "Sexto": 6,
    "Séptimo": 7,
    "Octavo": 8,
    "Noveno": 9,
    "Décimo": 10,
    "Undécimo": 11,
    "Duodécimo": 12,
}

GROUP_CONSTRAINTS = {
    5: {"min": 4, "max": 7},
    6: {"min": 4, "max": 7},
    7: {"min": 4, "max": 7},
    8: {"min": 4, "max": 7},
    9: {"min": 3, "max": 5},
    10: {"min": 3, "max": 5},
    11: {"min": 3, "max": 5},
    12: {"min": 3, "max": 5},
}

EXCEL_PATH = "data/info_reunion_refinacion_modelo/Mapa de practica general Medicina 2025-1.xlsx"

REPS_PATTERN = re.compile(r"(\d{9,10})\s*-\s*\d{2}")


def get_group_constraints(semestre_plan: int) -> dict:
    return GROUP_CONSTRAINTS.get(semestre_plan, {"min": 0, "max": 999})


def parse_escenario(text: str) -> tuple[str, str, str]:
    if not isinstance(text, str):
        return ("", "", "")

    reps_match = REPS_PATTERN.search(text)
    id_institucion = reps_match.group(1) if reps_match else ""

    if "/" in text:
        parts = text.split("/", 1)
        institucion = parts[0].strip()
        remainder = parts[1]
        sede = REPS_PATTERN.sub("", remainder)
        sede = re.sub(r"\(.*?\)", "", sede)
        sede = sede.replace("\n", " ").strip()
    else:
        institucion = text.split("\n")[0].strip()
        sede = ""

    return id_institucion, institucion, sede


def parse_mapa_practica(path: str = EXCEL_PATH) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Hoja1", header=None)
    df = raw.iloc[2:].copy()
    df.columns = [0, 1, 2, 3, 4, 5]

    df[4] = pd.to_numeric(df[4], errors="coerce")
    df = df.dropna(subset=[4])

    df[0] = df[0].ffill()
    df[1] = df[1].ffill()
    df[2] = df[2].ffill()

    df = df[df[0].isin(PERIOD_MAP)]

    parsed = df[3].apply(parse_escenario)
    df["ID_Institucion"] = parsed.apply(lambda x: x[0])
    df["Institucion"] = parsed.apply(lambda x: x[1])
    df["Sede"] = parsed.apply(lambda x: x[2])

    result = pd.DataFrame({
        "Semestre_plan": df[0].map(PERIOD_MAP),
        "Asignatura": df[1].str.strip(),
        "Rotacion": df[2].str.strip(),
        "ID_Institucion": df["ID_Institucion"],
        "Institucion": df["Institucion"],
        "Sede": df["Sede"],
        "Cupo": df[4].astype(int),
    })

    result = result.reset_index(drop=True)
    return result


if __name__ == "__main__":
    df = parse_mapa_practica()
    print(f"Total rows: {len(df)}")
    print(f"\nRows by Semestre_plan:")
    print(df["Semestre_plan"].value_counts().sort_index())
    print(f"\nUnique institutions: {df['ID_Institucion'].nunique()}")
    print(f"Unique asignaturas: {df['Asignatura'].nunique()}")
    print(f"Total cupos: {df['Cupo'].sum()}")
    print(f"\nSample rows:")
    print(df.head(10).to_string(index=False))
    print(f"\nRows with empty ID_Institucion: {(df['ID_Institucion'] == '').sum()}")
