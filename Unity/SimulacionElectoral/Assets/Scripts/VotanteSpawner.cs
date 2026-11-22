using System.Collections.Generic;
using UnityEngine;

public class VotanteSpawner : MonoBehaviour
{
    public static VotanteSpawner Instancia { get; private set; }

    public TextAsset eventosJson;
    public GameObject prefabMujer, prefabHombre, prefabMayor, prefabSillaRuedas, prefabEmbarazada;
    public bool crearTodosAlIniciar; // solo para probar: forma a todos en la fila

    public List<EventoSim> Eventos { get; private set; }
    readonly Dictionary<int, EventoSim> datos = new();
    readonly Dictionary<int, Votante> votantes = new();

    [System.Serializable] class Lista { public List<EventoSim> items; }

    void Awake()
    {
        Instancia = this;
        // JsonUtility no lee un arreglo suelto, por eso se envuelve
        Eventos = JsonUtility.FromJson<Lista>("{\"items\":" + eventosJson.text + "}").items;
        foreach (var e in Eventos)
            if (e.votante > 0 && !datos.ContainsKey(e.votante)) datos[e.votante] = e;
    }

    void Start()
    {
        if (!crearTodosAlIniciar) return;
        int n = 0;
        foreach (var id in datos.Keys)
            Obtener(id).transform.position = PuntosCasilla.Instancia.LugarEnFila(n++);
    }

    // Devuelve el votante; si todavía no existe, lo crea al final de la fila.
    public Votante Obtener(int id)
    {
        if (votantes.TryGetValue(id, out var v)) return v;

        var p = PuntosCasilla.Instancia;
        var mirando = Quaternion.LookRotation(p.filaInicio.position - p.filaFin.position);
        var go = Instantiate(Prefab(datos[id]), p.filaFin.position, mirando, transform);
        go.name = $"Votante_{id}";

        v = go.AddComponent<Votante>();
        v.Iniciar(datos[id]);
        votantes[id] = v;
        return v;
    }

    GameObject Prefab(EventoSim d) => d.motivo_prioridad switch
    {
        "discapacidad" => prefabSillaRuedas,
        "embarazo" => prefabEmbarazada,
        "adulto mayor" => prefabMayor,
        _ => d.genero == "Mujer" ? prefabMujer : prefabHombre
    };
}
