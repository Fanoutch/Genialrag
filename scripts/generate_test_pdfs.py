"""Generate 3 multi-page test PDFs into data/ for RAG smoke testing.

Usage:
    python scripts/generate_test_pdfs.py
"""
from fpdf import FPDF
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"


FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def make_pdf(filename: str, title: str, pages: list[tuple[str, str]]) -> None:
    """Create a PDF with one section per page.

    Each entry in `pages` is (section_title, body_text).
    """
    pdf = FPDF()
    pdf.add_font("DejaVu", "", FONT_REGULAR)
    pdf.add_font("DejaVu", "B", FONT_BOLD)
    pdf.set_auto_page_break(auto=True, margin=20)

    for section_title, body in pages:
        pdf.add_page()
        pdf.set_font("DejaVu", "B", 16)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(4)
        pdf.set_font("DejaVu", "B", 13)
        pdf.cell(0, 8, section_title, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font("DejaVu", "", 11)
        # multi_cell handles automatic line wrapping
        pdf.multi_cell(0, 6, body)

    out_path = DATA_DIR / filename
    pdf.output(str(out_path))
    print(f"  ✓ {out_path}")


# =============================================================================
# PDF 1 : Manuel vélo électrique
# =============================================================================
velo = [
    (
        "Section 1 - Spécifications techniques",
        "Le vélo électrique modèle E-Bike 2024 dispose d'une batterie lithium-ion "
        "de 504 Wh offrant une autonomie maximale de 80 kilomètres en mode Eco. "
        "Le moteur central délivre une puissance nominale de 250 watts et un "
        "couple de 65 Nm. La vitesse d'assistance est limitée à 25 km/h "
        "conformément à la réglementation européenne EN 15194. Le poids total "
        "du vélo est de 22 kilogrammes. Le cadre est en aluminium 6061. La "
        "garantie constructeur est de 2 ans pour le cadre et 1 an pour la "
        "batterie."
    ),
    (
        "Section 2 - Charge de la batterie",
        "La batterie doit être chargée exclusivement avec le chargeur d'origine "
        "fourni avec le vélo. Le temps de charge complet est de 4 heures à "
        "partir d'une batterie totalement déchargée. La température de charge "
        "doit être comprise entre 0 et 40 degrés Celsius. Ne jamais charger "
        "une batterie gelée. Stocker la batterie à environ 60 pour cent de "
        "charge en cas d'inutilisation prolongée. Effectuer un cycle complet "
        "de charge tous les 3 mois pour préserver la durée de vie."
    ),
    (
        "Section 3 - Entretien régulier",
        "Vérifier la pression des pneus avant chaque sortie. La pression "
        "recommandée est de 3,5 bars pour l'usage urbain et 4 bars pour les "
        "longues distances. Lubrifier la chaîne tous les 200 kilomètres avec "
        "une huile spécifique vélo. Nettoyer le vélo avec un chiffon humide, "
        "jamais au jet d'eau haute pression qui endommage les roulements. "
        "Faire réviser le système de freinage tous les 1500 kilomètres dans "
        "un atelier agréé. Remplacer les plaquettes de frein dès que leur "
        "épaisseur descend en dessous de 1,5 millimètre."
    ),
    (
        "Section 4 - Sécurité et conduite",
        "Le port du casque est fortement recommandé et obligatoire pour les "
        "enfants de moins de 12 ans transportés ou conducteurs. Les vélos à "
        "assistance électrique limités à 25 km/h ne nécessitent pas "
        "d'immatriculation ni de permis. Une assurance responsabilité civile "
        "est obligatoire. La nuit, l'éclairage avant blanc et arrière rouge "
        "doit être allumé en continu. Un dispositif sonore type sonnette est "
        "obligatoire. Ne jamais transporter un passager sauf si le vélo est "
        "spécifiquement conçu pour."
    ),
    (
        "Section 5 - Garantie et SAV",
        "La garantie constructeur de 2 ans couvre les défauts de fabrication "
        "du cadre et des composants mécaniques. La batterie est garantie 1 an "
        "ou 500 cycles de charge selon le premier terme atteint. La garantie "
        "ne couvre pas l'usure normale (pneus, plaquettes, chaîne, câbles). "
        "Pour toute demande SAV, contacter le service client au 01 23 45 67 89 "
        "muni du numéro de série situé sous la cadre. Le délai moyen de "
        "réparation en atelier agréé est de 7 jours ouvrés."
    ),
]

# =============================================================================
# PDF 2 : Recettes pâtisserie
# =============================================================================
patisserie = [
    (
        "Recette 1 - Tarte aux pommes",
        "Ingrédients pour 6 personnes : 1 pâte brisée de 250 grammes, 6 "
        "pommes type Golden, 50 grammes de sucre, 30 grammes de beurre, 1 "
        "sachet de sucre vanillé. Préchauffer le four à 200 degrés Celsius. "
        "Étaler la pâte dans un moule de 26 centimètres de diamètre. Éplucher "
        "et couper les pommes en lamelles fines. Disposer en rosace sur la "
        "pâte. Saupoudrer de sucre et de sucre vanillé. Parsemer de noisettes "
        "de beurre. Cuire 35 minutes à 200 degrés Celsius. Servir tiède."
    ),
    (
        "Recette 2 - Cookies au chocolat",
        "Ingrédients pour 20 cookies : 250 grammes de farine, 200 grammes de "
        "sucre roux, 125 grammes de beurre mou, 1 œuf, 1 sachet de levure "
        "chimique, 200 grammes de pépites de chocolat noir, 1 pincée de sel. "
        "Préchauffer le four à 180 degrés Celsius. Mélanger le beurre et le "
        "sucre jusqu'à blanchiment. Ajouter l'œuf, puis la farine et la "
        "levure. Incorporer les pépites de chocolat. Former des boules de 30 "
        "grammes et les espacer sur une plaque. Cuire 12 minutes à 180 "
        "degrés. Laisser refroidir 10 minutes avant de décoller."
    ),
    (
        "Recette 3 - Crème brûlée",
        "Ingrédients pour 4 ramequins : 50 centilitres de crème liquide "
        "entière, 6 jaunes d'œufs, 80 grammes de sucre, 1 gousse de vanille, "
        "4 cuillères à soupe de sucre roux pour la caramélisation. Préchauffer "
        "le four à 100 degrés Celsius. Faire chauffer la crème avec la gousse "
        "de vanille fendue. Battre les jaunes avec le sucre. Verser la crème "
        "chaude sur le mélange en fouettant. Répartir dans les ramequins. "
        "Cuire au bain-marie 1 heure à 100 degrés. Laisser refroidir 4 "
        "heures au réfrigérateur. Saupoudrer de sucre roux et caraméliser au "
        "chalumeau juste avant de servir."
    ),
    (
        "Recette 4 - Madeleines au miel",
        "Ingrédients pour 12 madeleines : 100 grammes de farine, 100 grammes "
        "de beurre fondu, 80 grammes de sucre, 2 œufs, 1 cuillère à soupe de "
        "miel liquide, 1/2 sachet de levure chimique, le zeste d'un demi "
        "citron. Mélanger les œufs et le sucre. Ajouter la farine, la levure, "
        "le zeste et le miel. Incorporer le beurre fondu. Réserver la pâte "
        "30 minutes au réfrigérateur. Préchauffer le four à 220 degrés "
        "Celsius. Garnir les moules à madeleines beurrés au 3/4. Cuire 4 "
        "minutes à 220 degrés puis baisser à 180 degrés et poursuivre 6 "
        "minutes pour obtenir la bosse caractéristique."
    ),
    (
        "Recette 5 - Mousse au chocolat",
        "Ingrédients pour 6 personnes : 200 grammes de chocolat noir à 70 "
        "pour cent de cacao, 6 œufs, 30 grammes de sucre, 1 pincée de sel. "
        "Faire fondre le chocolat au bain-marie à feu doux. Séparer les "
        "blancs des jaunes. Ajouter les jaunes au chocolat fondu hors du "
        "feu. Monter les blancs en neige avec le sel. Quand ils commencent "
        "à mousser, ajouter le sucre progressivement. Incorporer délicatement "
        "les blancs au mélange chocolaté avec une spatule. Répartir en "
        "verrines. Réfrigérer au minimum 4 heures avant de servir."
    ),
    (
        "Recette 6 - Pâte à crêpes classique",
        "Ingrédients pour 15 crêpes : 250 grammes de farine, 4 œufs, 50 "
        "centilitres de lait, 10 centilitres de bière (facultatif), 30 "
        "grammes de beurre fondu, 1 cuillère à soupe de sucre, 1 pincée de "
        "sel. Verser la farine dans un saladier. Faire un puits et y casser "
        "les œufs. Mélanger en incorporant peu à peu le lait. Ajouter le "
        "beurre fondu, le sucre, le sel et la bière. Laisser reposer 1 heure. "
        "Cuire dans une poêle chaude légèrement beurrée pendant environ 1 "
        "minute par face. Garder au chaud sur une assiette couverte d'un "
        "torchon."
    ),
]

# =============================================================================
# PDF 3 : Guide jardinage
# =============================================================================
jardinage = [
    (
        "Section 1 - Calendrier de semis au printemps",
        "Le mois de mars est idéal pour semer les radis, les carottes "
        "primeurs et les épinards directement en pleine terre. En avril, "
        "semer les haricots verts, les courgettes et les tomates sous abri. "
        "Mai marque la fin des Saints de Glace après le 15, on peut alors "
        "repiquer les plants de tomates en extérieur sans risque de gel. La "
        "température minimale du sol pour la germination des tomates est de "
        "12 degrés Celsius. Les radis lèvent en 5 à 7 jours."
    ),
    (
        "Section 2 - Calendrier de semis en été",
        "En juin, semer les choux d'hiver, les poireaux et les blettes. "
        "Juillet est le mois des semis de mâche, de chicorée et de navets "
        "d'automne. En août, planter les fraisiers pour une récolte l'année "
        "suivante. La fenêtre de semis idéale est tôt le matin ou en fin de "
        "journée pour éviter le stress thermique. L'arrosage doit être "
        "régulier mais sans excès, idéalement 2 à 3 fois par semaine en "
        "abondance plutôt que tous les jours en surface."
    ),
    (
        "Section 3 - Plantes d'automne",
        "Septembre et octobre sont propices à la plantation des bulbes de "
        "printemps : tulipes, narcisses, jonquilles, crocus. La profondeur "
        "de plantation correspond à 3 fois la hauteur du bulbe. Espacer les "
        "tulipes de 10 centimètres en tous sens. Les bulbes se plantent "
        "pointe vers le haut. Pailler après la première gelée pour protéger "
        "du froid intense. La floraison intervient entre mars et mai selon "
        "les variétés. Les bulbes peuvent rester en place 3 à 5 ans."
    ),
    (
        "Section 4 - Entretien hivernal",
        "Décembre à février est la période de repos végétatif. Tailler les "
        "rosiers en février-mars en supprimant le bois mort et en raccourcissant "
        "les branches principales à 3 ou 4 yeux. Protéger les plantes "
        "fragiles avec un voile d'hivernage si la température descend en "
        "dessous de moins 5 degrés Celsius. Bêcher les parcelles libres pour "
        "que le gel décompacte la terre. Apporter du compost mûr en "
        "couverture, à raison de 3 kilogrammes par mètre carré."
    ),
    (
        "Section 5 - Compostage domestique",
        "Un bon compost respecte un équilibre entre matières vertes (azote) "
        "et matières brunes (carbone) dans une proportion d'environ 1 pour "
        "2 en volume. Les matières vertes incluent les épluchures de "
        "légumes, les tontes de gazon, le marc de café. Les matières brunes "
        "regroupent les feuilles mortes, le carton non imprimé, la sciure "
        "de bois non traité. Brasser le tas tous les 15 jours pour aérer. "
        "Le compost est mûr en 6 à 12 mois selon les conditions."
    ),
]


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating PDFs in {DATA_DIR}/")

    make_pdf(
        "manuel_velo_electrique.pdf",
        "Manuel utilisateur - Vélo électrique E-Bike 2024",
        velo,
    )
    make_pdf(
        "recettes_patisserie.pdf",
        "Recettes de pâtisserie classique",
        patisserie,
    )
    make_pdf(
        "guide_jardinage.pdf",
        "Guide pratique du jardinage saisonnier",
        jardinage,
    )

    print("Done.")


if __name__ == "__main__":
    main()
