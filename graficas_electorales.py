
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# Carpeta donde se encuentra este script
CARPETA = Path(__file__).resolve().parent

ARCHIVO_CSV = CARPETA / "metricas_mesa.csv"
ARCHIVO_JSON = CARPETA / "eventos_unity.json"
CARPETA_SALIDA = CARPETA / "graficas"

CARPETA_SALIDA.mkdir(exist_ok=True)


# 1. CARGAR DATOS

datos = pd.read_csv(ARCHIVO_CSV)

with open(ARCHIVO_JSON, "r", encoding="utf-8") as archivo:
    eventos = json.load(archivo)

# Convertir minutos simulados a horas del día.
# La simulación comienza a las 07:30.
datos["Hora"] = 7.5 + datos["Tiempo_min"] / 60

# Evitar registros repetidos del mismo instante
datos = datos.sort_values("Tiempo_min")


# 2. IDENTIFICAR EVENTOS EXTRAORDINARIOS

tipos_importantes = {
    "Ataque": ("Ataque Minions", "red"),
    "Tornado": ("Tornado", "purple"),
    "Lluvia": ("Lluvia", "steelblue")
}

eventos_importantes = []

for evento in eventos:
    tipo = evento.get("tipo")

    if tipo in tipos_importantes:
        nombre, color = tipos_importantes[tipo]

        eventos_importantes.append({
            "hora": 7.5 + evento["t_min"] / 60,
            "nombre": nombre,
            "color": color
        })


def configurar_grafica(titulo, eje_y):
    plt.title(titulo, fontsize=14, fontweight="bold")
    plt.xlabel("Hora del día")
    plt.ylabel(eje_y)
    plt.grid(alpha=0.25)
    plt.xlim(7.5, 21.5)


def marcar_eventos():
    """Dibuja líneas verticales para eventos externos."""
    etiquetas_usadas = set()

    for evento in eventos_importantes:
        nombre = evento["nombre"]

        etiqueta = (
            nombre if nombre not in etiquetas_usadas else None
        )

        plt.axvline(
            evento["hora"],
            color=evento["color"],
            linestyle="--",
            alpha=0.7,
            linewidth=1.5,
            label=etiqueta
        )

        etiquetas_usadas.add(nombre)


def guardar_grafica(nombre):
    ruta = CARPETA_SALIDA / nombre
    plt.tight_layout()
    plt.savefig(ruta, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Gráfica guardada: {ruta}")


# 3. GRÁFICA DE FILAS

plt.figure(figsize=(12, 6))

plt.plot(
    datos["Hora"],
    datos["Fila_verificacion"],
    label="Fila de verificación",
    color="royalblue",
    linewidth=2
)

plt.plot(
    datos["Hora"],
    datos["Fila_mampara"],
    label="Fila de mamparas",
    color="darkorange",
    linewidth=2
)

configurar_grafica(
    "Longitud de las filas durante la jornada",
    "Número de personas en espera"
)

marcar_eventos()
plt.legend()
guardar_grafica("01_filas.png")


# 4. GRÁFICA DE VOTANTES ATENDIDOS

plt.figure(figsize=(12, 6))

plt.plot(
    datos["Hora"],
    datos["Votantes_atendidos"],
    color="seagreen",
    linewidth=2,
    label="Votantes atendidos"
)

configurar_grafica(
    "Votantes atendidos durante la jornada",
    "Número acumulado de votantes"
)

marcar_eventos()
plt.legend()
guardar_grafica("02_votantes_atendidos.png")


# 5. GRÁFICA DEL TIEMPO PROMEDIO DE ESPERA

plt.figure(figsize=(12, 6))

plt.plot(
    datos["Hora"],
    datos["Espera_promedio"],
    color="darkmagenta",
    linewidth=2,
    label="Espera promedio acumulada"
)

configurar_grafica(
    "Evolución del tiempo promedio de espera",
    "Tiempo de espera (minutos)"
)

marcar_eventos()
plt.legend()
guardar_grafica("03_tiempo_espera.png")


# 6. COMPARACIÓN DE INDICADORES

total_atendidos = int(datos["Votantes_atendidos"].max())
fila_maxima = int(datos["Fila_maxima"].max())
espera_final = float(datos["Espera_promedio"].iloc[-1])

indicadores = [
    "Votantes atendidos",
    "Fila máxima"
]

valores = [
    total_atendidos,
    fila_maxima
]

plt.figure(figsize=(9, 5))

barras = plt.bar(
    indicadores,
    valores,
    color=["seagreen", "royalblue"]
)

for barra in barras:
    altura = barra.get_height()

    plt.text(
        barra.get_x() + barra.get_width() / 2,
        altura + 0.5,
        str(int(altura)),
        ha="center",
        fontweight="bold"
    )

plt.title(
    "Indicadores de la simulación electoral",
    fontsize=14,
    fontweight="bold"
)

plt.ylabel("Número de personas")
plt.ylim(0, max(valores) * 1.2)
plt.grid(axis="y", alpha=0.2)

guardar_grafica("04_indicadores.png")


# 7. RESUMEN EN TERMINAL

print("\n" + "=" * 45)
print("RESUMEN DE LA SIMULACIÓN")
print("=" * 45)

print(f"Votantes atendidos: {total_atendidos}")
print(f"Fila máxima: {fila_maxima}")
print(f"Espera promedio final: {espera_final:.2f} min")
print(f"Eventos registrados: {len(eventos)}")

print("\nEventos extraordinarios:")

for evento in eventos_importantes:
    print(
        f"- {evento['nombre']} "
        f"(hora decimal: {evento['hora']:.2f})"
    )

print("\nTodas las gráficas se generaron correctamente.")
