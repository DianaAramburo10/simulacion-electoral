# Simulación multiagente del proceso electoral

## Estructura del proyecto

| Archivo | Descripción |
|---|---|
| modelo_electoral.py | Modelo principal de la simulación y comportamiento de los agentes. |
| requirements.txt | Dependencias necesarias para ejecutar el proyecto. |
| README.md | Documentación del proyecto. |
| .gitignore | Archivos y carpetas que no se deben subir al repositorio. |

## Instalación y ejecución

### 1. Clonar el repositorio

Copiar la URL del repositorio desde GitHub y ejecutar en la terminal:

    git clone URL_DEL_REPOSITORIO
    cd simulacion-electoral

### 2. Crear un entorno virtual

    python3 -m venv .venv

### 3. Activar el entorno virtual

**macOS y Linux:**

    source .venv/bin/activate

**Windows (PowerShell):**

    .venv\Scripts\Activate.ps1

### 4. Instalar las dependencias

    pip install -r requirements.txt

### 5. Ejecutar la simulación

**Modo demostración:**

    python modelo_electoral.py --modo demo --seed 3

**Modo jornada electoral completa:**

    python modelo_electoral.py --modo jornada --seed 3

## Modos de simulación

| Característica | Demo | Jornada |
|---|---|---|
| Población | 80 votantes | Lista nominal de 690 ciudadanos |
| Verificadores | 3 | 3 |
| Mamparas | 3 | 3 |
| Eventos extraordinarios | Programados | Probabilísticos |
| Inicio | 07:30 | 07:30 |
| Cierre | 18:00 | 18:00 |
| Semilla predeterminada | 3 | 3 |

La semilla permite reproducir los resultados de la simulación bajo las mismas condiciones.

## Archivos generados

Al ejecutar la simulación se generan automáticamente los siguientes archivos:
- **eventos_unity.json:** registro de los eventos ocurridos durante la simulación.
- **metricas_mesa.csv:** registro de las métricas recopiladas mediante DataCollector.


## Consideraciones importantes

- No subir la carpeta .venv.
- No subir archivos temporales o generados automáticamente.
- Actualizar requirements.txt si se agregan nuevas dependencias.
- Probar el funcionamiento del código antes de subir cambios.
- Documentar las nuevas funcionalidades.
- Evitar modificar directamente la rama main.

## Experimentos y análisis de resultados

Se desarrolló el archivo `experimentos.py` para evaluar el comportamiento de la simulación electoral bajo diferentes configuraciones. El objetivo es analizar cómo influyen la cantidad de votantes, el intervalo entre llegadas y el número de mamparas en la atención de los ciudadanos.

### Ejecución de los experimentos

Para ejecutar los experimentos, desde la carpeta principal del proyecto se utiliza el siguiente comando:

```bash
python experimentos.py
```

El programa utiliza el modelo definido en `modelo_electoral.py` y realiza un total de **90 simulaciones**, distribuidas en tres experimentos:

| Variable | Configuraciones evaluadas |
|---|---|
| Número de votantes | 40, 80 y 120 votantes |
| Intervalo promedio entre llegadas | 1.0, 1.5 y 3.0 minutos |
| Número de mamparas | 2, 3 y 4 mamparas |

Cada configuración se ejecuta bajo dos condiciones:

- **Sin eventos externos:** se desactivan los eventos de lluvia, ataques de Minions y tornados.
- **Con eventos externos:** se permite la aparición de estos eventos durante la simulación.

En ambas condiciones pueden ocurrir incidentes internos del modelo.

Para reducir la influencia de una sola ejecución aleatoria, cada configuración se repite utilizando cinco semillas: `3`, `7`, `11`, `15` y `19`.

### Métricas evaluadas

Se recopilan las siguientes métricas para comparar los resultados:

| Métrica | Descripción |
|---|---|
| Votantes atendidos | Cantidad de ciudadanos que completaron su votación. |
| Porcentaje de atención | Porcentaje de votantes atendidos respecto al total de ciudadanos simulados. |
| Fila máxima | Mayor cantidad de personas registrada en la fila de verificación. |
| Tiempo promedio de espera | Tiempo promedio que esperaron los ciudadanos que lograron votar. |

### Archivos generados

Al finalizar la ejecución, los resultados se almacenan automáticamente en la carpeta `experimentos_resultados/`.

| Archivo | Contenido |
|---|---|
| `repeticiones.csv` | Resultados individuales de las 90 simulaciones. |
| `resumen.csv` | Promedios de las cinco repeticiones para cada configuración y condición. |
| Gráficas PNG | Nueve gráficas comparativas de porcentaje de atención, fila máxima y tiempo promedio de espera. |

### Resultados principales

Los experimentos permitieron observar cómo las variaciones en los parámetros y la presencia de eventos externos afectan el funcionamiento de la casilla electoral.

**1. Influencia de los eventos externos**

En la configuración base de 80 votantes, intervalo promedio de 1.5 minutos y tres mamparas, se obtuvieron los siguientes resultados:

| Condición | Porcentaje promedio de atención |
|---|---:|
| Sin eventos externos | 91.75 % |
| Con eventos externos | 68.50 % |

La presencia de eventos externos redujo el porcentaje de ciudadanos atendidos, debido a las interrupciones que pueden producirse durante la jornada electoral.

**2. Influencia del intervalo entre llegadas**

En las simulaciones sin eventos externos, aumentar el intervalo promedio entre llegadas de 1.0 a 3.0 minutos redujo el tiempo promedio de espera de **12.44 a 2.74 minutos**.

Esto indica que una llegada más espaciada de votantes puede disminuir la congestión de las filas y facilitar la atención.

**3. Influencia del número de mamparas**

El aumento del número de mamparas no produjo una mejora constante en todas las ejecuciones.

Esto se debe a que la atención también depende de otros factores, como la disponibilidad de verificadores, las decisiones de los agentes y los incidentes aleatorios que pueden ocurrir durante la simulación.

### Conclusiones

Los resultados muestran que el desempeño de la casilla electoral depende de la combinación de los recursos disponibles, la frecuencia de llegada de los ciudadanos y los eventos que interrumpen el proceso.

La experimentación permite comparar diferentes escenarios e identificar condiciones que pueden generar mayores tiempos de espera o reducir la cantidad de votantes atendidos.

Los valores obtenidos corresponden a simulaciones realizadas con cinco semillas por configuración, por lo que deben interpretarse como resultados del modelo y no como predicciones de una jornada electoral real.