// Un evento de eventos_unity.json. Los nombres deben ser iguales a las llaves del JSON.
[System.Serializable]
public class EventoSim
{
    public float t_min;
    public string hora, tipo, estado, genero, motivo_prioridad, texto;
    public int votante, edad, recurso, atacantes; // null en el JSON llega como 0
    public bool prioritario;
}
