# 📊 Modelo de Optimización - Asignación de Estudiantes

Sistema completo para la optimización de asignación de estudiantes a escenarios de práctica usando programación lineal entera mixta (MILP).

## 🎯 Características

✅ **Optimización inteligente** de asignaciones basada en múltiples criterios  
✅ **Interfaz web** con Streamlit (upload y visualización)  
✅ **10 criterios ponderables** (beneficios y costos)  
✅ **Generación de datos de ejemplo** cuando falta información  
✅ **Análisis de capacidad** y detección de brechas  
✅ **Logging y debug** automático  
✅ **Estructura modular** y mantenible  

---

## 📁 Estructura del Proyecto

```
modelo_opt_oficina_practicas/
├── app.py                          # Aplicación Streamlit principal
├── requirements.txt                # Dependencias Python
├── README.md                       # Este archivo
│
├── src/                           # Código fuente
│   ├── core/                      # Lógica de optimización
│   │   ├── __init__.py
│   │   ├── data_loader.py        # Cargador de datos Excel
│   │   ├── calculator.py          # Cálculo de scores
│   │   └── optimizer.py           # Modelo MILP
│   │
│   ├── utils/                     # Funciones utilitarias
│   │   └── __init__.py            # Logging y helpers
│   │
│   └── visualization/             # Componentes Streamlit
│       └── __init__.py            # Gráficos y tablas
│
├── data/                          # Datos
│   ├── #Plantilla_V3_FacSalud.xlsx
│   ├── uploads/                   # Archivos subidos por usuarios
│   └── outputs/                   # Resultados generados
│
├── scripts/                       # Scripts de CLI
│   ├── modelo_v1.py              # Versión CLI del modelo
│   └── [otros scripts]
│
├── logs/                          # Logs de ejecución
├── debug_logs/                    # Logs de debug
│
├── ANÁLISIS_RESULTADOS.md        # Análisis detallado
└── GUÍA_LLENADO_PLANTILLA.md    # Cómo llenar Excel
```

---

## 🚀 Instalación

### 1. Requisitos previos
- Python 3.9+
- pip o conda

### 2. Clonar/Descargar proyecto
```bash
cd /Users/juanmanuelarias/Documents/trabajo/javeriana/modelo_opt_oficina_practicas
```

### 3. Crear entorno virtual (recomendado)
```bash
python -m venv venv

# Activar en macOS/Linux
source venv/bin/activate

# O en Windows
venv\Scripts\activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## 🎬 Uso

### Opción 1: Interfaz Web (Streamlit) - RECOMENDADO

```bash
streamlit run app.py
```

Abre en tu navegador: http://localhost:8501

**Pasos:**
1. Sube tu plantilla Excel V3
2. Configura Set de Ponderaciones y Semestre
3. Haz clic en "Ejecutar Optimización"
4. Visualiza resultados y descárgalos

### Opción 2: Línea de Comandos

```bash
python scripts/modelo_v1.py
```

Genera salida en consola con asignaciones y análisis.

---

## 📊 Qué hace el modelo

### Entrada (Excel V3)
- **01_Oferta**: Instituciones + servicios
- **02_Oferta_x_Programa**: Cupos disponibles
- **03_Calidad**: Criterios de calidad
- **04_Costo_del_Sitio**: Costos (contraprestación, EPP)
- **05_Ponderaciones**: Pesos de criterios
- **Demanda**: Estudiantes a ubicar (opcional)

### Proceso
```
Datos → Normalización → Cálculo de Scores → Optimización MILP → Resultados
  ↓          ↓                ↓                    ↓              ↓
Excel    Escala 0-1    V(j,g) ponderado   Max utilidad      Asignaciones
```

### Salida
- Tabla de asignaciones (institución × grupo × cantidad)
- Análisis de utilización de capacidad
- Comparación demanda vs cobertura
- Recomendaciones si hay brechas

---

## 🔧 Configuración

### Variables de entorno (opcional)
Crear archivo `.env`:
```
SET_ID=SET001
SEMESTRE=2026-1
LOG_LEVEL=INFO
```

---

##✅ Checklist: Preparar la Plantilla

- [ ] Completar `02_Oferta_x_Programa` con cupos reales
- [ ] Verificar `04_Costo_del_Sitio` tiene costos
- [ ] (Opcional) Crear hoja `Demanda Pregrado/Posgrado`
- [ ] Verificar `05_Ponderaciones` suma de pesos = 1.0
- [ ] Datos en `01_Oferta` y `03_Calidad` completos

Ver detalles en: `GUÍA_LLENADO_PLANTILLA.md`

---

## 📈 Ejemplo de Uso

```python
from src.core import DataLoader, Optimizer, ScoreCalculator

# 1. Cargar datos
loader = DataLoader("data/Plantilla_V3.xlsx", set_id="SET001", semestre="2026-1")
loader.load_all()

# 2. Validar
loader.validate_pesas()

# 3. Procesar y optimizar
# (ver app.py para flujo completo)
```

---

## 🐛 Debug y Logs

### Ver logs
```bash
tail -f logs/modelo_*.log
tail -f debug_logs/debug_*.log
```

### Environment de debug
En `app.py`, cambiar:
```python
optimizer = Optimizer(verbose=True)  # Muestra más detalles
```

---

## 📝 Documentación Adicional

- **[ANÁLISIS_RESULTADOS.md](ANÁLISIS_RESULTADOS.md)** - Interpretación de resultados
- **[GUÍA_LLENADO_PLANTILLA.md](GUÍA_LLENADO_PLANTILLA.md)** - Cómo llenar Excel

---

## 🤝 Contribuir / Reportar Issues

Si encuentras problemas:
1. Revisa los logs en `debug_logs/`
2. Verifica estructura de datos en Excel
3. Asegúrate que `.env` está correcto

---

## 📞 Soporte

Para preguntas técnicas ver:
- Módulos en `src/core/` - documentación inline
- Ejemplos en `scripts/`

---

## 📄 Licencia

Desarrollado para Facultad de Salud - Universidad Javeriana, 2026.

---

**Última actualización**: 20 de febrero de 2026  
**Versión**: 2.0 (con Streamlit)
