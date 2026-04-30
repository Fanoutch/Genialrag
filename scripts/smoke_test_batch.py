"""Run a batch of test questions against the SECTORED RAG.

Each question is associated with the sector (collection) that should
contain its answer. Cross-domain tests verify that asking in the wrong
sector yields a clean "Je ne sais pas".

Usage:
    python -m scripts.smoke_test_batch
"""
from src.rag import answer_question
from src.vectorstore import VectorStore


# Each entry: (tag, sector, question, expected_to_answer)
# expected_to_answer = True if the chosen sector should contain the answer
QUESTIONS: list[tuple[str, str, str, bool]] = [
    # Niveau 🟢 — questions simples, scope correct
    ("S1", "medical",      "Quelle est la posologie maximale du paracétamol par 24h ?", True),
    ("S2", "comptabilite", "Quel est le taux normal de TVA en France ?",                True),
    ("S3", "restauration", "À quelle température conserver de la viande crue ?",        True),
    ("S4", "velo",         "Quelle est l'autonomie du vélo électrique ?",               True),
    # Niveau 🟡 — questions sur les NOUVEAUX fichiers
    ("N1", "comptabilite", "Comment calculer un amortissement linéaire ?",              True),
    ("N2", "juridique",    "Quelle est la durée de la période d'essai pour un cadre ?", True),
    ("N3", "medical",      "Comment reconnaître un AVC ?",                              True),
    ("N4", "restauration", "Combien d'allergènes obligatoires faut-il signaler ?",      True),
    ("N5", "informatique", "Qu'est-ce que la 2FA ?",                                    True),
    ("N6", "velo",         "Comment réparer une crevaison ?",                           True),
    ("N7", "patisserie",   "Comment tempérer du chocolat noir ?",                       True),
    ("N8", "jardinage",    "Comment composter à la maison ?",                           True),
    # Niveau 🟠 — D3 INSI, scopé médical
    ("D3", "medical",      "Que signifie INSI dans le médical ?",                       True),
    # Niveau 🔴 — questions hors corpus, "Je ne sais pas" attendu
    ("X1", "medical",      "Quel est le plus grand fleuve du monde ?",                  False),
    ("X2", "patisserie",   "Comment cuisiner du riz cantonais ?",                       False),
    # Niveau 🔵 — CROSS-DOMAINE : info existe, mauvais secteur choisi
    ("C1", "informatique", "Quelle est la posologie du paracétamol ?",                  False),
    ("C2", "jardinage",    "Comment réparer un vélo ?",                                 False),
]


def run():
    print(f"Running {len(QUESTIONS)} questions across sectored collections\n")
    n_ok_answer = 0
    n_ok_idk = 0

    for tag, sector, question, expected in QUESTIONS:
        store = VectorStore(persist_dir="chroma_db", collection_name=sector)
        print("=" * 78)
        print(f"[{tag}] sector={sector}   QUESTION : {question}")
        print(f"     attendu : {'✅ doit répondre' if expected else '❌ doit dire Je ne sais pas'}")
        print("=" * 78)

        result = answer_question(question, store)

        print("\n--- TOP 4 CHUNKS REMONTÉS ---")
        for i, c in enumerate(result["sources"], 1):
            name = c["source"].split("/")[-1]
            page = f" p.{c['page']}" if c["page"] is not None else ""
            preview = c["text"].replace("\n", " ")[:80]
            label = c.get("section_title") or "—"
            print(f"  [{i}] dist={c['distance']:.3f}  {name}{page}  «{label[:40]}»")
            print(f"       extrait: {preview}…")

        print("\n--- RÉPONSE LLM ---")
        print(result["answer"])

        # Coarse self-check
        is_idk = "ne sais pas" in result["answer"].lower()
        if expected and not is_idk:
            n_ok_answer += 1
            print("\n✅ Question répondue (attendu)")
        elif not expected and is_idk:
            n_ok_idk += 1
            print("\n✅ 'Je ne sais pas' correct (attendu)")
        elif expected and is_idk:
            print("\n⚠️  RAG a dit 'Je ne sais pas' alors qu'on attendait une réponse")
        else:
            print("\n⚠️  RAG a répondu alors qu'on attendait 'Je ne sais pas'")

        print()

    n_total = len(QUESTIONS)
    n_ok_total = n_ok_answer + n_ok_idk
    print("=" * 78)
    print(
        f"RÉCAP : {n_ok_total}/{n_total} comportements attendus — "
        f"réponses correctes : {n_ok_answer}, 'Je ne sais pas' corrects : {n_ok_idk}"
    )


if __name__ == "__main__":
    run()
