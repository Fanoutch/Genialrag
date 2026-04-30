# Mise en production — guide de configuration

Ce document décrit **où** et **comment** modifier la configuration de la
pipeline pour pointer vers d'autres modèles (LLM ou embedding) en production.

---

## TL;DR

| Tu veux changer… | Fichier à modifier | Re-indexation nécessaire ? |
|---|---|---|
| Le **token d'API** | `.env` | Non |
| Le **LLM** (génération) | `src/llm_client.py` | **Non** |
| Le **modèle d'embedding** | `src/llm_client.py` | **Oui — TOUT** |
| Les **URLs des endpoints** | `src/llm_client.py` | Selon le cas |

**Règle d'or** : tout sauf le token est dans `src/llm_client.py`. C'est le
**seul fichier** à modifier pour migrer.

---

## Architecture des points de configuration

### Secrets → fichier `.env` (gitignored, jamais commit)

```bash
# .env à la racine du projet
CHUTES_API_KEY=ton_token_ici
```

### Configuration → `src/llm_client.py`

```python
EMBED_URL = "https://chutes-baai-bge-m3.chutes.ai/v1/embeddings"
GEN_URL   = "https://llm.chutes.ai/v1/chat/completions"
GEN_MODEL = "deepseek-ai/DeepSeek-V3-0324-TEE"

EMBED_DIM = 1024  # dimension des vecteurs bge-m3
```

Tout est centralisé ici par design — c'est explicite dans le spec :
> "un seul fichier à modifier pour pointer vers d'autres APIs"

---

## Changer le LLM (sans re-indexer)

Le LLM ne touche **jamais** aux vecteurs stockés dans ChromaDB. Il prend juste
le prompt + chunks récupérés et génère une réponse. Tu peux le changer à
chaud sans aucun impact sur la base.

### Fichier : `src/llm_client.py`

Modifie ces deux constantes :

```python
GEN_URL   = "https://llm.chutes.ai/v1/chat/completions"   # ← endpoint
GEN_MODEL = "deepseek-ai/DeepSeek-V3-0324-TEE"            # ← nom du modèle
```

Et éventuellement le payload dans `generate()` si le format diffère :

```python
payload = {
    "model": GEN_MODEL,
    "messages": [{"role": "user", "content": prompt}],
    "stream": False,
    "max_tokens": 1024,
    "temperature": 0.3,
}
```

Et le parsing de la réponse (ligne dans `generate()`) :

```python
return data["choices"][0]["message"]["content"]
```

### Cas concrets

#### A) Autre modèle sur Chutes (ex: Llama 3 70B)

Une seule ligne :

```python
GEN_MODEL = "meta-llama/Meta-Llama-3-70B-Instruct"
```

`GEN_URL` et le format de payload/parsing restent identiques (Chutes est
OpenAI-compatible sur tous ses modèles).

#### B) API maison (autre PC)

Si l'API maison est OpenAI-compatible :

```python
GEN_URL   = "http://192.168.1.42:8080/v1/chat/completions"  # ← ton endpoint
GEN_MODEL = "nom-de-ton-modele"                              # ← si requis
```

Si le format diffère, ajuste le `payload` ET la ligne de parsing.

Si le token a un autre nom :
```python
# Dans .env
HOME_API_TOKEN=xxx

# Dans llm_client.py
CHUTES_API_KEY = os.getenv("HOME_API_TOKEN")  # renommer la var
```

#### C) Fournisseur tiers (OpenAI, Anthropic, etc.)

**OpenAI** :
```python
GEN_URL   = "https://api.openai.com/v1/chat/completions"
GEN_MODEL = "gpt-4o"
# Format identique (Chutes copie le format OpenAI), aucun changement de payload
```

**Anthropic** :
```python
GEN_URL   = "https://api.anthropic.com/v1/messages"
GEN_MODEL = "claude-sonnet-4-6"
# Format DIFFÉRENT — le payload et le parsing doivent être adaptés
# Voir https://docs.anthropic.com/en/api/messages
```

---

## Changer le modèle d'embedding (RE-INDEXATION OBLIGATOIRE)

⚠️ **Attention** : le modèle d'embedding détermine la **forme** et le **sens
mathématique** des vecteurs. Si tu changes de modèle :

- Les vecteurs déjà stockés deviennent **inutilisables**
- Comparer un nouveau vecteur (modèle B) à un ancien (modèle A) n'a aucun sens
- La recherche RAG donnera des résultats incohérents

### Procédure

1. **Modifier `src/llm_client.py`** :
   ```python
   EMBED_URL = "<nouvel_endpoint>"
   EMBED_DIM = <nouvelle_dimension>  # ex: 1536 pour ada-002, 768 pour MiniLM
   ```

2. **Ajuster `embed_texts()`** si le format diffère.

3. **SUPPRIMER l'ancienne base** :
   ```bash
   rm -rf chroma_db/
   ```

4. **Ré-indexer tous les documents** :
   ```bash
   python ingest.py
   ```

### Quand garder `bge-m3` même en prod

`bge-m3` est un excellent choix pour la production :
- **Multilingue** (excellent en français)
- **Dim 1024** : bon ratio qualité / taille
- **Open source** : tu peux l'auto-héberger sans dépendre de Chutes
- **Stable et reproductible** : les vecteurs ne changent pas entre versions

Garde-le tant que tu n'as pas une raison forte de changer (ex: contrainte de
performance, modèle plus performant pour ton domaine).

---

## Checklist de migration

### Si tu changes uniquement le LLM (cas le plus courant)

- [ ] Modifier `GEN_URL` et `GEN_MODEL` dans `src/llm_client.py`
- [ ] Ajuster `payload` et le parsing dans `generate()` si nécessaire
- [ ] Mettre à jour le token dans `.env` si un nouveau token est requis
- [ ] Tester avec `python ask.py` (pas besoin de re-indexer)
- [ ] Commit le changement de `llm_client.py`

### Si tu changes l'embedding

- [ ] Modifier `EMBED_URL` et `EMBED_DIM` dans `src/llm_client.py`
- [ ] Ajuster `embed_texts()` si le format diffère
- [ ] Mettre à jour le token dans `.env` si un nouveau token est requis
- [ ] **Supprimer `chroma_db/`** (`rm -rf chroma_db/`)
- [ ] Ré-indexer : `python ingest.py`
- [ ] Tester avec `python ask.py`
- [ ] Commit le changement de `llm_client.py`

### Si tu changes les deux (ex: bascule complète sur APIs maison)

- [ ] Toutes les étapes ci-dessus
- [ ] Vérifier que les nouveaux modèles sont accessibles depuis la machine
- [ ] Tester avec un petit corpus avant de traiter tous les docs

---

## Pourquoi cette architecture

Le design impose ces contraintes :

1. **Aucun secret dans le code** → token toujours en `.env`
2. **Aucune configuration dans `.env`** → URLs/modèles toujours dans le code
3. **Un seul fichier de migration** → `src/llm_client.py` est le seul point de
   contact avec les APIs externes

Cette discipline garantit qu'une migration de prod est :
- **Traçable** (un commit = un changement de config)
- **Reproductible** (un autre dev peut refaire le même changement)
- **Sûre** (pas de divergence silencieuse entre machines)
