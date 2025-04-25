import requests
import json
import unicodedata
from time import sleep

# === CONFIGURACIÓN DE INVESTIGADORES ===
orcid_map = {
    "0000-0003-1587-8564": "Antonio J. Castro",
    "0000-0002-3437-7629": "Cristina Quintas Soriano",
    "0000-0002-5120-7947": "Juan M. Requena-Mullor",
    "0000-0003-1405-8126": "Daniela Alba-Patiño",
    "0000-0001-8968-8160": "Sean Goodwin",
    "0000-0003-3706-8431": "Enrica Garau",
    "0009-0000-4234-6964": "Álvaro Peláez",
    "0000-0002-3087-5268": "Irene Otamendi Urroz",
    "0009-0002-5176-402X": "Youssra El Ghafraoui",
    "0000-0003-2401-8929": "Maria D. Rodríguez López"
}

# === FUNCIONES ===
def get_dois_from_orcid(orcid_id: str) -> list:
    headers = {'Accept': 'application/vnd.orcid+json'}
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"[ERROR] No se pudo obtener datos para ORCID {orcid_id}")
        return []

    works = response.json().get("group", [])
    dois = set()
    for work in works:
        external_ids = work.get("external-ids", {}).get("external-id", [])
        for eid in external_ids:
            if eid.get("external-id-type") == "doi":
                doi = eid.get("external-id-value")
                if doi:
                    clean_doi = doi.lower().replace("https://doi.org/", "").strip()
                    dois.add(clean_doi)
    return list(dois)

# === RUTA DE SALIDA ===
ruta_dois = "Escritorio/ETLProjects/PickingPublications/orcid_dois.json"

# === EJECUCIÓN PRINCIPAL ===
all_dois = set()
per_author_dois = {}

print("📡 Obteniendo DOIs desde ORCID...")
for orcid in orcid_map.keys():
    nombre = orcid_map[orcid]
    print(f"🔍 {nombre} ({orcid})...")
    dois = get_dois_from_orcid(orcid)
    per_author_dois[nombre] = dois
    all_dois.update(dois)
    sleep(1)

# Guardamos solo el listado 
with open(ruta_dois, "w", encoding="utf-8") as f_out:
    json.dump(sorted(list(all_dois)), f_out, ensure_ascii=False, indent=2)

print("\n✅ Fichero generado:")
print(f"— DOIs guardados en: {ruta_dois}")
