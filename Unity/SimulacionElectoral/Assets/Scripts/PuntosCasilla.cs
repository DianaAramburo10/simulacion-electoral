using System.Collections.Generic;
using UnityEngine;

// Va en el objeto "Puntos" de la escena.
// Es el "contrato" entre la escena (Persona 4) y el movimiento (Persona 5):
// la Persona 5 pide un destino por nombre o por índice y no tiene que saber coordenadas.
public class PuntosCasilla : MonoBehaviour
{
    public static PuntosCasilla Instancia { get; private set; }

    [Header("Fila")]
    public Transform entrada;       // Entrada_Casilla
    public Transform filaInicio;    // primer lugar de la fila
    public Transform filaFin;       // Fin_De_Fila
    public float separacionFila = 0.8f; // metros entre personas formadas

    [Header("Mesa y mamparas")]
    public Transform[] verificadores = new Transform[3]; // índice = recurso del modelo
    public Transform[] funcionarios = new Transform[3];
    public Transform esperaMampara;
    public Transform[] mamparas = new Transform[3];     // 0, 1 y Accesible
    public Transform urnas;
    public Transform salida;

    [Header("Hogar (nivel II)")]
    public Transform[] casas = new Transform[3];

    void Awake()
    {
        Instancia = this;
        AutoAsignar();
    }

    // Lugar número n de la fila: avanza desde filaInicio hacia filaFin.
    public Vector3 LugarEnFila(int n)
    {
        Vector3 dir = (filaFin.position - filaInicio.position).normalized;
        return filaInicio.position + dir * separacionFila * n;
    }

    // Llena los campos buscando hijos por nombre (los crea ColocarCasilla).
    // Usamos "== null" y no "??=" porque Unity redefine == para sus objetos.
    // Se llama sola al agregar el componente (Reset) o al iniciar el juego.
    void Reset() => AutoAsignar();

    void AutoAsignar()
    {
        var hijos = new Dictionary<string, Transform>();
        foreach (Transform t in transform) hijos[t.name] = t;
        Transform H(string n) => hijos.TryGetValue(n, out var t) ? t : null;
        if (verificadores == null || verificadores.Length != 3) verificadores = new Transform[3];
        if (funcionarios == null || funcionarios.Length != 3) funcionarios = new Transform[3];
        if (mamparas == null || mamparas.Length != 3) mamparas = new Transform[3];
        if (casas == null || casas.Length != 3) casas = new Transform[3];

        if (entrada == null) entrada = H("Entrada_Casilla");
        if (filaInicio == null) filaInicio = H("Fila_Inicio");
        if (filaFin == null) filaFin = H("Fin_De_Fila");
        if (esperaMampara == null) esperaMampara = H("Espera_Mampara");
        if (urnas == null) urnas = H("Urnas");
        if (salida == null) salida = H("Salida");
        for (int i = 0; i < 3; i++)
        {
            if (verificadores[i] == null) verificadores[i] = H($"Verificador_{i}");
            if (funcionarios[i] == null) funcionarios[i] = H($"Funcionario_{i}");
        }
        if (mamparas[0] == null) mamparas[0] = H("Mampara_0");
        if (mamparas[1] == null) mamparas[1] = H("Mampara_1");
        if (mamparas[2] == null) mamparas[2] = H("Mampara_Accesible");
        if (casas[0] == null) casas[0] = H("Puerta_Casa");
        if (casas[1] == null) casas[1] = H("Puerta_Casa_2");
        if (casas[2] == null) casas[2] = H("Puerta_Casa_3");
    }

    // Dibuja esferas en la vista Scene para ver los puntos (no se ven en el juego).
    void OnDrawGizmos()
    {
        foreach (Transform t in transform)
        {
            Gizmos.color = t.name.StartsWith("Mampara") ? Color.cyan
                         : t.name.StartsWith("Verificador") ? Color.yellow
                         : t.name.StartsWith("Funcionario") ? Color.red : Color.green;
            Gizmos.DrawSphere(t.position + Vector3.up * 0.05f, 0.15f);
        }
    }
}
