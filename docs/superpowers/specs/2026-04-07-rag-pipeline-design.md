# Design — Pipeline RAG expérimentale (Genialrag)

**Date** : 2026-04-07
**Statut** : Validé, prêt pour planification d'implémentation

## Contexte

Construire une pipeline RAG (Retrieval-Augmented Generation) expérimentale pour
poser des questions à une base documentaire. Le projet est volontairement
minimaliste : il sert de banc d'essai pour comprendre le fonctionnement d'un
RAG bout en bout avant d'envisager une version production.

**Contexte API** : les APIs maison de l'utilisateur (génération + embeddings) ne
sont pas accessibles depuis cette machine de développement. Pour pouvoir tester
la pipeline en local avec de **vrais** modèles, on utilise **Chutes**
(chutes.ai) qui héberge `bge-m3` et `DeepSeek-V3-0324-TEE` accessibles via API
HTTP OpenAI-compatible. Sur l'autre PC, l'utilisateur pourra plus tard
remplacer les URLs Chutes par celles de ses APIs maison — un seul fichier à
modifier.

## Objectifs

- Indexer des documents PDF et TXT dans une base vectorielle
- Permettre de poser des questions en CLI et obtenir une réponse avec les
  sources citées
- Rester simple, lisible, sans framework lourd
- Tester avec de **vrais** modèles via Chutes (`bge-m3` + `DeepSeek-V3-0324-TEE`)
- Faciliter le transfert vers un autre PC : un seul fichier à modifier pour
  pointer vers d'autres APIs (les APIs maison de l'utilisateur)

## Hors scope (V1)

- Mémoire conversationnelle multi-tours (V2 si V1 concluante)
- Formats autres que PDF/TXT (docx, html, etc.)
- Interface web (Gradio/Streamlit)
- Re-ranking, query expansion, chunking sémantique avancé
- Tests automatisés exhaustifs (le projet est expérimental)

## Décisions techniques

| Sujet | Choix | Justification |
|---|---|---|
| Langage | Python vanilla | Pas de framework lourd ; on contrôle chaque étape |
| Vector DB | ChromaDB (`PersistentClient`) | Local, zéro config, persistance fichier, métadonnées |
| Modèle d'embedding | `bge-m3` via Chutes (endpoint dédié) | Multilingue, dim 1024, dispo sur Chutes |
| Modèle de génération | `deepseek-ai/DeepSeek-V3-0324-TEE` via Chutes | Excellent en français, gros contexte, instruction-following solide, exécution en TEE (confidentialité) |
| Authentification Chutes | Token via variable d'env `CHUTES_API_TOKEN` | Pas de clé en dur dans le code |
| Lecture PDF | `pypdf` | Léger, pip install simple, suffisant pour V1 |
| Interface | CLI (deux scripts) | Friction minimale pour tester |
| Stratégie de chunking | Caractères, taille 800, overlap 100 | Simple et raisonnable pour `bge-m3` |

## Architecture

### Structure du projet

```
Genialrag/
├── data/                  # Documents source (PDF/TXT) à indexer
├── chroma_db/             # Base vectorielle persistée (auto-générée)
├── src/
│   ├── loader.py          # Lecture PDF + TXT → documents normalisés
│   ├── chunker.py         # Découpage en chunks
│   ├── llm_client.py      # Stubs API (mode faux ↔ vrai)
│   ├── vectorstore.py     # Wrapper ChromaDB
│   └── rag.py             # Logique retrieval + prompt + génération
├── ingest.py              # CLI : indexation
├── ask.py                 # CLI : questions interactives (one-shot)
├── requirements.txt
└── README.md
```

### Flux de données

```
Indexation :
  [PDF/TXT dans data/] → loader → chunker → embed_texts → ChromaDB

Interrogation :
  [Question] → embed_texts → search → prompt → generate → [Réponse + sources]
```

## Composants

### 1. `src/loader.py` — Chargement des documents

**Rôle** : lire les fichiers de `data/` (récursivement) et les transformer en
une liste d'objets uniformes.

**Format de sortie** :
```python
{
    "source": "data/manuel.pdf",   # chemin relatif
    "page": 3,                     # numéro de page (None pour TXT)
    "text": "contenu du texte..."
}
```

**Détails** :
- PDF : `pypdf` ; un PDF produit plusieurs entrées (une par page) pour
  permettre la citation à la page près.
- TXT : un fichier produit une entrée unique avec `page=None`.
- Parcours récursif de `data/`, filtré sur extensions `.pdf` et `.txt`.

### 2. `src/chunker.py` — Découpage en chunks

**Rôle** : découper chaque document en morceaux de taille adaptée au modèle
d'embedding.

**Stratégie** : découpage par caractères avec chevauchement.
- Taille : 800 caractères
- Overlap : 100 caractères
- Le chevauchement évite qu'une phrase importante soit coupée à la frontière.

**Format de sortie** :
```python
{
    "chunk_id": "manuel.pdf_p3_c0",   # ID unique stable
    "source": "data/manuel.pdf",
    "page": 3,
    "text": "morceau de 800 caractères..."
}
```

**Notes** :
- L'ID est dérivé du fichier, de la page et de l'index du chunk dans la page.
  Stable d'une exécution à l'autre → la ré-indexation écrase au lieu de
  dupliquer.
- Stratégie volontairement simple. Si la qualité de récupération est mauvaise,
  on pourra évoluer (chunking par phrases/paragraphes, semantic chunking).

### 3. `src/llm_client.py` — Client LLM (cœur de la portabilité)

**Rôle** : isoler tous les appels API. **Seul fichier à modifier pour pointer
vers d'autres APIs plus tard (APIs maison sur l'autre PC).**

**Interface publique** :
```python
def embed_texts(texts: list[str]) -> list[list[float]]:
    """Liste de textes → liste de vecteurs (dimension 1024 pour bge-m3)."""

def generate(prompt: str) -> str:
    """Prompt complet → réponse texte du LLM."""
```

**Implémentation V1 : appels Chutes**

Configuration en haut du fichier :
```python
CHUTES_API_TOKEN = os.getenv("CHUTES_API_TOKEN")
EMBED_URL = "https://chutes-baai-bge-m3.chutes.ai/v1/embeddings"
GEN_URL   = "https://llm.chutes.ai/v1/chat/completions"
GEN_MODEL = "deepseek-ai/DeepSeek-V3-0324-TEE"
```

Si `CHUTES_API_TOKEN` est absent au démarrage : message d'erreur clair
demandant de définir la variable d'environnement (`export CHUTES_API_TOKEN=...`
ou via fichier `.env` chargé avec `python-dotenv`).

**`embed_texts(texts)`** :
- POST sur `EMBED_URL` avec headers `Authorization: Bearer <token>` et
  `Content-Type: application/json`.
- Body : `{"input": texts, "model": null}` (l'endpoint est dédié à `bge-m3`,
  `model` est `null` par convention de l'API Chutes pour cet endpoint).
- Parsing : la réponse suit le format OpenAI embeddings,
  `response["data"][i]["embedding"]` pour chaque texte.
- Retourne la liste des vecteurs dans l'ordre des textes d'entrée.
- Gestion d'erreur : si le statut HTTP n'est pas 2xx, lever une exception avec
  le code et le corps de la réponse pour faciliter le debug.

**`generate(prompt)`** :
- POST sur `GEN_URL` avec mêmes headers.
- Body :
  ```json
  {
    "model": "deepseek-ai/DeepSeek-V3-0324-TEE",
    "messages": [{"role": "user", "content": "<prompt complet>"}],
    "stream": false,
    "max_tokens": 1024,
    "temperature": 0.3
  }
  ```
- `stream: false` pour récupérer la réponse complète d'un coup (plus simple en
  CLI ; on pourra activer le streaming en V2).
- `temperature: 0.3` (basse) car en RAG on veut des réponses factuelles, pas
  créatives.
- Parsing : `response["choices"][0]["message"]["content"]`.
- Retourne la chaîne de caractères de la réponse.

**Migration vers d'autres APIs (autre PC)** : seules les constantes
`EMBED_URL`, `GEN_URL`, `GEN_MODEL` et éventuellement la structure du body
sont à modifier. Si l'API maison est aussi OpenAI-compatible, c'est trivial.
Sinon, ajuster le parsing dans les deux fonctions.

### 4. `src/vectorstore.py` — Wrapper ChromaDB

**Rôle** : encapsuler ChromaDB derrière une interface minimale pour pouvoir le
remplacer plus tard (Qdrant, etc.) sans toucher au reste du code.

**Interface publique** :
```python
class VectorStore:
    def __init__(self, persist_dir: str = "chroma_db"): ...
    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> None: ...
    def search(self, query_embedding: list[float], top_k: int = 4) -> list[dict]: ...
```

**Détails** :
- `PersistentClient(path="chroma_db")` : la base est créée automatiquement au
  premier appel si elle n'existe pas.
- Une seule collection `"documents"`.
- Métadonnées stockées : `source`, `page`. Permet de citer la source dans la
  réponse.
- ID Chroma = `chunk_id` du chunker. Ré-indexation → upsert (pas de doublons).
- `search` retourne une liste de dicts `{chunk_id, source, page, text, distance}`
  triés par pertinence décroissante.
- **Le module ne calcule pas les embeddings** : il reçoit les vecteurs déjà
  calculés. Séparation des responsabilités.

### 5. `src/rag.py` — Logique RAG

**Rôle** : orchestrer une requête de bout en bout.

**Interface publique** :
```python
def answer_question(
    question: str,
    vectorstore: VectorStore,
    top_k: int = 4,
) -> dict:
    """Retourne {"answer": str, "sources": list[dict]}."""
```

**Étapes internes** :
1. Embedder la question (`embed_texts([question])[0]`).
2. Chercher les `top_k` chunks les plus proches (`vectorstore.search`).
3. Construire le prompt (template ci-dessous).
4. Appeler `generate(prompt)`.
5. Retourner la réponse + la liste structurée des sources utilisées.

**Template de prompt** :
```
Tu es un assistant qui répond à des questions en te basant UNIQUEMENT
sur les extraits de documentation fournis ci-dessous.
Si la réponse n'est pas dans les extraits, dis "Je ne sais pas".
Cite les sources sous la forme [source: nom_fichier, page X].

EXTRAITS :
---
[Extrait 1 — source: manuel.pdf, page 3]
<texte du chunk 1>
---
[Extrait 2 — source: guide.txt]
<texte du chunk 2>
---
...

QUESTION : <la question de l'utilisateur>

RÉPONSE :
```

**Choix de design du prompt** :
- Instruction explicite "uniquement à partir des extraits" → réduit les
  hallucinations.
- "Je ne sais pas" autorisé → RAG honnête.
- Sources visibles dans le prompt → le LLM peut citer naturellement.
- Délimiteurs `---` → aident le LLM à séparer les extraits.
- Sources retournées séparément en plus du texte → le CLI les affiche
  proprement, même si le LLM oublie de citer.

### 6. CLI — `ingest.py` et `ask.py`

Volontairement minces : ils orchestrent les modules sans logique métier.

#### `ingest.py`

**Usage** :
```bash
python ingest.py
python ingest.py --data-dir autres_docs/    # optionnel
```

**Étapes** :
1. `loader.load_documents(data_dir)`
2. `chunker.chunk_documents(docs)`
3. Embedding par batches de 32 (`llm_client.embed_texts`)
4. `vectorstore.add_chunks(chunks, embeddings)`
5. Récap final : `"Indexé N chunks depuis K fichiers en Ts"`

**UX** : affichage textuel de progression à chaque étape.

#### `ask.py`

**Usage** :
```bash
python ask.py
```

**Comportement** :
- Boucle interactive : question → réponse → re-question. Sortie via `Ctrl+C`
  ou en tapant `quit`.
- Pour chaque question :
  1. `rag.answer_question(question, vectorstore)`
  2. Afficher la réponse
  3. Afficher la liste compacte des sources :
     ```
     Sources :
       - manuel.pdf (page 3)
       - guide.txt
       - manuel.pdf (page 7)
     ```
- **One-shot strict** : aucune mémoire entre les questions. La boucle est un
  simple confort UX.

**Erreur courante gérée** : si la base ChromaDB est vide ou inexistante,
afficher `"Base vectorielle vide. Lance d'abord python ingest.py"`.

## Dépendances

`requirements.txt` :
```
pypdf
chromadb
requests
python-dotenv
```

- `pypdf` : lecture des PDF
- `chromadb` : base vectorielle locale
- `requests` : appels HTTP vers Chutes
- `python-dotenv` : chargement de `CHUTES_API_TOKEN` depuis un fichier `.env`

## Workflow utilisateur

### Sur ce PC (test avec Chutes)

1. `pip install -r requirements.txt`
2. Créer un fichier `.env` à la racine avec :
   ```
   CHUTES_API_TOKEN=<ton_token_chutes>
   ```
   (`.env` doit être ajouté à `.gitignore` pour ne jamais commiter le token.)
3. Mettre quelques fichiers de test (PDF + TXT) dans `data/`
4. `python ingest.py` → indexation avec vrais embeddings `bge-m3`
5. `python ask.py` → vraies réponses générées par DeepSeek V3

### Sur l'autre PC (APIs maison)

1. Transférer le projet
2. `pip install -r requirements.txt`
3. Ouvrir `src/llm_client.py` :
   - Modifier les constantes `EMBED_URL`, `GEN_URL`, `GEN_MODEL`
   - Ajuster le parsing si l'API n'est pas OpenAI-compatible
   - Adapter la variable d'env utilisée pour le token si différente
4. Mettre les documents dans `data/`
5. `python ingest.py` puis `python ask.py`

## Critères de succès

- La pipeline tourne bout en bout en mode faux sur ce PC sans erreur.
- Indexer plusieurs PDF + TXT crée bien une base ChromaDB persistante.
- Re-lancer `ingest.py` deux fois ne crée pas de doublons (upsert via
  `chunk_id` stable).
- Sur l'autre PC, après modification de `llm_client.py` uniquement, la
  pipeline produit des réponses cohérentes citant les bonnes sources.

## Évolutions envisagées (V2+)

- Mémoire conversationnelle multi-tours
- Support de formats supplémentaires (docx, html, etc.)
- Chunking plus intelligent (par phrase/paragraphe ou sémantique)
- Re-ranking des résultats
- Migration vers une vector DB plus robuste (Qdrant) quand le volume augmente
- Streaming des réponses (`stream: true`) pour effet "ChatGPT" en temps réel
- Bascule sur les APIs maison de l'utilisateur (transfert sur l'autre PC)

## Cible long terme (production)

L'objectif final est une **application Windows** avec le chatbot intégré
(installateur, fenêtre native ou web embarquée). Implications à garder en tête
dès la V1 :

- **Packaging** : la pipeline doit pouvoir tourner en standalone (PyInstaller,
  Tauri + Python embarqué, ou solution équivalente). Éviter toute dépendance
  qui ne packagerait pas bien sous Windows.
- **Interface** : la CLI V1 sera remplacée par une UI graphique. La séparation
  actuelle (`rag.py` = logique pure, `ask.py` = présentation CLI) facilite
  cette transition — il suffira de remplacer `ask.py` par un front graphique
  qui appelle les mêmes fonctions.
- **Base vectorielle** : ChromaDB en mode `PersistentClient` est compatible
  Windows et embarquable, donc pas de blocage. Migration éventuelle vers SQLite
  + sqlite-vec si on veut un seul fichier base de données.
- **APIs** : la version production utilisera probablement les APIs maison de
  l'utilisateur (pas Chutes). Le design actuel — un seul fichier
  `llm_client.py` à modifier — supporte déjà ce changement.
- **Configuration** : prévoir un mécanisme de config plus user-friendly que
  `.env` (fichier de paramètres dans `%APPDATA%`, dialogue de première
  configuration dans l'UI, etc.).
