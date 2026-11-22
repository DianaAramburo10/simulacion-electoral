using UnityEngine;

public class Votante : MonoBehaviour
{
    public int id, edad;
    public string genero, motivo;
    Material sueter;

    public void Iniciar(EventoSim d)
    {
        id = d.votante; edad = d.edad; genero = d.genero; motivo = d.motivo_prioridad;
        // .materials hace copias, así el color solo cambia en este votante
        foreach (var r in GetComponentsInChildren<Renderer>())
            foreach (var m in r.materials)
                if (m.name.StartsWith("Sueter")) sueter = m;
        // matiz entre 0.15 y 0.85 para que ninguno salga rojo (el rojo es "se va sin votar")
        ColorSueter(Random.ColorHSV(0.15f, 0.85f, 0.4f, 0.7f, 0.6f, 0.9f));
    }

    public void ColorSueter(Color c)
    {
        if (sueter != null) sueter.color = c;
    }
}
