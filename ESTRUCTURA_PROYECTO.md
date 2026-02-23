```
modelo_opt_oficina_practicas/
│
├── 🎯 app.py ............................ APLICACIÓN STREAMLIT (punto de entrada)
├── requirements.txt .................... Dependencias Python
├── README.md ........................... Documentación completa
├── INICIO_RAPIDO.md .................... Referencia rápida
├── ANÁLISIS_RESULTADOS.md .............. Análisis de ejemplo
├── GUÍA_LLENADO_PLANTILLA.md ........... Cómo llenar Excel
├── .gitignore .......................... Archivos a ignorar en Git
│
│
├── 📁 src/ ............................. CÓDIGO MODULAR
│   │
│   ├── core/ .......................... LÓGICA DE OPTIMIZACIÓN
│   │   ├── __init__.py
│   │   ├── data_loader.py ............ 📥 Cargador de Excel
│   │   │                              • Lee hojas: Oferta, Calidad, Cupos, Costos, Ponderaciones
│   │   │                              • Valida pesos
│   │   │                              • Detecta datos de ejemplo
│   │   │
│   │   ├── calculator.py ............ 📊 Normalizador de criterios
│   │   │                              • Normaliza escala 1-5, 0-5, 0-100
│   │   │                              • Calcula beneficios vs costos
│   │   │                              • Maneja servicios binarios
│   │   │
│   │   └── optimizer.py ............ 🔧 Resolvedor MILP
│   │                                  • Crea variables de decisión
│   │                                  • Define restricciones
│   │                                  • Usa solver CBC de PuLP
│   │                                  • Retorna asignaciones óptimas
│   │
│   ├── utils/ ......................... FUNCIONES UTILITARIAS
│   │   └── __init__.py .............. 📝 Logging y helpers
│   │                                  • setup_logging()
│   │                                  • save_results_json()
│   │
│   └── visualization/ ................. COMPONENTES STREAMLIT
│       └── __init__.py .............. 🎨 Renderizadores UI
│                                      • render_header()
│                                      • render_upload_section()
│                                      • render_results_summary()
│                                      • render_charts()
│
│
├── 📊 data/ ............................ DATOS
│   ├── Plantilla_V3_FacSalud.xlsx ..... Base de plantilla (tu archivo principal)
│   ├── uploads/ ....................... 📤 Archivos subidos por usuarios
│   │   └── .gitkeep
│   │
│   └── outputs/ ....................... 📥 Resultados generados
│       └── .gitkeep
│
│
├── 📝 scripts/ ......................... SCRIPTS DE CLI (legacy)
│   └── modelo_v1.py ................... Versión línea de comandos
│
│
├── 📋 logs/ ............................ REGISTROS DE EJECUCIÓN
│   ├── .gitkeep
│   └── modelo_YYYYMMDD_HHMMSS.log .... Se generan aquí
│
│
└── 🐛 debug_logs/ ..................... LOGS DE DEBUG
    ├── .gitkeep
    └── debug_YYYYMMDD_HHMMSS.log .... Se generan aquí


═══════════════════════════════════════════════════════════════════════════════

ARCHIVOS NUEVOS CREADOS:

✅ src/core/__init__.py
✅ src/core/data_loader.py
✅ src/core/calculator.py
✅ src/core/optimizer.py
✅ src/utils/__init__.py
✅ src/visualization/__init__.py
✅ app.py (🎯 APLICACIÓN STREAMLIT)
✅ requirements.txt
✅ README.md
✅ INICIO_RAPIDO.md
✅ .gitignore
✅ logs/.gitkeep
✅ debug_logs/.gitkeep
✅ data/uploads/.gitkeep
✅ data/outputs/.gitkeep


═══════════════════════════════════════════════════════════════════════════════

CÓMO EJECUTAR:

1. Terminal:
   cd /Users/juanmanuelarias/Documents/trabajo/javeriana/modelo_opt_oficina_practicas

2. Activar entorno:
   source venv/bin/activate

3. Instalar dependencias (primera vez):
   pip install -r requirements.txt

4. EJECUTAR APP:
   streamlit run app.py

5. Se abrirá en: http://localhost:8501


═══════════════════════════════════════════════════════════════════════════════

FUNCIONALIDADES POR MÓDULO:

┌─────────────────────────────────────────────────────────────────────────┐
│ app.py (APLICACIÓN PRINCIPAL)                                           │
├─────────────────────────────────────────────────────────────────────────┤
│ ✅ Upload de Excel                                                       │
│ ✅ Configuración (Set ID, Semestre)                                      │
│ ✅ Generación automática de datos de ejemplo                             │
│ ✅ Ejecución de optimización                                             │
│ ✅ Visualización de resultados:                                          │
│    • Resumen executivo (métricas)                                        │
│    • Tabla de asignaciones                                               │
│    • Gráfico de demanda vs asignación                                    │
│    • Gráfico de capacidad utilizada                                      │
│ ✅ Descarga de resultados (CSV)                                          │
│ ✅ Secciones: Entrada, Resultados, Ayuda                                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ src/core/data_loader.py (CARGA DE DATOS)                                │
├─────────────────────────────────────────────────────────────────────────┤
│ class DataLoader:                                                        │
│   ✅ load_all()           → Carga todas las hojas                         │
│   ✅ validate_pesas()     → Valida suma = 1.0                            │
│   ✅ get_ponderaciones_dict() → Retorna pesos y tipos                    │
│   ✅ has_cupos_data()     → Detecta si hay datos reales                  │
│   ✅ has_costos_data()    → Detecta si hay costos reales                 │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ src/core/calculator.py (NORMALIZACIÓN DE CRITERIOS)                     │
├─────────────────────────────────────────────────────────────────────────┤
│ class ScoreCalculator:                                                   │
│   ✅ norm_1_5()           → Normaliza 1-5 → 0-1                          │
│   ✅ norm_0_5()           → Normaliza 0-5 → 0-1                          │
│   ✅ norm_pct()           → Normaliza % → 0-1                            │
│   ✅ minmax_cost()        → Normaliza costos (menor es mejor)            │
│   ✅ minmax_benefit()     → Normaliza beneficios (mayor es mejor)        │
│   ✅ normalize_criteria() → Normaliza TODO                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ src/core/optimizer.py (OPTIMIZACIÓN MILP)                               │
├─────────────────────────────────────────────────────────────────────────┤
│ class Optimizer:                                                         │
│   ✅ optimize()           → Resuelve modelo MILP                         │
│                              • Crea variables x(j,g)                     │
│                              • Maximiza ∑score · x(j,g)                  │
│                              • Restricción: ∑x(j,g) = demanda            │
│                              • Restricción: ∑x ≤ capacidad               │
│   ✅ get_objective_value() → Retorna valor óptimo                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ src/visualization/__init__.py (INTERFAZ STREAMLIT)                      │
├─────────────────────────────────────────────────────────────────────────┤
│ ✅ render_header()              → Título y logo                          │
│ ✅ render_upload_section()      → Area de upload de Excel                │
│ ✅ render_config_section()      → Inputs: Set ID, Semestre               │
│ ✅ render_results_summary()     → Métricas principales                   │
│ ✅ render_asignaciones_table()  → Tabla de resultados                    │
│ ✅ render_capacidad_chart()     → Gráfico de utilización                 │
│ ✅ render_demanda_vs_asignacion() → Gráfico comparativo                  │
│ ✅ render_debug_info()          → Panel de debug                         │
└─────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════

FLUJO DE DATOS:

Excel (V3) 
    ↓
DataLoader.load_all() ─── Lee 5 hojas
    ↓
Excel → DataFrames
    ↓
    ├─→ DataLoader.validate_pesas() → Suma = 1.0 ✓
    ├─→ DataLoader.get_ponderaciones_dict() → {criterio: peso}
    │
    └─→ Merge(Oferta + Calidad)
            ↓
        ScoreCalculator.normalize_criteria()
            ├─→ Escala 1-5 → 0-1
            ├─→ Escala 0-5 → 0-1
            ├─→ Pct 0-100 → 0-1
            └─→ Costos (inversión)
            ↓
        Cálculo V(j,g) = ∑pesos · criterios_normalizados
            ↓
        Optimizer.optimize(V, demanda, cupos)
            ├─→ Variables: x(j,g) ∈ Z≥0
            ├─→ Maximize: ∑V(j,g)·x(j,g)
            ├─→ Restricciones:
            │   • ∑x(j,g) = demanda(g)
            │   • ∑x ≤ capacidad(j,p,n,s)
            │
            └─→ Solver CBC
                    ↓
                Asignaciones Óptimas
                    ↓
            RESULTADOS:
            • Tabla de asignaciones
            • Utilización de capacidad
            • Análisis de brecha


═══════════════════════════════════════════════════════════════════════════════

DATOS DE ENTRADA ESPERADOS (Excel):

HOJA | DESCRIPCIÓN                 | REQUERIDO | ESTADO
────────────────────────────────────────────────────────
01   | Oferta (instituciones)      | SÍ        | ✓ Llena
02   | Cupos (capacidad)           | SÍ        | ⚠️ Vacía
03   | Calidad (criterios)         | SÍ        | ✓ Llena
04   | Costos (contraprestación)   | SÍ        | ⚠️ Verificar
05   | Ponderaciones (pesos)       | SÍ        | ✓ Llena
NEW  | Demanda (estudiantes)       | OPT       | ❌ No existe


═══════════════════════════════════════════════════════════════════════════════

CARPETAS CREADAS:

📁 src/
   ├── core/      → Lógica de optimización
   ├── utils/     → Funciones utilitarias
   └── visualization/ → Componentes Streamlit

📁 data/
   ├── uploads/   → Archivos que subes
   └── outputs/   → Resultados generados

📁 logs/          → Registros de app
📁 debug_logs/    → Registros de debug

```

---

**Estructura completada ✅**  
**Listo para usar: `streamlit run app.py`**
