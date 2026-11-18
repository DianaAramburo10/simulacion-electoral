# Simulación electoral con Mesa

Migración del script original a Mesa 3.3.1 (Python 3.11 o superior). Conserva heapq como cola de eventos discretos; un step procesa un evento y t_min indica minutos simulados desde las 07:30. No equivale a un minuto por step.

## Instalación (macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python modelo_electoral.py --modo demo --seed 3
python modelo_electoral.py --modo jornada --seed 3
```

Cada ejecución genera eventos_unity.json y metricas_mesa.csv (sobrescribe los anteriores). El modelo expone estado_unity() para una futura API. No incluye servidor ni cliente Unity.

## Repositorio

```bash
git init
git add .
git commit -m "Migración del modelo electoral a Mesa"
```

## Validación de migración

Se compararon el script original y la adaptación con una implementación de prueba mínima de las interfaces Model, Agent y DataCollector; los reportes y JSON coincidieron byte a byte en demo y jornada con semilla 3. No se pudo instalar Mesa en el entorno de validación; falta repetir las pruebas con la dependencia real. Se preservaron las reglas del script original, incluidas sus limitaciones: espera promedio solo entre quienes votaron y fila máxima solo de verificación; no es una validación empírica del proceso real.
