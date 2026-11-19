
import csv
import os
from contextlib import redirect_stdout
from io import StringIO

import matplotlib.pyplot as plt

from modelo_electoral import ModeloElectoral


# Configuración original del modo demo
BASE = {
    "n_demo": 80,
    "intervalo_llegadas": 1.5,
    "num_mamparas": 3
}

# Cambiar una variable a la vez
ESCENARIOS = {
    "Numero de votantes": [
        ("40 votantes", {"n_demo": 40}),
        ("80 votantes", {"n_demo": 80}),
        ("120 votantes", {"n_demo": 120})
    ],
    "Intervalo de llegadas": [
        ("1.0 min", {"intervalo_llegadas": 1.0}),
        ("1.5 min", {"intervalo_llegadas": 1.5}),
        ("3.0 min", {"intervalo_llegadas": 3.0})
    ],
    "Numero de mamparas": [
        ("2 mamparas", {"num_mamparas": 2}),
        ("3 mamparas", {"num_mamparas": 3}),
        ("4 mamparas", {"num_mamparas": 4})
    ]
}

# Cinco repeticiones para reducir el efecto del azar
SEMILLAS = [3, 7, 11, 15, 19]
CONDICIONES = {
    "Sin eventos externos": False,
    "Con eventos externos": True
}
CARPETA = "experimentos_resultados"
os.makedirs(CARPETA, exist_ok=True)


def ejecutar_simulacion(configuracion, semilla, eventos_externos=True):
    parametros = BASE.copy()
    parametros.update(configuracion)

    # Evitar imprimir miles de eventos en la terminal
    with redirect_stdout(StringIO()):
        modelo = ModeloElectoral(
            modo="demo",
            seed=semilla,
            n_demo=parametros["n_demo"],
            intervalo_llegadas=parametros["intervalo_llegadas"],
            num_mamparas=parametros["num_mamparas"],
            eventos_externos=eventos_externos
        )

        while modelo.running:
            modelo.step()

    metricas = modelo.metricas()

    return {
        "votantes": parametros["n_demo"],
        "intervalo_llegadas": parametros["intervalo_llegadas"],
        "mamparas": parametros["num_mamparas"],
        "atendidos": metricas["votantes_atendidos"],
        "fila_maxima": metricas["fila_maxima"],
        "espera_promedio": metricas["espera_promedio"],
        "porcentaje_atendidos": (
            100 * metricas["votantes_atendidos"]
            / parametros["n_demo"]
        )
    }


def promedio(valores):
    return sum(valores) / len(valores)


def generar_grafica(tipo, resultados, campo, titulo, eje_y, archivo):
    etiquetas = [fila["escenario"] for fila in resultados]
    valores = [fila[campo] for fila in resultados]

    fig, ax = plt.subplots(figsize=(9, 5))
    barras = ax.bar(etiquetas, valores)

    ax.set_title(titulo)
    ax.set_xlabel(tipo)
    ax.set_ylabel(eje_y)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)

    limite = max(valores) if valores else 1
    ax.set_ylim(0, max(1, limite * 1.18))

    for barra, valor in zip(barras, valores):
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height(),
            f"{valor:.2f}",
            ha="center",
            va="bottom"
        )

    plt.tight_layout()
    plt.savefig(
        os.path.join(CARPETA, archivo),
        dpi=180
    )
    plt.close(fig)

def main():
    registros = []
    resumen = []

    for tipo, escenarios in ESCENARIOS.items():
        print(f"\nExperimento: {tipo}")

        for nombre, cambios in escenarios:
            for condicion, activar_eventos in CONDICIONES.items():
                repeticiones = []

                for semilla in SEMILLAS:
                    datos = ejecutar_simulacion(
                        cambios,
                        semilla,
                        eventos_externos=activar_eventos
                    )

                    registros.append({
                        "experimento": tipo,
                        "escenario": nombre,
                        "condicion": condicion,
                        "semilla": semilla,
                        **datos
                    })

                    repeticiones.append(datos)

                fila = {
                    "experimento": tipo,
                    "escenario": nombre,
                    "condicion": condicion,
                    "atendidos": promedio(
                        [r["atendidos"] for r in repeticiones]
                    ),
                    "fila_maxima": promedio(
                        [r["fila_maxima"] for r in repeticiones]
                    ),
                    "espera_promedio": promedio(
                        [r["espera_promedio"] for r in repeticiones]
                    ),
                    "porcentaje_atendidos": promedio(
                        [r["porcentaje_atendidos"] for r in repeticiones]
                    )
                }

                resumen.append(fila)

                print(
                    f"  {nombre} | {condicion}: "
                    f"{fila['atendidos']:.1f} atendidos, "
                    f"{fila['fila_maxima']:.1f} fila maxima, "
                    f"{fila['espera_promedio']:.2f} min de espera"
                )

    # Exportar todas las repeticiones
    with open(
        os.path.join(CARPETA, "repeticiones.csv"),
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=list(registros[0].keys())
        )
        escritor.writeheader()
        escritor.writerows(registros)

    # Exportar promedios por escenario y condicion
    with open(
        os.path.join(CARPETA, "resumen.csv"),
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=list(resumen[0].keys())
        )
        escritor.writeheader()
        escritor.writerows(resumen)

    # Generar graficas comparativas
    for tipo in ESCENARIOS:
        datos_tipo = [
            fila for fila in resumen
            if fila["experimento"] == tipo
        ]

        nombre_archivo = {
            "Numero de votantes": "votantes",
            "Intervalo de llegadas": "llegadas",
            "Numero de mamparas": "mamparas"
        }[tipo]

        for campo, titulo, eje_y, sufijo in [
            (
                "espera_promedio",
                "Comparacion del tiempo promedio de espera",
                "Minutos",
                "espera"
            ),
            (
                "fila_maxima",
                "Comparacion de la fila maxima",
                "Personas",
                "fila"
            ),
            (
                "porcentaje_atendidos",
                "Porcentaje de votantes atendidos",
                "Porcentaje (%)",
                "atendidos"
            )
        ]:
            etiquetas = [
                f"{fila['escenario']}\n{fila['condicion']}"
                for fila in datos_tipo
            ]
            valores = [fila[campo] for fila in datos_tipo]

            fig, ax = plt.subplots(figsize=(12, 6))
            barras = ax.bar(range(len(valores)), valores)

            ax.set_title(titulo)
            ax.set_xlabel(tipo)
            ax.set_ylabel(eje_y)
            ax.set_xticks(range(len(etiquetas)))
            ax.set_xticklabels(etiquetas, rotation=25, ha="right")
            ax.grid(axis="y", alpha=0.25)
            ax.set_axisbelow(True)

            limite = max(valores) if valores else 1
            ax.set_ylim(0, max(1, limite * 1.2))

            for barra, valor in zip(barras, valores):
                ax.text(
                    barra.get_x() + barra.get_width() / 2,
                    barra.get_height(),
                    f"{valor:.2f}",
                    ha="center",
                    va="bottom"
                )

            plt.tight_layout()
            plt.savefig(
                os.path.join(
                    CARPETA,
                    f"{nombre_archivo}_{sufijo}.png"
                ),
                dpi=180
            )
            plt.close(fig)

    print("\nExperimentos terminados.")
    print(f"Resultados guardados en: {CARPETA}")


if __name__ == "__main__":
    main()

