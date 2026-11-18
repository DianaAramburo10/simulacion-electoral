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
