# Graph Report - .  (2026-06-10)

## Corpus Check
- Corpus is ~20,116 words - fits in a single context window. You may not need a graph.

## Summary
- 224 nodes · 257 edges · 35 communities (18 shown, 17 thin omitted)
- Extraction: 84% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_App Main Logic (compute, debug, excel)|App Main Logic (compute, debug, excel)]]
- [[_COMMUNITY_DataLoader and Rotation Queries|DataLoader and Rotation Queries]]
- [[_COMMUNITY_App Helpers and Processors|App Helpers and Processors]]
- [[_COMMUNITY_Core Package Init and DataLoader Class|Core Package Init and DataLoader Class]]
- [[_COMMUNITY_Streamlit Visualization Components|Streamlit Visualization Components]]
- [[_COMMUNITY_GroupOptimizer MILP|GroupOptimizer MILP]]
- [[_COMMUNITY_DataLoader DataFrames and Ponderaciones|DataLoader DataFrames and Ponderaciones]]
- [[_COMMUNITY_PPTX Presentation Generator|PPTX Presentation Generator]]
- [[_COMMUNITY_Score Normalization Functions (static)|Score Normalization Functions (static)]]
- [[_COMMUNITY_Project Documentation Suite|Project Documentation Suite]]
- [[_COMMUNITY_Utility Functions and JSON IO|Utility Functions and JSON IO]]
- [[_COMMUNITY_Numeric Helper to_float|Numeric Helper to_float]]
- [[_COMMUNITY_Norm 1-5 Function|Norm 1-5 Function]]
- [[_COMMUNITY_Norm 0-5 Function|Norm 0-5 Function]]
- [[_COMMUNITY_Norm Percentage Function|Norm Percentage Function]]
- [[_COMMUNITY_Min-Max Benefit Function|Min-Max Benefit Function]]
- [[_COMMUNITY_Min-Max Cost Function|Min-Max Cost Function]]
- [[_COMMUNITY_CLI Optimization Model (legacy)|CLI Optimization Model (legacy)]]
- [[_COMMUNITY_Refined Model Plan Document|Refined Model Plan Document]]
- [[_COMMUNITY_Load Results JSON Utility|Load Results JSON Utility]]
- [[_COMMUNITY_Save Results JSON Utility|Save Results JSON Utility]]
- [[_COMMUNITY_Setup Logging Utility|Setup Logging Utility]]
- [[_COMMUNITY_Map Practice Parser Function|Map Practice Parser Function]]
- [[_COMMUNITY_Documentation Project Overview|Documentation: Project Overview]]
- [[_COMMUNITY_Documentation Template Guide|Documentation: Template Guide]]
- [[_COMMUNITY_Documentation Quick Start|Documentation: Quick Start]]
- [[_COMMUNITY_Documentation Results Analysis|Documentation: Results Analysis]]
- [[_COMMUNITY_Documentation Project Structure|Documentation: Project Structure]]

## God Nodes (most connected - your core abstractions)
1. `main()` - 19 edges
2. `DataLoader` - 15 edges
3. `procesar_datos()` - 10 edges
4. `GroupOptimizer class (MILP with group size constraints)` - 8 edges
5. `GroupOptimizer` - 7 edges
6. `procesar_datos (Agregado mode)` - 7 edges
7. `procesar_refinado (Refinado mode)` - 7 edges
8. `DataLoader.load_all` - 7 edges
9. `create_presentation()` - 6 edges
10. `Optimizer` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Plan Task 1: scripts/parse_mapa_practica.py (Mapa de Práctica parser)` --conceptually_related_to--> `DataFrame 'rotaciones' (from sheet 06_Rotaciones or parser)`  [INFERRED]
  docs/superpowers/plans/2026-06-05-modelo-refinado-por-semestre.md → src/core/data_loader.py
- `Rationale: Group size constraints (semesters 5-8: 4-7 students; 9-12: 3-5 students) — pedagogical/administrative cohort limits per plan` --rationale_for--> `GroupOptimizer class (MILP with group size constraints)`  [INFERRED]
  docs/superpowers/plans/2026-06-05-modelo-refinado-por-semestre.md → src/core/optimizer.py
- `CLI Optimization Model` --semantically_similar_to--> `Score Calculator`  [INFERRED] [semantically similar]
  scripts/modelo_v1.py → src/core/calculator.py
- `Project README` --semantically_similar_to--> `Project Structure Documentation`  [INFERRED] [semantically similar]
  README.md → ESTRUCTURA_PROYECTO.md
- `Plan Task 4: Streamlit app.py 'Refinado por semestre' mode` --references--> `DataLoader.get_ponderaciones_dict`  [EXTRACTED]
  docs/superpowers/plans/2026-06-05-modelo-refinado-por-semestre.md → src/core/data_loader.py

## Hyperedges (group relationships)
- **Debug and Diagnostic Suite** — debug_tipos, debug_merge, debug_cupos, diagnostico [INFERRED 0.80]
- **Project Documentation Suite** — readme, estructura_proyecto, guia_llenado, analisis_resultados, inicio_rapido [EXTRACTED 0.90]

## Communities (35 total, 17 thin omitted)

### Community 0 - "App Main Logic (compute, debug, excel)"
Cohesion: 0.09
Nodes (32): clean_criterio_codigo(), _compute_scores(), compute_scores_debug(), generar_excel_resultados(), generate_ejemplo_costos(), generate_ejemplo_cupos(), generate_ejemplo_demanda(), get_config_options_from_upload() (+24 more)

### Community 1 - "DataLoader and Rotation Queries"
Cohesion: 0.07
Nodes (16): DataLoader, Cargador de datos desde plantilla Excel, Valida que los pesos sumen 1.0. Retorna la suma., Retorna (pesos, tipos) de criterios para set_id y semestre., Carga y valida datos desde plantilla Excel V3, Retorna Set_ID disponibles en la hoja de ponderaciones., Retorna semestres disponibles en ponderaciones., Verifica si hay datos reales en cupos. (+8 more)

### Community 2 - "App Helpers and Processors"
Cohesion: 0.14
Nodes (24): clean_criterio_codigo (normalize criterion code), _compute_scores (helper), generar_excel_resultados (multi-sheet export), lookup_costo nested function (3-level cost fallback), main() entry point, MILP Mathematical Model Documentation, procesar_datos (Agregado mode), procesar_refinado (Refinado mode) (+16 more)

### Community 3 - "Core Package Init and DataLoader Class"
Cohesion: 0.14
Nodes (20): src.core package public API (DataLoader, Optimizer, GroupOptimizer, ScoreCalculator), DataLoader class, DataLoader.get_asignaturas_rotaciones, DataLoader.get_ips_for_rotacion, DataLoader.get_rotaciones_dict, DataLoader.load_rotaciones, DataFrame 'rotaciones' (from sheet 06_Rotaciones or parser), GroupOptimizer class (MILP with group size constraints) (+12 more)

### Community 4 - "Streamlit Visualization Components"
Cohesion: 0.11
Nodes (17): Componentes de visualización para Streamlit, Renderiza resumen de resultados, Renderiza encabezado de la aplicación, Renderiza tabla de asignaciones, Renderiza gráfico de utilización de capacidad, Renderiza comparación demanda vs asignación, Renderiza información de debug, Renderiza sección de upload (+9 more)

### Community 5 - "GroupOptimizer MILP"
Cohesion: 0.13
Nodes (7): GroupOptimizer, Optimizer, Modelo de optimización MILP para asignación de estudiantes, Retorna el valor óptimo de la función objetivo, Optimización con grupos de tamaño controlado por semestre., Ejecuta optimización MILP de asignación, Resuelve el problema de optimización.                  Parameters:         -----

### Community 6 - "DataLoader DataFrames and Ponderaciones"
Cohesion: 0.17
Nodes (13): DataLoader._to_float (static helper), DataFrame 'calidad' (from sheet 03_Calidad), DataFrame 'costos' (from sheet 04_Costo_del_Sitio), DataFrame 'cupos' (from sheet 02_Oferta_x_Programa), DataLoader.get_ponderaciones_dict, DataLoader.has_costos_data, DataLoader.has_cupos_data, DataLoader.load_all (+5 more)

### Community 7 - "PPTX Presentation Generator"
Cohesion: 0.24
Nodes (11): add_background(), add_bullet_list(), add_table(), add_textbox(), create_presentation(), Generador de presentación PPTX del Modelo de Optimización, Genera la presentación completa, Agrega fondo de color a una diapositiva (+3 more)

### Community 8 - "Score Normalization Functions (static)"
Cohesion: 0.29
Nodes (8): minmax_cost(), norm_0_5(), norm_1_5(), norm_pct(), normalize_criteria(), Calculador de scores normalizados para criterios, Calcula scores normalizados de criterios, ScoreCalculator

### Community 9 - "Project Documentation Suite"
Cohesion: 0.22
Nodes (10): Results Analysis Document, Score Calculator, Project Structure Documentation, Template Filling Guide, Quick Start Guide, CLI Optimization Model, Multicriteria Scoring System, Project README (+2 more)

### Community 10 - "Utility Functions and JSON IO"
Cohesion: 0.25
Nodes (7): load_results_json(), Utilidades generales del proyecto, Configura logging para toda la aplicación, Guarda resultados en JSON, Carga resultados desde JSON, save_results_json(), setup_logging()

## Ambiguous Edges - Review These
- `lookup_costo nested function (3-level cost fallback)` → `clean_criterio_codigo (normalize criterion code)`  [AMBIGUOUS]
  app.py · relation: semantically_similar_to

## Knowledge Gaps
- **23 isolated node(s):** `PPTX Presentation Generator`, `Debug ID Types Script`, `Debug Merge Script`, `Debug Cupos Script`, `Diagnostic Script` (+18 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `lookup_costo nested function (3-level cost fallback)` and `clean_criterio_codigo (normalize criterion code)`?**
  _Edge tagged AMBIGUOUS (relation: semantically_similar_to) - confidence is low._
- **Why does `main()` connect `App Main Logic (compute, debug, excel)` to `DataLoader and Rotation Queries`, `Streamlit Visualization Components`?**
  _High betweenness centrality (0.150) - this node is a cross-community bridge._
- **Why does `DataLoader` connect `DataLoader and Rotation Queries` to `App Main Logic (compute, debug, excel)`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `procesar_datos()` connect `App Main Logic (compute, debug, excel)` to `GroupOptimizer MILP`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `main()` (e.g. with `render_header()` and `render_upload_section()`) actually correct?**
  _`main()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `procesar_datos()` (e.g. with `lookup_costo()` and `Optimizer`) actually correct?**
  _`procesar_datos()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `GroupOptimizer class (MILP with group size constraints)` (e.g. with `Optimizer.optimize` and `Rationale: Group size constraints (semesters 5-8: 4-7 students; 9-12: 3-5 students) — pedagogical/administrative cohort limits per plan`) actually correct?**
  _`GroupOptimizer class (MILP with group size constraints)` has 3 INFERRED edges - model-reasoned connections that need verification._