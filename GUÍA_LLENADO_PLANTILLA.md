# 📖 GUÍA DE LLENADO DE PLANTILLA - Modelo de Optimización de Prácticas

## Resumen de lo que necesitas hacer:

Tu plantilla Excel V3 tiene algunas hojas llenas y otras vacías. El modelo necesita que completes:

1. **02_Oferta_x_Programa** ← CRÍTICA (está vacía)
2. **04_Costo_del_Sitio** ← Verificar datos  
3. **Nueva hoja: Demanda Pregrado/Posgrado** ← A crear

---

## 1️⃣ LLENAR: 02_Oferta_x_Programa

### ¿Qué es?
Define **cuántos cupos (capacidad) ofrece cada institución** para cada programa y tipo de estudiante, por semestre.

### Estructura de columnas:
```
A: ID_Institucion      (número NIT o código)
B: Institucion         (nombre)
C: Programa            (ej: "Medicina", "Enfermería", etc.)
D: Tipo_Estudiante (Pregrado/Posgrado)
E: Semestre (AAAA-S)   (ej: "2026-1")
F: Cupo_Estimado_Semestral  (número de estudiantes)
G: Observaciones       (opcional)
```

### Ejemplo de cómo llenarla:

```
ID_Institucion | Institucion              | Programa | Tipo_Estudiante | Semestre | Cupo_Estimado_Semestral
7600103715     | Hospital San José        | Medicina | Pregrado        | 2026-1   | 12
7600103715     | Hospital San José        | Medicina | Posgrado        | 2026-1   | 5
7600103715     | Hospital San José        | Medicina | Pregrado        | 2026-2   | 10
500102104      | Clínica Universidad      | Medicina | Pregrado        | 2026-1   | 20
500102104      | Clínica Universidad      | Medicina | Posgrado        | 2026-1   | 8
7600102541     | Hospital Simón Bolívar   | Medicina | Pregrado        | 2026-1   | 15
7600103359     | Centro Médico Bogotá     | Medicina | Pregrado        | 2026-1   | 18
```

### 💡 Notas importantes:
- **Un cupo no se asigna a un tipo de práctica específico** (es genérico)
- Los cupos pueden variar por semestre (cuando abre/cierra rotaciones)
- Incluir TODAS las combinaciones (programa × tipo_estudiante × semestre) que ofreces
- Los números deben ser enteros > 0

---

## 2️⃣ VERIFICAR: 04_Costo_del_Sitio

### ¿Qué es?
Define los **costos asociados** a que un estudiante de cierto programa y tipo de práctica se haga en cierta institución.

### Estructura de columnas:
```
A: ID_Institucion
B: Institucion
C: Programa_Costo        ("Medicina", "Todos" si aplica a todo)
D: Tipo_Estudiante_Costo ("Pregrado", "Posgrado")
E: Tipo_Practica_Costo   ("Rotación pregrado", "Internado", "Residencia", etc.)
F: Semestre_Vigencia (AAAA-S)
G: %_Contraprestacion_Matricula (0-100)
H: EPP_Exigidos          (detalle)
I: Cobro_EPP             ("No cobra EPP" o "Cobra EPP a la Universidad")
J: Observaciones_Costo
K: Fecha_Corte_Datos
```

### Ejemplo:
```
7600103715 | Hospital San José     | Medicina | Pregrado | Rotación pregrado       | 2026-1 | 30 | Completo | No cobra EPP | ...
7600103715 | Hospital San José     | Medicina | Pregrado | Internado de medicina   | 2026-1 | 25 | Parcial  | No cobra EPP | ...
500102104  | Clínica Universidad   | Todos    | Pregrado | Rotación pregrado       | 2026-1 | 40 | Parcial  | Cobra EPP    | ...
```

### 💡 Notas:
- **Columna G**: % de contraprestación (0-100) - usado para calcular costo
- **Columna I**: Factor importante en el modelo (afecta el score)
- Usa "Todos" en Programa_Costo si la política es igual para todos los programas
- Verificar que existan filas para TODAS las combinaciones relevantes

---

## 3️⃣ CREAR: Demanda Pregrado/Posgrado (Nueva hoja)

### ¿Qué es?
Define **cuántos estudiantes necesitas ubicar** en cada grupo (combinación de programa, tipo, práctica, semestre).

### Pasos:
1. Abre tu Excel
2. **Nuevo → Insertar hoja** → Llámala: `"Demanda Pregrado/Posgrado"`
3. Copia esta estructura de encabezados:

```
Semestre | Programa | Tipo_Estudiante | Tipo_Practica            | Demanda_Estudiantes
```

### Ejemplo completo:

```
Semestre | Programa  | Tipo_Estudiante | Tipo_Practica              | Demanda_Estudiantes
2026-1   | Medicina  | Pregrado        | Rotación pregrado          | 40
2026-1   | Medicina  | Pregrado        | Internado de medicina      | 25
2026-1   | Medicina  | Posgrado        | Residencia Medicina        | 18
2026-1   | Medicina  | Posgrado        | Fellowship                 | 6
2026-2   | Medicina  | Pregrado        | Rotación pregrado          | 35
2026-2   | Enfermería| Pregrado        | Práctica hospitalaria      | 50
```

### 💡 Notas:
- Los tipos de práctica deben cuadrar con los definidos en 04_Costo_del_Sitio
- La suma de todos es tu demanda total
- Números enteros > 0
- **Esto es lo que la ley/acreditación exige que enseñes**

---

## 🔄 FLUJO COMPLETO DE DATOS

```
┌─────────────────────────────────────────────────────────────────┐
│                      PLANTILLA EXCEL V3                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 01_Oferta ──┐                                                   │
│             ├─→ Merge ────→ Base de criterios                   │
│ 03_Calidad ─┘                 (Oferta + Calidad)                │
│                                       ↓                          │
│                          Normalizar criterios                    │
│                                       ↓                          │
│ 05_Ponderaciones ───────→ Calcular scores V(j,g)                │
│                                       ↓                          │
│                    ┌────────────────────────────┐                │
│                    │   MODELO DE OPTIMIZACIÓN   │                │
│                    │  (Maximiza utilidad total) │                │
│                    └────────────────────────────┘                │
│                            ↑        ↑                           │
│                            │        │                           │
│    02_Oferta_x_Programa ───┘        └─→ 04_Costo_del_Sitio      │
│          (Cupos)               Demanda Pregrado/Posgrado        │
│                                (Demanda)                         │
│                                                                 │
│                        ↓         ↓         ↓                     │
│                    ┌───────────────────────────┐                │
│                    │   RESULTADO / ASIGNACIÓN   │                │
│                    │   Óptima de estudiantes    │                │
│                    │   a instituciones          │                │
│                    └───────────────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎬 EJECUCIÓN

Una vez llenes las 3 hojas, ejecuta:

```bash
cd /Users/juanmanuelarias/Documents/trabajo/javeriana/modelo_opt_oficina_practicas
python scripts/modelo_v1.py
```

Esto generará:
- ✅ Asignaciones óptimas por institución
- ✅ Análisis de capacidad vs demanda
- ✅ Identificación de brechas
- ✅ Scores de calidad por asignación

---

## ⚠️ VALIDACIONES AUTOMÁTICAS

El modelo verifica:
- ✓ Suma de pesos = 1.0
- ✓ Datos de cupos y costos consistentes
- ✓ Demanda asignada ≤ Capacidad total
- ✓ Tipos de datos correctos
- ✓ Sin valores faltantes críticos

Si algo falta, el script genera datos de ejemplo y **avisa claramente**.

---

## 📞 PREGUNTAS FRECUENTES

**P: ¿Qué pasa si la demanda > capacidad?**  
R: El modelo asigna lo máximo posible e identifica la brecha. Recomendará aumentar cupos o ajustar demanda.

**P: ¿Los cupos deben variar por tipo de práctica?**  
R: No - son genéricos por (inst, prog, tipo_est, semestre). El modelo distribuye entre prácticas.

**P: ¿Puedo cambiar los pesos en 05_Ponderaciones?**  
R: Sí. Pero deben sumar exactamente 1.0. El modelo lo valida automáticamente.

**P: ¿Para qué semestres debo llenar datos?**  
R: Mínimo para 2026-1 y 2026-2. Más adelante pueden ser 2027-1, 2027-2, etc.

---

**Última actualización**: 18 de febrero de 2026
