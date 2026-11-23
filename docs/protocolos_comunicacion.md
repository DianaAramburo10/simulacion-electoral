# Protocolos de comunicación entre agentes

Los agentes se comunican con mensajes al estilo FIPA: `modelo.enviar(t, emisor, receptor, performativa, contenido)`.
El receptor decide su respuesta en su método `recibir`. Todos los mensajes se guardan en `mensajes_agentes.csv`.

| Performativa | Significado |
|---|---|
| `request` | El emisor pide algo |
| `inform` | El emisor comunica un dato |
| `agree` | El receptor acepta |
| `refuse` | El receptor se niega o rechaza |

## 1. Verificación de credencial (Funcionario ↔ Votante)

```mermaid
sequenceDiagram
    participant F as Funcionario
    participant V as Votante
    F->>V: request: muestre su credencial
    V-->>F: inform: vigente / ya votó / vencida / no_aparece / casilla_equivocada
    alt credencial válida
        F->>V: agree: pase a la mampara
    else credencial con problema o ya votó
        F->>V: refuse: motivo
    end
```

## 2. Prioridad en la fila (Votante → Presidente)

```mermaid
sequenceDiagram
    participant V as Votante (65+, discapacidad o embarazo)
    participant P as Presidente
    V->>P: request: pido pasar primero
    P-->>V: agree: pase primero
    Note over V: se adelanta en la fila
```

## 3. Mover la fila bajo techo (Presidente → Votantes en fila)

```mermaid
sequenceDiagram
    participant P as Presidente
    participant V as Cada votante en la fila
    Note over P: empieza a llover y decide mover la fila
    P->>V: request: muévanse bajo techo
    V-->>P: agree: me muevo
    Note over V: su estrés baja 10 puntos
```

## 4. Retirar a un revoltoso (Presidente → Votante)

```mermaid
sequenceDiagram
    participant P as Presidente
    participant V as Votante en la pelea
    Note over P: hay una pelea y decide intervenir
    P->>V: request: retírese de la fila
    V-->>P: agree: me retiro
```

## 5. Protesta de un voto nulo (Representante → Presidente)

```mermaid
sequenceDiagram
    participant R as Representante de partido
    participant P as Presidente
    Note over P: declara nulo un voto dudoso
    R->>P: request: pido recuento
    P-->>R: agree: se recuenta el voto
    Note over P: el escrutinio tarda 5 a 15 min más
```

## 6. Entrega del acta (Presidente → CAE)

```mermaid
sequenceDiagram
    participant P as Presidente
    participant C as CAE
    Note over P: termina el escrutinio
    P->>C: inform: acta lista
    C-->>P: agree: llevo el acta al PREP
    Note over C: traslado y transmisión al PREP
```
