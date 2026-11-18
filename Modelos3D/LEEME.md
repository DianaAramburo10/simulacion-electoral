# Casilla de votacion: modelos 3D

Entrega de la persona 3 (Blender). Todo esta en metros y pensado para soltarse en Unity sin ajustes.

> **Probado en Unity el 16 de noviembre de 2026.** Los modelos entran parados, con Rotation 0, 0, 0 y Scale 1, 1, 1, y a tamano real (la votante mide como cubo y medio de Unity). `Casilla.fbx` y `Barrio.fbx` encajan al soltarlos los dos en 0, 0, 0.

## Que hay en esta carpeta

| Archivo | Que es |
|---|---|
| `FBX/` | 20 archivos: 18 modelos sueltos, mas `Casilla.fbx` y `Barrio.fbx` ya armados |
| `posiciones.json` | Donde va cada objeto, en coordenadas de Blender y en las esperadas de Unity |
| `Casilla_render.png` | Imagen de la casilla para el documento |
| `Barrio_render.png` | Vista general: casas, calle y casilla conectadas |
| `Personajes_render.png` | Los cinco votantes y los dos funcionarios |
| `Casilla_escena.blend` | Archivo fuente de Blender 5.2, por si quieren ver o cambiar algo |

---

## 1. Como comprobar que les entro igual (opcional, 2 minutos)

1. Arrastren `FBX/Urna.fbx` a `Assets` y luego a la escena, en Position 0, 0, 0.
2. En el Inspector debe decir Rotation 0, 0, 0 y Scale 1, 1, 1.
3. Junto a un cubo de Unity (1 metro), la urna debe verse un poco mas baja.

Si en su version de Unity sale distinto, avisen a Camila.

---

## 2. Persona 4: escena, camara y presentacion

**Importar**

1. Copien toda la carpeta `FBX` dentro de `Assets/Modelos`.
2. Seleccionen todos los FBX y, en el Inspector, pestana **Materials**, usen **Extract Materials** hacia una carpeta `Assets/Materiales`. Asi los colores quedan como materiales editables.
3. Las urnas son translucidas en Blender. Si en Unity salen opacas, cambien el material `Urna` a modo Transparent, o dejenlo opaco: no afecta nada mas.

**Armar la escena**

1. Arrastren `Casilla.fbx` a Position 0, 0, 0. Trae piso, patio y las dos paredes ya acomodados.
1. Arrastren `Barrio.fbx` tambien a Position 0, 0, 0. Trae el terreno, la calle, tres casas y arboles, ya alineados con la casilla. No hay que unir nada a mano.
2. Coloquen el resto con `posiciones.json`, usando los valores de `unity_esperado` (x, y, z y giro_y). Coloquen primero una mampara para comprobar que cae en su lugar (a la derecha de la mesa, con la abertura hacia el centro). Si no, avisen y se regenera el archivo.
3. Conviertan en prefab cada modelo que se repite: `Silla` (3), `Mampara` (2), `Urna` (6), los votantes y los funcionarios.
4. Los tres funcionarios van detras de la mesa, mirando al frente: en Blender X = -0.8, 0 y 0.8, con Y = 2.44. Son figuras de pie; si quieren que parezcan sentados, bajenlos unos 25 cm para que la mesa les tape las piernas, como en el render.

**Lo obligatorio y lo opcional**

| Obligatorio | Decoracion (pueden omitirla) |
|---|---|
| Casilla, Mesa_Funcionarios, Silla, Mampara, Mampara_Accesible, Urna | Toldo, Cartel, Banderines, Maceta, Papeleria, Unifila |
| Votante_Mujer, Votante_Hombre, Votante_Mayor, Votante_Silla_Ruedas, Votante_Embarazada, Funcionario_Mujer, Funcionario_Hombre | Barrio (solo si hacen la simulacion del hogar; sin el, la casilla funciona igual) |

**Colores que se pueden cambiar**

- `Banda`: la franja de cada urna. Un color por eleccion.
- `Chaleco`: el chaleco de los funcionarios, por si quieren distinguir al presidente de los secretarios.
- `Sueter`: la prenda de arriba de cada votante. Sirve para que no se vean todos iguales.

---

## 3. Persona 5: comportamiento y conexion con Python

- **Los votantes no tienen esqueleto ni animacion.** Se mueven deslizandose, con NavMeshAgent o moviendo su posicion. No hay Animator que configurar.
- **Frente del modelo:** cada votante mira hacia +Z de Unity (su `forward`), asi que girar hacia el destino funciona directo.
- **Estados con color:** cambien el color del material `Sueter` de esa instancia. Es la forma mas simple de mostrar verificando, en mampara o abandonando.
- **Dos tipos de agente, cada uno con su modelo:** votantes (sueter verde azulado) y funcionarios (`Funcionario_Mujer` y `Funcionario_Hombre`, con camisa clara, chaleco vino y gafete). Se distinguen a simple vista sin cambiar nada.
- **Cinco modelos de votante** segun los datos de su codigo:

| Dato del votante en el codigo | Modelo |
|---|---|
| `genero == 'Mujer'` sin prioridad | `Votante_Mujer` |
| `genero == 'Hombre'` sin prioridad | `Votante_Hombre` |
| `motivo_prioridad == 'adulto mayor'` | `Votante_Mayor` (con baston) |
| `motivo_prioridad == 'discapacidad'` | `Votante_Silla_Ruedas` |
| `motivo_prioridad == 'embarazo'` | `Votante_Embarazada` |

- **Votante_Silla_Ruedas** mide 0.70 m de ancho y 1.10 m de largo con la silla, asi que cabe por la puerta (1.2 m) y en `Mampara_Accesible`. Si usan NavMeshAgent, denle un radio un poco mayor que a los demas (unos 0.4 m).
- **NavMesh:** marquen `Casilla` y `Barrio` como estaticos y horneen una sola vez. Terreno, calle, banqueta, patio y piso estan casi al mismo nivel (diferencias de 1 a 2 cm), asi que queda una sola superficie caminable sin escalones. La puerta de la casilla mide 1.2 m de ancho.

**A que punto va cada estado** (coordenadas de Blender en metros; las de Unity estan en `posiciones.json`)

| Estado en el codigo | Punto | X | Y |
|---|---|---|---|
| Esperando verificacion | Fila afuera, entre los postes de la unifila | de -4.9 hacia -8 | -1.4 |
| Entrada | Puerta de la pared izquierda | -3.9 | -1.4 |
| Verificando | Frente a la mesa de funcionarios | de -0.8 a 0.8 | 1.25 |
| Esperando mampara | Centro de la casilla | 0.5 | 0.3 |
| En mampara | Frente a Mampara, Mampara.001 o Mampara_Accesible | 1.75 | 1.5, 0.3 o -1.05 |
| Caminando a urna | Frente a la fila de urnas | de -0.5 a 2.5 | -1.7 |
| Finalizado | Sale por el frente abierto | cualquiera | menor a -3 |

Los votantes con prioridad por discapacidad usan `Mampara_Accesible`.

**Simulacion del hogar (puntos extra de EXPO)**

El votante aparece en la puerta de una casa y camina hasta el final de la fila. Con el NavMesh horneado basta darle el destino.

| Punto | X | Y |
|---|---|---|
| Punto_Puerta_Casa | -14.8 | -13.6 |
| Punto_Puerta_Casa_2 | -4.8 | -13.6 |
| Punto_Puerta_Casa_3 | 6.2 | -13.6 |
| Punto_Cruce_Calle (opcional) | -9.0 | -11.5 |
| Punto_Fin_De_Fila | -8.0 | -1.4 |
| Punto_Entrada_Casilla | -3.9 | -1.4 |

La distancia es simbolica (unos 15 a 25 metros). El tiempo real de traslado lo calcula Python; Unity solo lo muestra, acelerado si hace falta.

Si no quieren que camine, pueden mostrar al votante en su puerta con una camara y luego hacerlo aparecer en `Punto_Fin_De_Fila`. Los modelos sirven igual para las dos formas.

---

## 4. Persona 2: documento

- `Casilla_render.png` es la imagen principal de la casilla.
- `Barrio_render.png` muestra las casas, la calle y la casilla en un solo mundo, por si incluyen la simulacion del hogar.
- Para el diagrama de clases: los modelos corresponden a Votante (3 variantes), Funcionario (2 variantes, con chaleco), Casilla, Mampara y Urna.

## 5. Persona 1: repositorio

Propuesta: subir esta carpeta completa como `Modelos3D/`. Los FBX pesan poco (menos de 2 MB en total).

---

## Datos tecnicos

**Convenciones**

- 1 unidad = 1 metro, con la escala aplicada.
- Origen de cada modelo en el centro de su base.
- Frente hacia -Y de Blender, que al exportar queda como +Z de Unity.
- Nombres sin acentos ni espacios.
- Cada FBX esta en 0, 0, 0 y sin rotacion. Las excepciones son `Casilla.fbx` y `Barrio.fbx`, que traen sus piezas ya acomodadas y se sueltan los dos en 0, 0, 0.

**Tamano y peso**

| Modelo | Alto | Triangulos |
|---|---|---|
| Votante_Mujer | 1.63 m | 12,740 |
| Votante_Hombre | 1.81 m | 11,252 |
| Votante_Mayor | 1.53 m | 11,384 |
| Votante_Silla_Ruedas | 1.47 m (sentado) | 17,432 |
| Votante_Embarazada | 1.63 m | 15,476 |
| Funcionario_Mujer | 1.63 m | 13,096 |
| Funcionario_Hombre | 1.81 m | 11,656 |
| Mampara y Mampara_Accesible | 1.9 m | 3,520 |
| Urna | 0.94 m | menos de 100 |
| Todo lo demas | | menos de 2,500 cada uno |

Con 80 votantes en pantalla son cerca de un millon de triangulos.

**Conversion de coordenadas**

Unity X = -Blender X, Unity Y = Blender Z, Unity Z = -Blender Y, y giro en Y de Unity = -giro en Z de Blender.

La orientacion de la casilla en la prueba coincide con esta conversion. Lo que falta comprobar es colocar un mueble suelto con los valores de `posiciones.json`.

## Lo que no esta hecho

- El atacante del evento de robo.
- Una pose sentada para los funcionarios. Son figuras de pie, colocadas detras de la mesa.
- Tornado y lluvia: son efectos de Unity, no modelos.

## Como se hizo

La casilla y los muebles se modelaron a mano en Blender. Los votantes, la decoracion, los colores, la luz, los renders y la exportacion se generaron con scripts de Python para Blender, con ayuda de Claude.
