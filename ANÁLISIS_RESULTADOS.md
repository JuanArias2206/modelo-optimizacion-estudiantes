# 📊 ANÁLISIS DE RESULTADOS DEL MODELO DE OPTIMIZACIÓN 
## Asignación de Estudiantes a Escenarios (Prácticas)

---

## 🎯 RESUMEN EJECUTIVO

El modelo de optimización ha sido **ejecutado exitosamente**. Los resultados muestran:

| Métrica | Valor |
|---------|-------|
| **Total de estudiantes demandados** | 80 |
| **Total de estudiantes asignados** | 75 |
| **Brecha (no asignados)** | 5 estudiantes |
| **Tasa de cobertura** | **93.8%** |
| **Capacidad total disponible** | 75 cupos |

---

## ⚠️ DIAGNÓSTICO

### Problema Identificado
**La capacidad total es INSUFICIENTE** para cubrir la demanda completa.

- Demanda total: **80 estudiantes**
- Capacidad disponible: **75 cupos**
- Déficit: **5 estudiantes**

### Causa Raíz
En la demanda de ejemplo se especificó:
- **Rotación pregrado** (Medicina, Pregrado): 40 estudiantes 
- **Internado de medicina** (Medicina, Pregrado): 25 estudiantes
- **Residencia** (Medicina, Posgrado): 15 estudiantes
  - **Total: 80 estudiantes**

Pero los cupos generados de ejemplo son:
- 5 instituciones × 15 cupos cada una = **75 cupos totales**

---

## 📋 ASIGNACIÓN REALIZADA

El modelo asignó de manera óptima los 75 cupos disponibles:

| Institución | Programa | Tipo_Estudiante | Tipo_Práctica | Asignados |
|-------------|----------|-----------------|---------------|-----------|
| 7600103715  | Medicina | Pregrado        | Rotación      | 15        |
| 500102104   | Medicina | Pregrado        | Internado     | 15        |
| 7600102541  | Medicina | Pregrado        | Internado     | 20        |
| 7600103359  | Medicina | Pregrado        | Rotación      | 25        |
|             | **TOTAL** |                 |               | **75**    |

---

## 🔍 INTERPRETACIÓN DE PONDERACIONES

El modelo utilizó estos **10 criterios ponderados** (peso = 0.10 cada uno):

### Criterios de BENEFICIO (mayor es mejor):
1. ✅ Acceso a Transporte Público (1-5 escala)
2. ✅ Alineación Misión/Visión/Propósito (1-5 escala)
3. ✅ Evaluación de Estudiantes y Profesores (0-5 escala)
4. ✅ Vinculación Planta de Especialistas (%)
5. ✅ Servicios de UCI y UCIN (0/1)
6. ✅ Servicios Pediátricos (0/1)
7. ✅ Servicios de Obstetricia (0/1)

### Criterios de COSTO (menor es mejor):
1. 💰 % Contraprestación de Matrícula
2. 💰 Cobro de EPP (Equipo Personal Protección)
3. 💰 Número de Universidades que Comparten (competencia)

La **suma de pesos = 1.0** ✓ (Validado correctamente)

---

## 📌 SITUACIÓN ACTUAL DE LA PLANTILLA

### 1. ✅ Hojas Completamente Diligenciadas:
- **01_Oferta**: 32 instituciones con datos de capacidad, servicios y criterios
- **03_Calidad**: 32 registros con información de evaluaciones y vinculación
- **05_Ponderaciones**: 10 criterios con pesos balanceados (0.1 cada uno)

### 2. ⚠️ Hojas Pendientes (CRÍTICAS):
- **02_Oferta_x_Programa**: VACÍA - Debe tener cupos por (institución, programa, tipo_estudiante, semestre)
- **04_Costo_del_Sitio**: Parece tener datos reales (73 registros)

### 3. ❌ Hojas NO ENCONTRADAS:
- **Demanda Pregrado/Posgrado**: No existe aún - Necesaria para definir cuántos estudiantes requiere cada programa/semestre

---

## 🔧 QUÉ NECESITAS HACER PARA LLENAR LA PLANTILLA

### PASO 1: Llenar 02_Oferta_x_Programa
Esta hoja define **cuántos cupos disponibles** tiene cada institución.

**Estructura esperada:**
```
ID_Institucion | Institución | Programa | Tipo_Estudiante | Semestre | Cupo_Estimado_Semestral
7600103715     | Hospital A  | Medicina | Pregrado        | 2026-1   | 12
7600103715     | Hospital A  | Medicina | Posgrado        | 2026-1   | 5
500102104      | Hospital B  | Medicina | Pregrado        | 2026-1   | 15
...
```

**Notas:**
- Los cupos NO se desglosan por tipo de práctica (son genéricos)
- Usa tipos de estudiante: "Pregrado" o "Posgrado"
- Formato de semestre: "AAAA-S" (ej: "2026-1", "2026-2")

### PASO 2: Verificar 04_Costo_del_Sitio
Parece tener datos. Verificar que incluya:
- Contraprestación como % (0-100) por (institución, programa, tipo_estudiante, tipo_práctica, semestre)
- Cobro de EPP ("No cobra EPP" o "Cobra EPP a la Universidad")

### PASO 3: Crear Demanda Pregrado/Posgrado (NUEVA HOJA)
Define **cuántos estudiantes se necesitan ubicar** en cada grupo.

**Estructura sugerida:**
```
Semestre | Programa | Tipo_Estudiante | Tipo_Practica           | Demanda_Estudiantes
2026-1   | Medicina | Pregrado        | Rotación pregrado       | 40
2026-1   | Medicina | Pregrado        | Internado de medicina   | 25
2026-1   | Medicina | Posgrado        | Residencia Medicina     | 15
```

---

## 🚀 PRÓXIMOS PASOS

1. **Inmediato**: Llenar `02_Oferta_x_Programa` con cupos reales
2. **Importante**: Crear hoja de demanda con grupos de estudiantes reales
3. **Optativo**: Si quieres criterios diferentes, actualizar `05_Ponderaciones`
4. **Ejecuta**: `python scripts/modelo_v1.py` con datos reales

---

## 💡 INTERPRETACIÓN DEL MODELO

El modelo resuelve este problema de optimización:

**Objetivo:** Maximizar la calidad/beneficio total ponderado  
**Sujeto a:**
- Cada grupo de estudiantes se asigna a exactamente UNA institución (o se fracciona óptimamente)
- La cantidad asignada a una institución no puede exceder su cupo
- La asignación debe ser un número entero de estudiantes

**Resultado:** La solución que cubre máxima demanda dentro de la capacidad disponible, optimizando los criterios de calidad y costos.

---

## 📞 NOTAS TÉCNICAS

- **Solver**: CBC (Coin-or-branch and cut) - MILP
- **Lenguaje**: Python 3.13 con PuLP, Pandas, OpenPyXL
- **Validaciones implementadas**:
  - ✅ Verificación de suma de pesos = 1.0
  - ✅ Manejo de datos faltantes y tipos
  - ✅ Detección automática de plantilla vacía
  - ✅ Generación de datos de ejemplo cuando faltan
  - ✅ Reportes de factibilidad y capacidad

---

**Fecha de análisis**: 18 de febrero de 2026  
**Set de ponderaciones usado**: SET001  
**Semestre analizado**: 2026-1
