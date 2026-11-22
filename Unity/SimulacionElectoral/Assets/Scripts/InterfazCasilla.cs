using System.Collections.Generic;
using TMPro;
using UnityEngine;

public class InterfazCasilla : MonoBehaviour
{
    public TMP_Text textoReloj, textoFila, textoAtendidos, textoAviso;
    public float segundosAviso = 4f;

    readonly HashSet<int> enFila = new(), atendidos = new();
    readonly Queue<string> avisos = new(); // varios eventos pueden caer en el mismo minuto
    int siguiente;
    float ocultarAvisoEn;

    void Update()
    {
        var eventos = VotanteSpawner.Instancia.Eventos;
        var t = RelojSimulacion.Instancia.t;
        while (siguiente < eventos.Count && eventos[siguiente].t_min <= t)
            Aplicar(eventos[siguiente++]);

        textoReloj.text = RelojSimulacion.Instancia.Hora;
        textoFila.text = $"En fila: {enFila.Count}";
        textoAtendidos.text = $"Votaron: {atendidos.Count}";
        if (Time.time > ocultarAvisoEn)
        {
            textoAviso.text = avisos.Count > 0 ? avisos.Dequeue() : "";
            ocultarAvisoEn = Time.time + segundosAviso;
        }
    }

    void Aplicar(EventoSim e)
    {
        if (e.votante == 0)
        {
            avisos.Enqueue(e.texto);
            return;
        }
        // cualquier evento distinto de formarse saca al votante de la fila
        if (e.tipo == "Formarse" || e.tipo == "Prioridad") enFila.Add(e.votante);
        else enFila.Remove(e.votante);

        if (e.tipo == "Salida" || e.tipo == "Toma de fila") atendidos.Add(e.votante);
    }
}
