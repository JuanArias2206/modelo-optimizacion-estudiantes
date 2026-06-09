# Graph Report - .  (2026-06-03)

## Corpus Check
- Corpus is ~13,690 words - fits in a single context window. You may not need a graph.

## Summary
- 147 nodes · 167 edges · 22 communities (13 shown, 9 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Main Application Logic|Main Application Logic]]
- [[_COMMUNITY_Project Overview|Project Overview]]
- [[_COMMUNITY_Data Loading Module|Data Loading Module]]
- [[_COMMUNITY_Streamlit UI Components|Streamlit UI Components]]
- [[_COMMUNITY_MILP Optimizer|MILP Optimizer]]
- [[_COMMUNITY_PPTX Generator|PPTX Generator]]
- [[_COMMUNITY_Score Calculator|Score Calculator]]
- [[_COMMUNITY_Utility Functions|Utility Functions]]
- [[_COMMUNITY_Data Validation|Data Validation]]
- [[_COMMUNITY_Min-Max Benefit|Min-Max Benefit]]
- [[_COMMUNITY_Score Normalization|Score Normalization]]
- [[_COMMUNITY_Norm Percentage|Norm Percentage]]
- [[_COMMUNITY_Norm 0-5|Norm 0-5]]
- [[_COMMUNITY_Norm 1-5|Norm 1-5]]
- [[_COMMUNITY_Min-Max Cost|Min-Max Cost]]
- [[_COMMUNITY_Core Init|Core Init]]
- [[_COMMUNITY_Dependencies|Dependencies]]

## God Nodes (most connected - your core abstractions)
1. `main()` - 14 edges
2. `DataLoader` - 11 edges
3. `procesar_datos()` - 10 edges
4. `Streamlit Application` - 8 edges
5. `CLI Optimization Model` - 7 edges
6. `create_presentation()` - 6 edges
7. `Optimizer` - 6 edges
8. `Data Loader` - 6 edges
9. `normalize_criteria()` - 5 edges
10. `add_textbox()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `Model Output Log` --references--> `CLI Optimization Model`  [EXTRACTED]
  salida_modelo.txt → scripts/modelo_v1.py
- `CLI Optimization Model` --semantically_similar_to--> `MILP Optimizer`  [INFERRED] [semantically similar]
  scripts/modelo_v1.py → src/core/optimizer.py
- `CLI Optimization Model` --semantically_similar_to--> `Score Calculator`  [INFERRED] [semantically similar]
  scripts/modelo_v1.py → src/core/calculator.py
- `Project README` --semantically_similar_to--> `Project Structure Documentation`  [INFERRED] [semantically similar]
  README.md → ESTRUCTURA_PROYECTO.md
- `procesar_datos()` --calls--> `lookup_costo()`  [INFERRED]
  app.py → scripts/modelo_v1.py

## Hyperedges (group relationships)
- **MILP Optimization Pipeline** — app, data_loader, calculator, optimizer [INFERRED 0.85]
- **Project Documentation Suite** — readme, estructura_proyecto, guia_llenado, analisis_resultados, inicio_rapido [EXTRACTED 0.90]
- **Debug and Diagnostic Suite** — debug_tipos, debug_merge, debug_cupos, diagnostico [INFERRED 0.80]

## Communities (22 total, 9 thin omitted)

### Community 0 - "Main Application Logic"
Cohesion: 0.10
Nodes (25): clean_criterio_codigo(), compute_scores_debug(), generar_excel_resultados(), generate_ejemplo_costos(), generate_ejemplo_cupos(), generate_ejemplo_demanda(), get_config_options_from_upload(), main() (+17 more)

### Community 1 - "Project Overview"
Cohesion: 0.12
Nodes (23): Results Analysis Document, Streamlit Application, Score Calculator, Data Loader, Debug Cupos Script, Debug Merge Script, Debug ID Types Script, Diagnostic Script (+15 more)

### Community 2 - "Data Loading Module"
Cohesion: 0.12
Nodes (10): DataLoader, Retorna Set_ID disponibles en la hoja de ponderaciones., Retorna semestres disponibles en ponderaciones., Verifica si hay datos reales en cupos., Carga y valida datos desde plantilla Excel V3, Verifica si hay datos reales en costos., Carga todos los datos necesarios. Retorna True si está completo., Valida que los pesos sumen 1.0. Retorna la suma. (+2 more)

### Community 3 - "Streamlit UI Components"
Cohesion: 0.11
Nodes (17): Componentes de visualización para Streamlit, Renderiza resumen de resultados, Renderiza encabezado de la aplicación, Renderiza tabla de asignaciones, Renderiza gráfico de utilización de capacidad, Renderiza comparación demanda vs asignación, Renderiza información de debug, Renderiza sección de upload (+9 more)

### Community 4 - "MILP Optimizer"
Cohesion: 0.15
Nodes (7): Cargador de datos desde plantilla Excel, Módulo principal: Corazón del modelo de optimización, Optimizer, Modelo de optimización MILP para asignación de estudiantes, Retorna el valor óptimo de la función objetivo, Ejecuta optimización MILP de asignación, Resuelve el problema de optimización.                  Parameters:         -----

### Community 5 - "PPTX Generator"
Cohesion: 0.24
Nodes (11): add_background(), add_bullet_list(), add_table(), add_textbox(), create_presentation(), Generador de presentación PPTX del Modelo de Optimización, Genera la presentación completa, Agrega fondo de color a una diapositiva (+3 more)

### Community 6 - "Score Calculator"
Cohesion: 0.29
Nodes (8): minmax_cost(), norm_0_5(), norm_1_5(), norm_pct(), normalize_criteria(), Calculador de scores normalizados para criterios, Calcula scores normalizados de criterios, ScoreCalculator

### Community 7 - "Utility Functions"
Cohesion: 0.25
Nodes (7): load_results_json(), Utilidades generales del proyecto, Configura logging para toda la aplicación, Guarda resultados en JSON, Carga resultados desde JSON, save_results_json(), setup_logging()

## Knowledge Gaps
- **10 isolated node(s):** `Debug ID Types Script`, `Debug Merge Script`, `Debug Cupos Script`, `Diagnostic Script`, `Visualization Components` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Main Application Logic` to `Data Loading Module`, `Streamlit UI Components`?**
  _High betweenness centrality (0.213) - this node is a cross-community bridge._
- **Why does `DataLoader` connect `Data Loading Module` to `Main Application Logic`, `MILP Optimizer`?**
  _High betweenness centrality (0.165) - this node is a cross-community bridge._
- **Why does `procesar_datos()` connect `Main Application Logic` to `MILP Optimizer`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `main()` (e.g. with `render_header()` and `render_upload_section()`) actually correct?**
  _`main()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `procesar_datos()` (e.g. with `lookup_costo()` and `Optimizer`) actually correct?**
  _`procesar_datos()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `Streamlit Application` (e.g. with `CLI Optimization Model` and `PPTX Presentation Generator`) actually correct?**
  _`Streamlit Application` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `CLI Optimization Model` (e.g. with `MILP Optimizer` and `Score Calculator`) actually correct?**
  _`CLI Optimization Model` has 4 INFERRED edges - model-reasoned connections that need verification._