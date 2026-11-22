using UnityEngine;
using UnityEngine.InputSystem;

// Va en la Main Camera. C = seguir al siguiente votante, V = volver a la vista general.
public class CamaraVotante : MonoBehaviour
{
    public float atras = 3.5f, arriba = 2.5f, suavidad = 5f;

    Vector3 posGeneral;
    Quaternion rotGeneral;
    Transform objetivo;
    int indice = -1;

    void Start()
    {
        posGeneral = transform.position;
        rotGeneral = transform.rotation;
    }

    void Update()
    {
        var k = Keyboard.current;
        if (k == null) return;
        if (k.cKey.wasPressedThisFrame) Siguiente();
        if (k.vKey.wasPressedThisFrame) objetivo = null;
    }

    void LateUpdate()
    {
        if (objetivo == null)
        {
            transform.SetPositionAndRotation(posGeneral, rotGeneral);
            return;
        }
        var deseada = objetivo.position - objetivo.forward * atras + Vector3.up * arriba;
        transform.position = Vector3.Lerp(transform.position, deseada, suavidad * Time.deltaTime);
        transform.LookAt(objetivo.position + Vector3.up * 1.2f);
    }

    void Siguiente()
    {
        var votantes = VotanteSpawner.Instancia.transform;
        if (votantes.childCount == 0) return;
        indice = (indice + 1) % votantes.childCount;
        objetivo = votantes.GetChild(indice);
    }
}
