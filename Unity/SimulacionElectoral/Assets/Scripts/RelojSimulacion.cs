using UnityEngine;

// Reloj compartido: minutos de simulación desde las 07:30. Lo usan la interfaz y el lector de eventos.
public class RelojSimulacion : MonoBehaviour
{
    public static RelojSimulacion Instancia { get; private set; }

    public float minutosPorSegundo = 2f;
    public float t;

    public string Hora => System.TimeSpan.FromMinutes(450 + t).ToString(@"hh\:mm");

    void Awake() => Instancia = this;

    void Update() => t += minutosPorSegundo * Time.deltaTime;
}
