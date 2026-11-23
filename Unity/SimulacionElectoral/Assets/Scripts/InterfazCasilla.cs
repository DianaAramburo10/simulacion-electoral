using System.Collections.Generic;
using TMPro;
using UnityEngine;

public class InterfazCasilla : MonoBehaviour
{
    public TMP_Text textoReloj, textoFila, textoAtendidos, textoAviso;
    public GameObject fondoAviso; // opcional: se oculta cuando no hay aviso
    public float segundosAviso = 4f;

    readonly HashSet<int> enFila = new(), atendidos = new();
    readonly Queue<EventoSim> avisos = new(); // varios eventos pueden caer en el mismo minuto
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
            // a velocidad alta se acumulan; los de más de 30 min de atraso ya no se muestran
            while (avisos.Count > 0 && t - avisos.Peek().t_min > 30f) avisos.Dequeue();
            textoAviso.text = avisos.Count > 0 ? $"{avisos.Peek().hora} · {avisos.Dequeue().texto}" : "";
            ocultarAvisoEn = Time.time + segundosAviso;
            if (fondoAviso != null) fondoAviso.SetActive(textoAviso.text != "");
        }
    }

    void Aplicar(EventoSim e)
    {
        if (e.votante == 0)
        {
            avisos.Enqueue(e);
            return;
        }
        // cualquier evento distinto de formarse saca al votante de la fila
        if (e.tipo == "Formarse" || e.tipo == "Prioridad") enFila.Add(e.votante);
        else enFila.Remove(e.votante);

        if (e.tipo == "Salida" || e.tipo == "Toma de fila") atendidos.Add(e.votante);
    }
}
