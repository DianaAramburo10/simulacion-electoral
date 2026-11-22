// Herramienta de editor (solo funciona dentro de Unity, no en el juego).
// Lee posiciones.json de Blender y coloca el mobiliario y los puntos de referencia.
// Menú: Casilla > Colocar mobiliario y puntos
#if UNITY_EDITOR
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

public static class ColocarCasilla
{
    // Estructuras que imitan el formato de posiciones.json (JsonUtility necesita clases [Serializable]).
    [System.Serializable] class Coords { public float x, y, z, giro_y; }
    [System.Serializable] class Entrada { public string nombre; public string tipo; public Coords unity_esperado; }
    [System.Serializable] class Lista { public Entrada[] items; }

    // Piezas que ya vienen dentro de Casilla.fbx o Barrio.fbx: no se vuelven a colocar.
    static readonly string[] YaIncluidos = { "Terreno", "Piso", "Patio", "Pared_", "Calle", "Casa", "Arbol" };

    [MenuItem("Casilla/Colocar mobiliario y puntos")]
    public static void Colocar()
    {
        // 1) Leer el JSON. Debe estar en Assets/Datos/posiciones.json
        var json = AssetDatabase.LoadAssetAtPath<TextAsset>("Assets/Datos/posiciones.json");
        if (json == null) { Debug.LogError("No encontré Assets/Datos/posiciones.json"); return; }
        // JsonUtility no lee arreglos sueltos, por eso lo envolvemos en un objeto {"items": [...]}
        var lista = JsonUtility.FromJson<Lista>("{\"items\":" + json.text + "}");

        var mobiliario = ObtenerOCrear("Mobiliario");
        var puntos = ObtenerOCrear("Puntos");

        foreach (var e in lista.items)
        {
            var u = e.unity_esperado;
            var pos = new Vector3(u.x, u.y, u.z);
            var rot = Quaternion.Euler(0f, u.giro_y, 0f);

            if (e.tipo == "punto") { CrearPunto(puntos, e.nombre.Replace("Punto_", ""), pos); continue; }
            if (EsYaIncluido(e.nombre)) continue;

            // "Urna.003" -> "Urna": el modelo base es el nombre antes del punto.
            string baseNombre = e.nombre.Split('.')[0];
            var asset = BuscarAsset(baseNombre);
            if (asset == null) { Debug.LogWarning($"No encontré prefab ni FBX para {baseNombre}"); continue; }

            // InstantiatePrefab mantiene el vínculo con el prefab (si cambias el prefab, se actualizan todas las copias).
            var go = (GameObject)PrefabUtility.InstantiatePrefab(asset, mobiliario);
            go.name = e.nombre;
            go.transform.SetPositionAndRotation(pos, rot);
            Undo.RegisterCreatedObjectUndo(go, "Colocar " + e.nombre);
        }

        // 2) Puntos derivados de la tabla de estados del LEEME (ya convertidos a coordenadas de Unity).
        var derivados = new Dictionary<string, Vector3>
        {
            { "Fila_Inicio", new Vector3(4.9f, 0, 1.4f) },
            { "Verificador_0", new Vector3(0.8f, 0, -1.25f) },
            { "Verificador_1", new Vector3(0f, 0, -1.25f) },
            { "Verificador_2", new Vector3(-0.8f, 0, -1.25f) },
            { "Funcionario_0", new Vector3(0.8f, 0, -2.44f) },
            { "Funcionario_1", new Vector3(0f, 0, -2.44f) },
            { "Funcionario_2", new Vector3(-0.8f, 0, -2.44f) },
            { "Espera_Mampara", new Vector3(-0.5f, 0, -0.3f) },
            { "Mampara_0", new Vector3(-1.75f, 0, -1.5f) },
            { "Mampara_1", new Vector3(-1.75f, 0, -0.3f) },
            { "Mampara_Accesible", new Vector3(-1.75f, 0, 1.05f) },
            { "Urnas", new Vector3(-1.0f, 0, 1.7f) },
            { "Salida", new Vector3(0f, 0, 4.0f) },
        };
        foreach (var d in derivados) CrearPunto(puntos, d.Key, d.Value);

        Debug.Log("Casilla colocada. Revisa Mobiliario y Puntos en la jerarquía.");
    }

    static bool EsYaIncluido(string nombre)
    {
        foreach (var p in YaIncluidos) if (nombre.StartsWith(p)) return true;
        return false;
    }

    // Busca primero un prefab en Assets/Prefabs y, si no existe, el FBX en Assets/Modelos.
    static GameObject BuscarAsset(string nombre)
    {
        foreach (var filtro in new[] { "t:Prefab", "t:Model" })
            foreach (var guid in AssetDatabase.FindAssets($"{nombre} {filtro}", new[] { "Assets/Prefabs", "Assets/Modelos" }))
            {
                var ruta = AssetDatabase.GUIDToAssetPath(guid);
                if (System.IO.Path.GetFileNameWithoutExtension(ruta) == nombre)
                    return AssetDatabase.LoadAssetAtPath<GameObject>(ruta);
            }
        return null;
    }

    static Transform ObtenerOCrear(string nombre)
    {
        var go = GameObject.Find(nombre);
        if (go == null) { go = new GameObject(nombre); Undo.RegisterCreatedObjectUndo(go, "Crear " + nombre); }
        return go.transform;
    }

    static void CrearPunto(Transform padre, string nombre, Vector3 pos)
    {
        var existente = padre.Find(nombre);
        var go = existente != null ? existente.gameObject : new GameObject(nombre);
        if (existente == null) Undo.RegisterCreatedObjectUndo(go, "Punto " + nombre);
        go.transform.SetParent(padre);
        go.transform.position = pos;
    }
}
#endif
