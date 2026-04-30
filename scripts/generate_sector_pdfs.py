"""Generate 8 additional sector-specific PDFs into data/<sector>/.

Usage:
    python scripts/generate_sector_pdfs.py
"""
from fpdf import FPDF
from pathlib import Path


DATA_DIR = Path(__file__).parent.parent / "data"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def make_pdf(sector: str, filename: str, title: str, pages: list[tuple[str, str]]) -> None:
    """Create a PDF inside data/<sector>/ with one section per page."""
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
        pdf.multi_cell(0, 6, body)

    out_dir = DATA_DIR / sector
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / filename
    pdf.output(str(out_path))
    print(f"  ✓ {out_path}")


# ============================================================================
# 1. comptabilite/comptabilite_immobilisations.pdf
# ============================================================================
immobilisations = [
    (
        "Section 1 - Définition des immobilisations",
        "Une immobilisation est un bien destiné à être utilisé durablement par "
        "l'entreprise, sur plus d'un exercice comptable. Elle figure à l'actif "
        "du bilan et fait l'objet d'un amortissement si sa valeur diminue avec "
        "le temps. Le seuil de 500 euros HT est généralement retenu en deçà "
        "duquel un bien peut être passé directement en charge plutôt qu'immobilisé. "
        "Trois grandes catégories existent : immobilisations incorporelles, "
        "corporelles et financières."
    ),
    (
        "Section 2 - Immobilisations incorporelles",
        "Les immobilisations incorporelles regroupent les biens sans consistance "
        "physique. Le compte 201 enregistre les frais d'établissement, amortis "
        "sur 5 ans. Le 203 traite les frais de recherche et développement. Le "
        "205 vise les concessions, brevets et licences avec une durée propre à "
        "chaque actif. Le 206 enregistre le droit au bail, non amortissable. Le "
        "207 retrace le fonds commercial. Le 208 couvre les autres immobilisations "
        "incorporelles dont les logiciels acquis."
    ),
    (
        "Section 3 - Immobilisations corporelles",
        "Les immobilisations corporelles sont les biens physiques destinés à un "
        "usage durable. Le compte 211 traite les terrains, non amortissables. Le "
        "212 enregistre les agencements de terrains. Le 213 vise les constructions "
        "amorties sur 20 à 50 ans. Le 215 retrace les installations techniques, "
        "matériel et outillage industriels. Le 218 enregistre les autres immobilisations "
        "corporelles dont véhicules sur 5 ans, mobilier sur 10 ans, matériel de "
        "bureau et informatique sur 3 à 5 ans."
    ),
    (
        "Section 4 - Immobilisations financières",
        "Les immobilisations financières concernent les placements à long terme. "
        "Le compte 261 enregistre les titres de participation représentant au "
        "moins 10 pour cent du capital d'une autre société. Le 271 retrace les "
        "autres titres immobilisés. Le 274 traite les prêts accordés. Le 275 "
        "vise les dépôts et cautionnements versés. Le 276 enregistre les autres "
        "créances immobilisées. Ces actifs ne s'amortissent pas mais font l'objet "
        "de provisions en cas de dépréciation."
    ),
    (
        "Section 5 - Valorisation et entrée au bilan",
        "Une immobilisation entre au bilan à son coût d'acquisition incluant "
        "le prix d'achat hors taxes récupérables, les frais directement "
        "rattachables comme transport et installation, et les droits de douane "
        "le cas échéant. Pour une production interne, on retient le coût de "
        "production complet. Les frais financiers d'emprunt peuvent être "
        "incorporés sur option pour les actifs nécessitant une longue période "
        "de préparation. Les escomptes commerciaux viennent en déduction du "
        "coût d'entrée."
    ),
]

# ============================================================================
# 2. juridique/juridique_droit_travail.pdf
# ============================================================================
droit_travail = [
    (
        "Section 1 - Contrat à durée indéterminée",
        "Le CDI est la forme normale et générale du contrat de travail selon "
        "le Code du travail. Il peut être conclu par écrit ou oral, mais l'écrit "
        "est recommandé pour la sécurité juridique. La période d'essai est de "
        "2 mois pour les ouvriers et employés, 3 mois pour les agents de maîtrise "
        "et techniciens, 4 mois pour les cadres. Elle est renouvelable une fois "
        "si la convention collective le permet. La rupture nécessite préavis sauf "
        "faute grave ou lourde."
    ),
    (
        "Section 2 - Contrat à durée déterminée",
        "Le CDD obéit à des règles strictes. Sa durée maximale est de 18 mois "
        "renouvellement compris dans la majorité des cas. Il ne peut être "
        "renouvelé que 2 fois maximum. Il doit être motivé par écrit pour un "
        "des cas autorisés : remplacement d'un salarié absent, accroissement "
        "temporaire d'activité, emploi saisonnier, contrat d'usage. À son "
        "terme, le salarié perçoit une indemnité de précarité de 10 pour cent "
        "du salaire brut total perçu. La transformation en CDI est la sanction "
        "automatique d'un CDD irrégulier."
    ),
    (
        "Section 3 - Congés payés et durée du travail",
        "Tout salarié acquiert 2,5 jours ouvrables de congés payés par mois "
        "travaillé soit 30 jours ouvrables ou 5 semaines par an pour un temps "
        "plein. La durée légale du travail est de 35 heures par semaine ou "
        "1607 heures par an. Au-delà, les heures supplémentaires sont majorées "
        "à 25 pour cent pour les 8 premières puis 50 pour cent au-delà. Le "
        "contingent annuel d'heures supplémentaires est fixé par accord, à "
        "défaut 220 heures par salarié et par an."
    ),
    (
        "Section 4 - Licenciement et indemnités",
        "Le licenciement nécessite une cause réelle et sérieuse. Le motif "
        "personnel peut être disciplinaire ou non. Le motif économique se "
        "justifie par difficultés économiques, mutations technologiques, "
        "réorganisation ou cessation d'activité. La procédure obligatoire "
        "comprend convocation à entretien préalable, entretien, notification "
        "écrite. Le préavis légal est de 1 mois pour moins de 2 ans d'ancienneté, "
        "2 mois au-delà. L'indemnité légale de licenciement est due dès 8 mois "
        "d'ancienneté, à raison de 1/4 de mois de salaire par année."
    ),
    (
        "Section 5 - Rupture conventionnelle",
        "La rupture conventionnelle est un accord amiable entre employeur et "
        "salarié pour rompre un CDI. Elle nécessite un ou plusieurs entretiens, "
        "puis la signature d'une convention. Le délai de rétractation est de 15 "
        "jours calendaires après signature. La convention doit être homologuée "
        "par la DREETS dans les 15 jours suivants. L'indemnité versée ne peut "
        "être inférieure à l'indemnité légale de licenciement. Le salarié "
        "bénéficie de l'allocation chômage dans les conditions de droit commun."
    ),
]

# ============================================================================
# 3. medical/medical_vaccins.pdf
# ============================================================================
vaccins = [
    (
        "Section 1 - Calendrier vaccinal du nourrisson",
        "Le calendrier vaccinal français rend obligatoires 11 vaccins pour les "
        "enfants nés depuis le 1er janvier 2018. À 2 mois : DTP, coqueluche, "
        "Hib, hépatite B, pneumocoque. À 4 mois : rappel hexavalent et pneumocoque. "
        "À 5 mois : méningocoque C. À 11 mois : rappel hexavalent et pneumocoque. "
        "À 12 mois : rougeole, oreillons, rubéole et méningocoque C. À 16-18 "
        "mois : rappel ROR. Le respect strict du calendrier conditionne l'admission "
        "en collectivité."
    ),
    (
        "Section 2 - Vaccins de l'adulte",
        "Les rappels DTP doivent être effectués à 25 ans, 45 ans, puis tous les "
        "10 ans à partir de 65 ans. Le vaccin contre la grippe saisonnière est "
        "recommandé annuellement à partir de 65 ans, ou plus tôt en cas de maladie "
        "chronique. Le zona est conseillé à partir de 65 ans en deux doses. La "
        "coqueluche est rappelée chez les femmes enceintes et l'entourage des "
        "nourrissons. Le pneumocoque est indiqué pour les personnes à risque dès "
        "l'enfance."
    ),
    (
        "Section 3 - Contre-indications absolues",
        "Toute vaccination est contre-indiquée en cas de réaction allergique "
        "grave anaphylactique à une dose précédente du même vaccin ou à l'un de "
        "ses composants. Les vaccins vivants atténués comme ROR, varicelle, "
        "fièvre jaune sont contre-indiqués pendant la grossesse, en cas "
        "d'immunodépression sévère et chez les nourrissons de moins de 9 mois "
        "pour la fièvre jaune. Une fièvre supérieure à 38,5 degrés justifie de "
        "reporter une vaccination. Un rhume banal ne contre-indique pas."
    ),
    (
        "Section 4 - Effets indésirables courants",
        "Les effets indésirables vaccinaux les plus fréquents sont locaux : "
        "douleur au point d'injection, rougeur, induration. Ces réactions "
        "disparaissent en 24 à 72 heures. Une fièvre modérée peut survenir 6 "
        "à 12 heures après l'injection. Pour le ROR, fièvre et éruption "
        "cutanée peuvent apparaître 5 à 12 jours après la vaccination. Les "
        "réactions graves restent exceptionnelles, le rapport bénéfice-risque "
        "des vaccins est très largement favorable selon les autorités sanitaires."
    ),
    (
        "Section 5 - Voyages et vaccinations spécifiques",
        "Les vaccinations recommandées pour voyage dépendent de la destination. "
        "La fièvre jaune est obligatoire pour entrer dans certains pays "
        "d'Afrique et d'Amérique du Sud, à faire 10 jours avant le départ et "
        "valable à vie. La typhoïde est recommandée pour les zones d'hygiène "
        "précaire. La rage est indiquée pour les séjours prolongés ou en zone "
        "rurale. L'hépatite A est conseillée pour la plupart des destinations "
        "tropicales. Une consultation en centre de vaccination internationale "
        "est recommandée 4 à 6 semaines avant le départ."
    ),
]

# ============================================================================
# 4. restauration/restauration_couts.pdf
# ============================================================================
food_cost = [
    (
        "Section 1 - Définition du food cost",
        "Le food cost ou ratio matière représente le pourcentage du chiffre "
        "d'affaires consacré à l'achat des matières premières alimentaires. Il "
        "se calcule en divisant le coût des matières consommées par le chiffre "
        "d'affaires hors taxes, multiplié par 100. Un restaurant traditionnel "
        "vise un food cost entre 25 et 35 pour cent. Un restaurant gastronomique "
        "monte à 35-40 pour cent. Un fast-food reste autour de 25-30 pour cent. "
        "Un food cost trop élevé indique des prix trop bas ou des pertes."
    ),
    (
        "Section 2 - Coefficient multiplicateur",
        "Le coefficient multiplicateur permet de fixer un prix de vente à partir "
        "du coût matière d'un plat. La formule simple : prix de vente HT = coût "
        "matière HT multiplié par coefficient. Pour un food cost cible de 30 "
        "pour cent, le coefficient est de 3,33. Pour 25 pour cent, il monte à "
        "4. Pour 35 pour cent, il descend à 2,86. Le prix TTC se calcule en "
        "appliquant la TVA correspondante : 10 pour cent en restauration sur "
        "place pour la nourriture, 20 pour cent pour les boissons alcoolisées."
    ),
    (
        "Section 3 - Fiche technique d'un plat",
        "Une fiche technique recense pour chaque plat les ingrédients, leurs "
        "quantités, leurs coûts, et le calcul du prix de revient. Elle inclut "
        "le numéro de référence du plat, son nom, le nombre de couverts, la "
        "liste des ingrédients avec dénomination précise, unité de mesure, "
        "quantité utilisée, prix d'achat unitaire, prix d'achat total, et le "
        "prix de revient final. Elle sert à standardiser les recettes, calculer "
        "les coûts précis et adapter les portions selon la production."
    ),
    (
        "Section 4 - Sources de pertes",
        "Les pertes alimentaires en restauration ont plusieurs origines. Les "
        "pertes de production correspondent aux épluchures et parures non "
        "valorisées. Les pertes de cuisson concernent l'évaporation et la "
        "réduction des viandes représentant 20 à 30 pour cent du poids cru. "
        "Les pertes de portionnement viennent d'écarts entre la fiche technique "
        "et la réalisation. Les pertes par vol ou casse sont à distinguer. Les "
        "pertes par péremption résultent d'une mauvaise gestion des stocks. "
        "Le total peut atteindre 8 à 12 pour cent du chiffre d'affaires sans "
        "vigilance."
    ),
    (
        "Section 5 - Inventaire et rotation",
        "L'inventaire mensuel valorise les stocks réels en fin de période. "
        "Le coût matière effectif se calcule : stock initial plus achats moins "
        "stock final. La méthode FIFO premier entré premier sorti garantit "
        "une rotation correcte. Le coefficient de rotation = consommations "
        "annuelles divisées par stock moyen. Un coefficient de 12 signifie "
        "rotation mensuelle. Un coefficient inférieur à 6 indique surstockage. "
        "Les produits frais doivent atteindre 24 à 52 selon la périssabilité. "
        "Un inventaire physique trimestriel détecte les écarts entre théorique "
        "et réel."
    ),
]

# ============================================================================
# 5. informatique/informatique_git.pdf
# ============================================================================
git_pdf = [
    (
        "Section 1 - Concepts de base",
        "Git est un système de gestion de versions décentralisé créé en 2005 "
        "par Linus Torvalds. Chaque dépôt local contient l'historique complet, "
        "permettant de travailler hors ligne. Trois zones structurent un projet "
        "Git : le working directory contenant les fichiers actuels, l'index "
        "ou staging area regroupant les modifications à committer, et le local "
        "repository conservant l'historique des commits. Un commit est une "
        "photographie instantanée de l'état du projet identifiée par un hash "
        "SHA-1 unique."
    ),
    (
        "Section 2 - Commandes essentielles",
        "Les commandes de base couvrent 90 pour cent des usages quotidiens. "
        "git init initialise un nouveau dépôt. git clone duplique un dépôt "
        "distant. git status affiche l'état des fichiers. git add stage des "
        "modifications. git commit -m enregistre un commit avec message. "
        "git log affiche l'historique. git diff montre les modifications non "
        "stagées. git push envoie les commits vers un remote. git pull récupère "
        "les modifications distantes. git checkout bascule entre branches ou "
        "restaure des fichiers."
    ),
    (
        "Section 3 - Branches et workflow",
        "Les branches permettent de développer plusieurs fonctionnalités en "
        "parallèle. git branch liste les branches existantes. git branch nom "
        "crée une nouvelle branche. git checkout -b nom crée et bascule en une "
        "commande. git merge intègre une branche dans la courante. git rebase "
        "réécrit l'historique pour appliquer les commits sur une nouvelle base. "
        "Le workflow GitFlow utilise main pour la production, develop pour "
        "l'intégration, feature/* pour les nouvelles fonctionnalités, hotfix/* "
        "pour les corrections urgentes."
    ),
    (
        "Section 4 - Conflits et résolution",
        "Un conflit survient quand deux branches modifient les mêmes lignes. "
        "Git marque les zones conflictuelles avec des balises spéciales : "
        "moins moins moins moins moins moins moins HEAD pour la version locale, "
        "égal égal égal égal égal égal égal pour le séparateur, plus plus plus "
        "plus plus plus plus pour la version distante. La résolution consiste "
        "à éditer manuellement le fichier en gardant le code souhaité, supprimer "
        "les balises, puis git add et git commit. La commande git mergetool "
        "lance un outil graphique de fusion pour faciliter cette opération."
    ),
    (
        "Section 5 - Bonnes pratiques",
        "Cinq règles structurent une utilisation efficace de Git. Premièrement "
        "des commits atomiques traitant un seul sujet. Deuxièmement des messages "
        "de commit clairs au présent de l'impératif comme 'Add user authentication'. "
        "Troisièmement ne jamais committer de secrets, fichiers binaires lourds, "
        "fichiers générés. Quatrièmement utiliser systématiquement gitignore pour "
        "exclure ces éléments. Cinquièmement pull avant push pour minimiser les "
        "conflits. Une revue de code via pull request est essentielle en équipe "
        "pour maintenir la qualité et partager les connaissances."
    ),
]

# ============================================================================
# 6. velo/velo_accessoires.pdf
# ============================================================================
accessoires_velo = [
    (
        "Section 1 - Le casque cycliste",
        "Le casque réduit de 70 pour cent le risque de traumatisme crânien grave "
        "selon les études françaises. Il est obligatoire pour tout enfant "
        "transporté ou conducteur de moins de 12 ans, recommandé fortement pour "
        "tous les autres. Un casque conforme à la norme EN 1078 marque CE est "
        "exigé. Sa durée de vie est de 5 ans maximum à compter de la fabrication, "
        "ou immédiate après un choc même apparent indolore. La taille doit "
        "permettre d'introduire deux doigts sous la mentonnière, le casque ne "
        "doit pas bouger en secouant la tête."
    ),
    (
        "Section 2 - Antivols et niveaux de sécurité",
        "Le niveau de sécurité d'un antivol se mesure par sa résistance à "
        "l'effraction. Le label Sold Secure ou ART classe les antivols de 1 "
        "à 5 étoiles, 5 étant le maximum. Pour un vélo de moins de 500 euros, "
        "un antivol U de 2 étoiles suffit. Pour 500 à 1500 euros, viser 3 "
        "étoiles. Au-dessus de 1500 euros, prendre 4 ou 5 étoiles et combiner "
        "deux antivols différents. La règle d'or : attacher cadre et roue arrière "
        "à un point fixe inamovible, idéalement deux antivols sur cadre+roue "
        "avant et cadre+roue arrière."
    ),
    (
        "Section 3 - Eclairages obligatoires",
        "Le Code de la route impose un éclairage avant blanc ou jaune et un "
        "éclairage arrière rouge dès la nuit ou la visibilité réduite. Les "
        "feux clignotants ne sont pas autorisés. La puissance doit être visible "
        "à 150 mètres. Des catadioptres sont également obligatoires : un blanc "
        "à l'avant, un rouge à l'arrière, deux orange sur les rayons des roues, "
        "deux orange sur les pédales. Un gilet rétroréfléchissant est obligatoire "
        "hors agglomération de nuit ou par mauvaise visibilité, lui aussi à "
        "norme EN 1150."
    ),
    (
        "Section 4 - Porte-bagages et capacité",
        "Un porte-bagages se choisit selon la charge à transporter et le type "
        "de vélo. La capacité standard varie de 10 à 25 kilogrammes. Les "
        "versions renforcées 4 points de fixation atteignent 35 à 50 kg. La "
        "norme ISO 11243 encadre les charges maximales. La fixation doit être "
        "compatible avec le cadre, certains vélos sans œillets nécessitent des "
        "adaptateurs sur tige de selle. Pour transporter un enfant, un "
        "siège-enfant fixé au porte-bagage est limité à 22 kg en général. Les "
        "remorques offrent une capacité bien supérieure pour les courses ou "
        "deux enfants."
    ),
    (
        "Section 5 - Sacoches et bagagerie",
        "Trois familles de sacoches existent. Les sacoches de guidon de 5 à "
        "10 litres pour les essentiels accessibles. Les sacoches de cadre "
        "sportives de 1 à 4 litres pour téléphone, snacks, outils. Les sacoches "
        "de porte-bagages de 15 à 30 litres par paire pour les voyages et "
        "courses, idéalement étanches IPX5 minimum pour la pluie. Le système "
        "de fixation Klickfix ou QuickLock permet la pose et dépose en quelques "
        "secondes. Le poids du contenu doit rester équilibré entre les deux "
        "sacoches latérales pour ne pas dévoyer le vélo."
    ),
]

# ============================================================================
# 7. patisserie/patisserie_chocolat.pdf
# ============================================================================
chocolat = [
    (
        "Section 1 - Tempérage du chocolat",
        "Le tempérage est l'étape qui donne au chocolat son cassant, son brillant "
        "et son aspect lisse. Il consiste à fondre le chocolat puis à le refroidir "
        "et le réchauffer selon des courbes précises. Pour le chocolat noir : "
        "fondre à 50-55 degrés, refroidir à 28-29 degrés, réchauffer à 31-32 "
        "degrés. Pour le chocolat au lait : 45-50 puis 27-28 puis 29-30. Pour "
        "le chocolat blanc : 40-45 puis 26-27 puis 28-29. Un chocolat mal tempéré "
        "blanchit en surface après cristallisation, perd son brillant et son "
        "cassant."
    ),
    (
        "Section 2 - Méthode du tablage",
        "Le tablage est la méthode professionnelle de tempérage par étalement "
        "sur marbre. Verser deux tiers du chocolat fondu sur le marbre froid à "
        "16-18 degrés. L'étaler avec une spatule en va-et-vient pour le "
        "refroidir et favoriser la cristallisation. Quand le chocolat épaissit "
        "à la bonne température, le rassembler et le réincorporer au tiers chaud "
        "restant. Cette méthode demande de la pratique mais donne le meilleur "
        "résultat. Une alternative à la maison utilise un thermomètre précis "
        "et un bain-marie."
    ),
    (
        "Section 3 - Ganache classique",
        "La ganache de base utilise des proportions adaptées à l'usage. Pour "
        "fourrer un gâteau ou des bonbons : ratio 1:1 chocolat noir et crème "
        "liquide entière. Pour glacer : 1:1,5. Pour des truffes ferme : 2:1. "
        "Faire chauffer la crème à frémissement, verser sur le chocolat haché "
        "et attendre 30 secondes. Mélanger lentement au centre puis élargir "
        "pour obtenir une émulsion lisse et brillante. Ajouter du beurre froid "
        "à 10 pour cent du poids total apporte du soyeux et de la conservation."
    ),
    (
        "Section 4 - Types et pourcentages",
        "Le chocolat noir contient minimum 35 pour cent de cacao mais les "
        "qualités professionnelles affichent 60 à 75 pour cent. Le chocolat "
        "au lait contient minimum 25 pour cent de cacao et au moins 14 pour "
        "cent de matière sèche de lait. Le chocolat blanc ne contient que du "
        "beurre de cacao, sucre et lait sans pâte de cacao, minimum 20 pour "
        "cent de beurre de cacao. La couverture désigne un chocolat à teneur "
        "élevée en beurre de cacao supérieure à 31 pour cent, idéal pour le "
        "tempérage et l'enrobage."
    ),
    (
        "Section 5 - Conservation et défauts",
        "Le chocolat se conserve à 16-18 degrés en environnement sec à moins "
        "de 60 pour cent d'humidité, à l'abri de la lumière et des odeurs "
        "fortes. Le réfrigérateur est déconseillé, il provoque condensation "
        "et blanchiment sucré. Le blanchiment gras correspond à des cristaux "
        "de beurre de cacao migrant en surface, signe de variations thermiques. "
        "Le blanchiment sucré apparaît comme des taches blanches dues à la "
        "recristallisation du sucre après contact avec l'humidité. Les deux "
        "défauts sont irréversibles mais le chocolat reste comestible et "
        "utilisable en pâtisserie."
    ),
]

# ============================================================================
# 8. jardinage/jardinage_arrosage.pdf
# ============================================================================
arrosage = [
    (
        "Section 1 - Besoins en eau des plantes",
        "Les besoins varient considérablement selon les espèces, le climat et "
        "la saison. En moyenne, un potager nécessite 3 à 5 millimètres d'eau "
        "par jour en été, soit 30 à 50 litres par mètre carré par semaine. "
        "Les tomates demandent un arrosage régulier de 2 à 3 litres par plant "
        "et par jour en pleine production. Les courgettes consomment 4 à 5 "
        "litres par pied par semaine. Les salades exigent une humidité constante "
        "à raison de 2 litres par mètre carré par jour. Les arbres adultes "
        "puisent l'eau en profondeur et nécessitent peu d'arrosage."
    ),
    (
        "Section 2 - Quand arroser",
        "Le moment de l'arrosage influence directement l'efficacité. Le matin "
        "tôt entre 6 et 9 heures est idéal en saison chaude car l'eau pénètre "
        "avant l'évaporation et le feuillage sèche dans la journée évitant "
        "les maladies. Le soir entre 18 et 20 heures est une alternative en "
        "automne et au printemps. Eviter absolument l'arrosage en plein midi "
        "qui provoque évaporation rapide et brûlures par effet loupe sur "
        "feuilles mouillées. Un sol sec en surface mais humide à 5 cm de "
        "profondeur ne nécessite pas d'arrosage."
    ),
    (
        "Section 3 - Techniques d'arrosage",
        "L'arrosage à l'arrosoir au pied des plantes est le plus précis et "
        "économique pour les petites surfaces. L'arrosage au tuyau avec "
        "lance-pomme convient aux jardins moyens mais consomme davantage. "
        "Le goutte-à-goutte automatisé est la technique la plus économe en "
        "eau, jusqu'à 50 pour cent d'économies, et précise. L'aspersion "
        "convient aux pelouses mais favorise les maladies cryptogamiques sur "
        "les légumes. Le système oya consiste à enterrer une jarre poreuse "
        "remplie d'eau qui diffuse lentement par capillarité."
    ),
    (
        "Section 4 - Paillage et économie d'eau",
        "Le paillage du sol réduit de 40 à 70 pour cent les besoins en arrosage "
        "selon les conditions. Une couche de 5 à 10 centimètres protège le sol "
        "des rayons directs, limite l'évaporation et conserve l'humidité. Les "
        "matériaux organiques comme paille, foin, feuilles mortes, BRF "
        "enrichissent le sol en se décomposant. Les matériaux minéraux comme "
        "ardoise ou pouzzolane sont durables. Le paillage protège aussi du "
        "froid en hiver et limite la pousse des adventices, double bénéfice "
        "pour le jardinier."
    ),
    (
        "Section 5 - Récupération d'eau de pluie",
        "Un récupérateur de pluie collecte l'eau du toit pour un arrosage "
        "économique et écologique. Une toiture de 100 mètres carrés capte "
        "environ 80 mètres cubes par an en France métropolitaine. Une cuve "
        "de 300 à 500 litres convient à un petit jardin, 1000 à 2000 litres "
        "pour un potager. L'eau de pluie est idéale pour les plantes car non "
        "calcaire et sans chlore. La cuve doit être opaque ou enterrée pour "
        "limiter la prolifération d'algues. Un filtre à feuilles et un trop-plein "
        "vers les eaux pluviales sont indispensables. L'usage est strictement "
        "réservé à l'arrosage extérieur, jamais en eau potable."
    ),
]


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating sector PDFs in {DATA_DIR}/")

    make_pdf("comptabilite", "comptabilite_immobilisations.pdf",
             "Immobilisations comptables", immobilisations)
    make_pdf("juridique", "juridique_droit_travail.pdf",
             "Droit du travail - Bases", droit_travail)
    make_pdf("medical", "medical_vaccins.pdf",
             "Vaccinations en France", vaccins)
    make_pdf("restauration", "restauration_couts.pdf",
             "Gestion des coûts en restauration", food_cost)
    make_pdf("informatique", "informatique_git.pdf",
             "Git - Gestion de versions", git_pdf)
    make_pdf("velo", "velo_accessoires.pdf",
             "Accessoires et équipement vélo", accessoires_velo)
    make_pdf("patisserie", "patisserie_chocolat.pdf",
             "Travail du chocolat en pâtisserie", chocolat)
    make_pdf("jardinage", "jardinage_arrosage.pdf",
             "Arrosage et économie d'eau au jardin", arrosage)

    print("Done.")


if __name__ == "__main__":
    main()
