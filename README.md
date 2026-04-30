# Genialrag

Pipeline RAG (Retrieval-Augmented Generation) expérimentale pour poser des
questions à une base documentaire (PDF + TXT). Indexation locale via ChromaDB,
embeddings `bge-m3` et génération `DeepSeek-V3-0324-TEE` via Chutes.

## Prérequis

- Python 3.10+
- Un compte [Chutes](https://chutes.ai) avec une clé API
- Les modèles `BAAI/bge-m3` et `deepseek-ai/DeepSeek-V3-0324-TEE` accessibles
  sur ton compte Chutes

## Installation

```bash
git clone <repo>
cd Genialrag
python -m venv .venv
source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Crée un fichier `.env` à la racine du projet :

```
CHUTES_API_KEY=ta_cle_chutes_ici
```

(Tu peux copier `.env.example` comme point de départ.)

## Utilisation

### 1. Mettre des documents dans `data/`

```bash
mkdir -p data
cp /chemin/vers/mes_documents/*.pdf data/
cp /chemin/vers/mes_documents/*.txt data/
```

### 2. Indexer

```bash
python ingest.py
```

Cela va lire tous les PDF/TXT de `data/`, les découper en chunks, calculer les
embeddings via Chutes, et les stocker dans `chroma_db/`.

L'indexation est **incrémentale** : chaque chunk est associé à un hash de son
contenu. Les ré-exécutions ne ré-embedent que les chunks nouveaux ou modifiés
et suppriment les chunks orphelins (issus de fichiers supprimés, renommés ou
raccourcis). Relancer `ingest.py` sans changement = 0 appel API.

### 3. Poser des questions

```bash
python ask.py
```

Cela ouvre une boucle interactive. Chaque question est traitée indépendamment
(pas de mémoire conversationnelle pour le moment). Tape `quit` ou `Ctrl+C` pour
sortir.

## Structure

```
Genialrag/
├── data/                # Tes PDF et TXT (gitignored)
├── chroma_db/           # Base vectorielle persistée (auto-générée, gitignored)
├── src/
│   ├── loader.py        # Lecture PDF + TXT
│   ├── chunker.py       # Découpage en chunks + hash de contenu
│   ├── llm_client.py    # Appels Chutes (← seul fichier à modifier pour
│   │                    #   pointer vers d'autres APIs)
│   ├── vectorstore.py   # Wrapper ChromaDB
│   └── rag.py           # Logique RAG (retrieval + prompt + génération)
├── ingest.py            # CLI d'indexation incrémentale
├── ask.py               # CLI de questions
└── tests/               # Tests unitaires (pytest)
```

## Paramètres clés à expérimenter

| Paramètre | Fichier | Défaut | Effet |
|---|---|---|---|
| `chunk_size` | `chunker.py` | 800 | Taille d'un chunk en caractères |
| `overlap` | `chunker.py` | 100 | Chevauchement entre chunks |
| `top_k` | `rag.py` | 4 | Nombre de chunks retournés à la recherche |
| `temperature` | `llm_client.py` | 0.3 | Aléa du LLM (bas = factuel) |
| `EMBED_BATCH_SIZE` | `ingest.py` | 32 | Textes par requête d'embedding |

## Tests

```bash
pytest -v
```

## Migration vers d'autres APIs

Pour utiliser d'autres APIs (par exemple les APIs maison sur un autre PC),
modifie uniquement `src/llm_client.py` :

- Mets à jour `EMBED_URL`, `GEN_URL`, `GEN_MODEL`
- Si l'API n'est pas OpenAI-compatible, ajuste le parsing des réponses JSON
  dans `embed_texts()` et `generate()`
- Adapte la variable d'environnement utilisée pour le token si nécessaire

Aucun autre fichier n'a besoin d'être modifié.
