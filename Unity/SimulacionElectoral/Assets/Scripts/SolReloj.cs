using UnityEngine;

// Va en la Directional Light. Mueve el sol según la hora del RelojSimulacion y anochece para el escrutinio.
public class SolReloj : MonoBehaviour
{
    public float giroY = -30f;
    public float intensidadNoche = 0.15f;

    Light luz;
    float intensidadDia;

    void Start()
    {
        luz = GetComponent<Light>();
        intensidadDia = luz.intensity;
    }

    void Update()
    {
        var t = RelojSimulacion.Instancia.t;
        // 07:00 (t = -30) amanece en 10°, 19:00 (t = 690) atardece en 170°
        transform.rotation = Quaternion.Euler(Mathf.Lerp(10f, 170f, Mathf.InverseLerp(-30f, 690f, t)), giroY, 0f);
        // de 19:00 a 20:30 (t = 780) baja la luz hasta la noche
        luz.intensity = Mathf.Lerp(intensidadDia, intensidadNoche, Mathf.InverseLerp(690f, 780f, t));
    }
}
