# ⚡ Inicio Rápido

## 1️⃣ Instalación (primera vez)

```bash
# Navega a la carpeta del proyecto
cd /Users/juanmanuelarias/Documents/trabajo/javeriana/modelo_opt_oficina_practicas

# Crea entorno virtual
python -m venv venv

# Activa el entorno
source venv/bin/activate

# Instala dependencias
pip install -r requirements.txt
```

---

## 2️⃣ Ejecutar la App

```bash
streamlit run app.py
```

Se abrirá automáticamente en: http://localhost:8501

---

## 3️⃣ Uso Básico

### En la App:

1. **📁 Subir archivo**
   - Click en "Selecciona tu archivo Excel"
   - Selecciona `Plantilla_V3_FacSalud.xlsx`

2. **⚙️ Configurar**
   - Set de Ponderaciones: `SET001` (por defecto)
   - Semestre: `2026-1` (por defecto)

3. **🚀 Ejecutar**
   - Click en "Ejecutar Optimización"
   - Espera a que termine (3-5 segundos)

4. **📊 Ver Resultados**
   - Ve a pestaña "Resultados"
   - Visualiza gráficos y tablas
   - Descarga CSV si necesitas

---

## 🔍 Estructura para Recordar

```
📦 proyecto/
├── app.py ............................ App Streamlit (lo que ejecutas)
├── requirements.txt .................. Dependencias
├── src/core/ ......................... Lógica del modelo
│   ├── data_loader.py ................ Carga Excel
│   ├── calculator.py ................. Normaliza criterios
│   └── optimizer.py .................. Resuelve MILP
├── data/ ............................ Datos
│   ├── uploads/ ..................... Archivos que subes
│   └── outputs/ ..................... Resultados
└── logs/ ............................ Registros de ejecución
```

---

## ❓ Preguntas Frecuentes

**P: ¿Dónde pongo mi archivo Excel?**  
R: En la app → "Selecciona tu archivo Excel" → Sube de donde quieras

**P: ¿Qué pasa si no tengo datos en cupos?**  
R: La app genera datos de EJEMPLO automáticamente (pero muestra advertencia)

**P: ¿Cómo veo los logs?**  
A: ```bash
tail -f logs/modelo_*.log
```

**P: ¿Cómo cambio los pesos de criterios?**  
R: En tu Excel: hoja "05_Ponderaciones" → columna "Peso (0-1)"

---

## 🐛 Si algo falla

1. Asegúrate que Python 3.9+ está instalado
   ```bash
   python --version
   ```

2. Verifica que el entorno está activado (debe aparecer `(venv)` en terminal)
   ```bash
   source venv/bin/activate
   ```

3. Reinstala dependencias
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

4. Revisa logs en `debug_logs/`

---

## 📞 Atajo comandos útiles

```bash
# Abrir la app
streamlit run app.py

# Ver estado de logs en tiempo real
tail -f logs/modelo_*.log

# Limpiar archivos temporales
rm -rf data/uploads/* data/outputs/*

# Desactivar entorno virtual
deactivate
```

---

**¡Listo!** Ya puedes usar la aplicación.  
Cualquier duda, revisa [README.md](README.md) o [GUÍA_LLENADO_PLANTILLA.md](GUÍA_LLENADO_PLANTILLA.md)
