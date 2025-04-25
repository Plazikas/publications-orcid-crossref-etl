import requests
import json
import uuid
import unicodedata
import re
from time import sleep

# === CONFIGURACIÓN DE INVESTIGADORES Y VARIANTES ===
name_to_id_variants = {
    "f1097c1f-ea46-43d6-a4fc-7e4b945fa924": [
        "Antonio J. Castro", "Antonio José Castro", "Castro, Antonio", "Castro, A. J.",
        "Castro A. J.", "Castro, A.", "Castro, A. A."
    ],
    "4d0e0d6f-fa33-4dda-880e-5ad002717954": [
        "Cristina Quintas-Soriano", "C. Quintas-Soriano", "Quintas-Soriano, Cristina", "Quintas-Soriano, C."
    ],
    "52bd00a7-c131-4fde-a752-5fba18b8ec89": [
        "Juan Miguel Requena-Mullor", "Juan M. Requena-Mullor", "Requena-Mullor, J. M.",
        "Requena Mullor, J. M.", "Requena-Mullor, J.", "Requena, J. M."
    ],


    
}

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

# === UTILIDADES ===
def normalize_author_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name)
    name = name.replace("‐", "-").replace("–", "-").replace("—", "-")
    name = name.lower().strip()
    return " ".join(name.split())

def get_crossref_data(doi: str) -> dict:
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["message"]
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

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

def to_int_or_none(value):
    try:
        return int(value)
    except:
        return None

# === RUTAS DE ARCHIVOS DE SALIDA ===
ruta_reporte = "Escritorio/ETLProjects/reporte_sociecos.txt"
ruta_ndjson = "Escritorio/ETLProjects/publicaciones_sanity.ndjson"
ruta_citas_apa = "Escritorio/ETLProjects/publicaciones_apa.txt"

# === FUNCIÓN PARA FORMATEAR EN FORMATO APA ===
def formatear_cita_apa(pub):
    if not pub.get("authors"):
        autores = "Sin autores"
    else:
        autores_lista = []
        for a in pub["authors"]:
            nombre = a["name"]
            autores_lista.append(nombre)
        if len(autores_lista) > 1:
            autores = ", ".join(autores_lista[:-1]) + ", & " + autores_lista[-1]
        else:
            autores = autores_lista[0]

    year = f"({pub['year']})" if pub.get("year") else "(s.f.)"
    titulo = f"{pub.get('title', '')}"
    revista = f"{pub.get('journal', '')}"
    
    info_volumen = ""
    if pub.get("volume"):
        info_volumen += str(pub["volume"])
    if pub.get("issue"):
        info_volumen += f"({pub['issue']})"
    if pub.get("pages"):
        info_volumen += f", {pub['pages']}"
    elif pub.get("articleNumber"):
        info_volumen += f", {pub['articleNumber']}"

    doi = pub.get("doi", "")

    return f"{autores} {year}. {titulo}. {revista}, {info_volumen}. {doi}"

# === EJECUCIÓN PRINCIPAL ===
orcid_ids = list(orcid_map.keys())
all_dois = set()
per_author_dois = {}
publicaciones = []

with open(ruta_reporte, "w", encoding="utf-8") as f_reporte, open(ruta_ndjson, "w", encoding="utf-8") as f_ndjson:
    print("📡 Consultando ORCID...")
    for orcid in orcid_ids:
        nombre = orcid_map[orcid]
        print(f"🔍 {nombre} ({orcid})...")
        dois = get_dois_from_orcid(orcid)
        per_author_dois[nombre] = dois
        all_dois.update(dois)
        sleep(1)

    print(f"\n🔢 Total DOIs únicos encontrados: {len(all_dois)}\n")

    for idx, doi in enumerate(sorted(all_dois), 1):
        try:
            print(f"📘 [{idx}/{len(all_dois)}] Procesando DOI: {doi}")
            data = get_crossref_data(doi)

            authors = []
            for a in data.get("author", []):
                given = a.get("given", "")
                family = a.get("family", "")
                initials = " ".join([n[0] + "." for n in given.split() if n])
                apa_name = f"{family}, {initials}".strip()

                entry = {
                    "_type": "author",
                    "_key": uuid.uuid4().hex[:12],
                    "name": apa_name
                }

                author_name_normalized = normalize_author_name(apa_name)
                for ref_id, variants in name_to_id_variants.items():
                    if any(normalize_author_name(v) in author_name_normalized for v in variants):
                        entry["researcherRef"] = {
                            "_type": "reference",
                            "_ref": ref_id
                        }
                        print(f"   🔗 Vinculado a: {apa_name} → {ref_id}")
                        break

                authors.append(entry)

            doi_id = "doi-" + re.sub(r"[^a-zA-Z0-9_-]", "_", data.get("DOI"))
            pub = {
                "_id": doi_id,
                "_type": "publication",
                "title": data.get("title", [""])[0],
                "authors": authors,
                "year": to_int_or_none(data.get("issued", {}).get("date-parts", [[None]])[0][0]),
                "journal": data.get("container-title", [""])[0],
                "doi": f"https://doi.org/{data.get('DOI')}"
            }

            if data.get("volume"):
                pub["volume"] = to_int_or_none(data.get("volume"))
            if data.get("issue"):
                pub["issue"] = to_int_or_none(data.get("issue"))
            if data.get("page"):
                if "-" in str(data.get("page")):
                    pub["pages"] = data.get("page")
                else:
                    pub["articleNumber"] = data.get("page")

            f_ndjson.write(json.dumps(pub, ensure_ascii=False) + "\n")
            f_reporte.write(f"{doi} — {pub['title']}\n")
            publicaciones.append(pub)
            sleep(1)

        except Exception as e:
            print(f"❌ Error al procesar DOI {doi}: {e}")
            f_reporte.write(f"❌ Error con DOI {doi}: {e}\n")

# === GUARDAR CITAS EN FORMATO APA ORDENADAS POR AÑO (DESCENDENTE) ===
publicaciones_ordenadas = sorted(
    [p for p in publicaciones if p.get("year")], 
    key=lambda x: x["year"], reverse=True
)

with open(ruta_citas_apa, "w", encoding="utf-8") as f_citas:
    for pub in publicaciones_ordenadas:
        cita = formatear_cita_apa(pub)
        f_citas.write(cita + "\n\n")

print("\n✅ Importación completada. Archivos generados:")
print(f"— Reporte: {ruta_reporte}")
print(f"— NDJSON para Sanity: {ruta_ndjson}")
print(f"— Citas en formato APA: {ruta_citas_apa}")
