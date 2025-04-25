# Sociecos Publications - ETL Scripts

This repository contains two Python scripts for managing scientific publications of the **Sociecos** research group. They are designed to fetch publications from ORCID and prepare the data for import into Sanity.io.

## Scripts

### 1. `getOrcids.py`

**Purpose:**

- Connects to the ORCID API to retrieve all DOIs for the researchers defined in the `orcid_map` dictionary.
- Generates a `orcid_dois.json` file containing a list of all unique DOIs.

**Usage:**
```bash
python getOrcids.py
```

**Output:**
- `orcid_dois.json`

---

### 2. `generateSanityNDJSON.py`

**Purpose:**

- Reads the list of DOIs from `orcid_dois.json`.
- Fetches metadata for each publication from the Crossref API.
- Formats each publication according to the structure required by Sanity.
- Automatically links known researchers to their Sanity documents via the `researcherRef` field.
- Saves the result into an `.ndjson` file ready for import.

**Usage:**
```bash
python generateSanityNDJSON.py
```

**Output:**
- `publicaciones_sanity.ndjson`

**Import into Sanity:**
```bash
sanity dataset import publicaciones_sanity.ndjson production --replace
```

---

## Output structure for Sanity

Each publication will have the following format:

```json
{
  "_id": "doi-xxxx",
  "_type": "publication",
  "title": "Publication Title",
  "authors": [
    {
      "_type": "author",
      "_key": "unique_key",
      "name": "Surname, Initials",
      "researcherRef": {
        "_type": "reference",
        "_ref": "Sanity Researcher ID"
      }
    },
    ...
  ],
  "year": 2023,
  "journal": "Journal Name",
  "doi": "https://doi.org/xxxx"
}
```

*Fields such as `volume`, `issue`, `pages`, or `articleNumber` are included if available.*

---

## Important Notes

- If an error occurs while processing a DOI (e.g., it does not exist in Crossref), the script will log it in the terminal and continue with the remaining DOIs.
- Author-researcher linking is performed by matching normalized names using the `name_to_id_variants` dictionary.
- Importing into Sanity uses the `--replace` flag, meaning documents with the same `_id` will be updated rather than duplicated.

---

## Requirements

- Python 3.7+
- Libraries:
  - `requests`
  - `uuid`
  - `unicodedata`

You can install the required libraries using:
```bash
pip install requests
```

---

## Contact

For any questions or improvements, contact the Sociecos development team or open an issue in the repository.


