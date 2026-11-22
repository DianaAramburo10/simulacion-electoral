// Herramienta de editor: extrae los materiales de todos los FBX de Assets/Modelos
// (lo mismo que el botón "Extract Materials", pero para todos a la vez).
// Menú: Casilla > Extraer materiales de todos los FBX
#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEngine;

public static class ExtraerMateriales
{
    [MenuItem("Casilla/Extraer materiales de todos los FBX")]
    public static void Extraer()
    {
        int total = 0;
        foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { "Assets/Modelos" }))
        {
            string rutaFbx = AssetDatabase.GUIDToAssetPath(guid);
            string modelo = Path.GetFileNameWithoutExtension(rutaFbx);

            // Una subcarpeta por modelo: así "Sueter" de Votante_Mujer y de Votante_Hombre no se pisan.
            string carpeta = $"Assets/Materiales/{modelo}";
            if (!AssetDatabase.IsValidFolder("Assets/Materiales")) AssetDatabase.CreateFolder("Assets", "Materiales");
            if (!AssetDatabase.IsValidFolder(carpeta)) AssetDatabase.CreateFolder("Assets/Materiales", modelo);

            // Los materiales "encerrados" dentro del FBX son sub-assets del archivo.
            foreach (var asset in AssetDatabase.LoadAllAssetsAtPath(rutaFbx))
            {
                if (asset is not Material mat) continue;
                string destino = $"{carpeta}/{mat.name}.mat";
                // ExtractAsset copia el material a un .mat editable y le dice al FBX
                // que use esa copia (es exactamente lo que hace el botón de Unity).
                string error = AssetDatabase.ExtractAsset(mat, destino);
                if (string.IsNullOrEmpty(error)) total++;
                else Debug.LogWarning($"{modelo}/{mat.name}: {error}");
            }

            // Reimportar para que el FBX empiece a usar los materiales extraídos.
            AssetDatabase.WriteImportSettingsIfDirty(rutaFbx);
            AssetDatabase.ImportAsset(rutaFbx, ImportAssetOptions.ForceUpdate);
        }
        AssetDatabase.Refresh();
        Debug.Log($"Listo: {total} materiales extraídos en Assets/Materiales.");
    }
}
#endif
