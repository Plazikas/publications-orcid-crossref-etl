import requests
import json
import uuid
import re
import unicodedata
from time import sleep

# === CONFIGURACIÓN ===
ruta_dois = "Escritorio/ETLProjects/PickingPublications/orcid_dois.json"
salida_ndjson = "Escritorio/ETLProjects/PickingPublications/publicaciones_sanity.ndjson"

# === MAPEO DE VARIANTES DE NOMBRES A _id EN SANITY ===
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
    "018e793e-15d7-438a-bb87-b78c1d930718": [
        "Daniela Alba-Patiño", "Alba‐Patiño, D.", "Alba-Patiño, D."
    ],
    "0377cf17-b13a-4b86-849f-fdd3fc859dcb": [
        "Sean Goodwin", "Goodwin, S."
    ],
    "089ba7cb-022a-4bde-81de-dd5c7dc30564": [
        "Enrica Garau", "Garau, E."
    ],
    "3daa5e46-45ae-475a-969b-86c3376c26c5": [
        "Álvaro Peláez"
    ],
    "0ebc2895-1546-4201-84cf-c590718158c0": [
        "Dainee Gibson"
    ],
    "12e946b0-b797-499e-9fe1-d8e49fda783c": [
        "Miguel Delibes-Mateos", "Delibes‐Mateos, M."
    ],
    "204f3b96-7704-4974-ae64-0d65738dda54": [
        "Colden V. Baxter", "Baxter, C. V."
    ],
    "2dd600b7-ce16-4bc8-896d-39826d116e80": [
        "Berta Martín López", "Martín-López, B."
    ],
    "5cb5f00f-bed8-49bb-bfc4-6dd7f7948856": [
        "Amanda Jiménez Aceituno", "Jiménez-Aceituno, A.", "Aceituno, A. J."
    ],
    "60726631-b6ad-408d-a8bb-5085252e09c6": [
        "Mario Soliño", "Soliño, M."
    ],
    "6d75dc97-06ac-486e-a909-845f1ee24862": [
        "Jodi Brandt", "Brandt, J."
    ],
    "94f34ebc-5729-4885-8e70-b33f306cc699": [
        "Irene Otamendi Urroz", "Otamendi-Urroz, I.", "Otamendi Urroz, I."
    ],
    "997981c4-1301-42dd-b54f-5b22df9ae554": [
        "Albert Norström", "Norström, A."
    ],
    "a0a990f8-4ffd-4805-96f3-8b09405739e3": [
        "Youssra El Ghafraoui", "El Ghafraoui, Y."
    ],
    "ac7b676c-707a-4ba5-9687-8098d29efa6c": [
        "Adam Eckersell", 
    ],
    "b7f6c792-d5d7-405e-841c-1a67ba3e9090": [
        "Maria D. Lopez Rodriguez", "López-Rodríguez, M. D.", "López-Rodriguez, M. D.",
        "López-Rodríguez, M."
    ],
    "c7b16428-b053-4456-8ec8-41a9a118a369": [
        "Trina Running", "Running, K."
    ],
    "e24af4bb-575d-4b47-896b-fdc32f85bdfa": [
        "Victor Galaz", "Galaz, V."
    ],
    "e61ebf47-dc9a-43a4-8549-f1d169e55fdd": [
        "Ana Paula Aguiar", "Aguiar, A. P. D.", "Aguiar, A. P."
    ],
    "f1686143-0f47-458c-a234-224aacb0026c": [
        "Caryn C. Vaughn", "Vaughn, C. C."
    ]
}

# === FUNCIONES AUXILIARES ===
def normalize_author_name(name: str) -> str:
    name = unicodedata.normalize("NFKC", name)
    name = name.replace("‐", "-").replace("–", "-").replace("—", "-")
    name = name.lower().strip()
    return " ".join(name.split())

def to_int_or_none(value):
    try:
        return int(value)
    except:
        return None

def get_crossref_data(doi: str) -> dict:
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["message"]
    else:
        raise Exception(f"{response.status_code} - {response.text}")

# === LECTURA DE DOIS ===
with open(ruta_dois, "r", encoding="utf-8") as f:
    dois = json.load(f)

# === PROCESAR Y GUARDAR PUBLICACIONES ===
with open(salida_ndjson, "w", encoding="utf-8") as f_out:
    for idx, doi in enumerate(sorted(dois), 1):
        try:
            print(f"[{idx}/{len(dois)}] Procesando DOI: {doi}")
            data = get_crossref_data(doi)

            # Procesar autores
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

            f_out.write(json.dumps(pub, ensure_ascii=False) + "\n")
            sleep(1)

        except Exception as e:
            print(f"❌ Error con DOI {doi}: {e}")

print("\n✅ Fichero NDJSON generado correctamente.")