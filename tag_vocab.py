# Controlled bilingual tag vocabulary for the FR/EN blog.
#
# A *concept* is one reusable tag with an English and a French label. The two are equal
# when the tag is language-neutral (proper nouns, acronyms, coinages). The vocabulary is
# the curated set of popular/reused tags that the picker offers and the migration
# normalizes toward; obscure one-off tags NOT listed here are left untouched.
#
# Lookups are case-insensitive (str.casefold) and whitespace-normalized, so every casing
# variant ("Personal Development" / "Personal development" / "développement personnel")
# collapses onto its concept for free — only typos, true synonyms, cross-language pairs,
# and merged-word accidents need an explicit alias. Because BOTH the EN and FR label key
# the same concept, a tag that leaked into the wrong language file ("Astrophysique" in an
# EN post, "Purpose" in an FR post) resolves to its concept and re-renders in the file's
# own language on the next save / during migration.
#
# `id` of a concept is its English label (globally unique). This is the seam the
# pair-aware set_tags ([[article-model]]), the picker ([[tag-suggestions]]), and the
# normalization migration all share.

HOUSE_TAG = "Gamsblurb"   # the site's house tag; always present on every post

# (en, fr, [extra raw aliases]) — en==fr for language-neutral tags. Ordered roughly by
# popularity so labels() returns the common tags first; the live index drives real
# ranking. Aliases cover ONLY what casefolding can't: typos, synonyms/variants, and
# merged-word accidents. Casing/accents-casing dups need no alias.
_CONCEPTS = [
    # ── House / series ──────────────────────────────────────────────────────────
    ("Gamsblurb", "Gamsblurb", ["Gamsblur", "GamsblogGamsblurb"]),
    ("Gamsblog", "Gamsblog", []),
    ("Gamsbook", "Gamsbook", []),
    ("Djosh Sho", "Djosh Sho", []),
    ("Guide For", "Guide Pour", []),
    ("Interverted (Novel)", "Interverti (Roman)", ["Interverted", "Interverti"]),

    # ── Top topics ──────────────────────────────────────────────────────────────
    ("Fiction", "Fiction", []),
    ("Health", "Santé", ["Heatlh"]),
    ("Mental Health", "Santé Mentale", []),
    ("Personal Development", "Développement Personnel", []),
    ("Motivation", "Motivation", []),
    ("Science", "Science", []),
    ("Learning", "Apprentissage", ["Learn", "Apprendre"]),
    ("Music", "Musique", []),
    ("Piano", "Piano", []),
    ("Productivity", "Productivité", []),
    ("Habits", "Habitudes", []),
    ("Gluten", "Gluten", []),
    ("Food", "Alimentation", ["Allimentation"]),
    ("Software Development", "Développement Logiciel",
     ["Software", "Logiciel", "développement de logiciels"]),
    ("Quote", "Citation", []),
    ("Purpose", "Raison d'Être", ["Raison de Vivre"]),
    ("Personalities", "Personnalités", []),
    ("Organization", "Organisation", []),
    ("One At A Time", "Un à la fois", []),
    ("Finance", "Finance", ["Finances"]),
    ("Money", "Argent", []),
    ("Education", "Éducation", []),
    ("Training vs Learning", "Entraînement vs Apprentissage", []),
    ("Technology", "Technologie", []),
    ("Programming", "Programmation", []),
    ("Code", "Code", ["Coding", "Codage"]),
    ("Priorities", "Priorités", ["Objectives", "Objectifs"]),
    ("Personal Care", "Soins Personnels", ["Soin Personnel"]),
    ("Meditation", "Méditation", []),
    ("Ikigai", "Ikigai", []),
    ("Did You Know", "Le Saviez-Vous", []),
    ("FunFact", "FunFact", ["Fun Fact"]),
    ("DevLog", "DevLog", []),
    ("Confidence", "Confiance", []),
    ("Self-confidence", "Confiance en soi", []),

    # ── Physics / space (often leaked into EN as the FR label) ────────────────────
    ("Astrophysics", "Astrophysique", []),
    ("Gravity", "Gravité", []),
    ("Black Hole", "Trou Noir", []),
    ("Dark Energy", "Énergie Sombre", []),
    ("Supernova", "Supernova", []),
    ("Big Bang", "Big Bang", []),
    ("Hawking Radiation", "Radiation de Hawking", []),
    ("Theory", "Théorie", []),
    ("Space", "Espace", []),
    ("Quantum", "Quantique", []),
    ("Civilization", "Civilisation", []),
    ("Globalization", "Mondialisation", ["Globalisation"]),

    # ── AI / tech ─────────────────────────────────────────────────────────────────
    ("Artificial Intelligence", "Intelligence Artificielle", ["AI", "IA"]),
    ("Computer Science", "Informatique", []),
    ("C++", "C++", ["C ++"]),

    # ── Writing / language ────────────────────────────────────────────────────────
    ("Writing", "Écriture", ["Write", "Écrire"]),
    ("New Word", "Nouveau Mot", []),
    ("New Expression", "Nouvelle Expression", []),
    ("Neologism", "Néologisme", []),
    ("French", "Français", []),
    ("English", "Anglais", []),
    ("Languages", "Langues", []),

    # ── Health / body ──────────────────────────────────────────────────────────────
    ("Fitness", "Fitness", ["Fit", "Forme"]),
    ("Exercise", "Exercice", []),
    ("Gym", "Gym", []),
    ("Walking", "Marche", ["Walk"]),
    ("Sleep", "Sommeil", []),
    ("Diet", "Régime Alimentaire", []),
    ("Nutrition", "Nutrition", []),
    ("Sugar", "Sucre", []),
    ("Stress", "Stress", []),
    ("Relaxation", "Relaxation", []),
    ("Breathing", "Respiration", []),
    ("Anxiety", "Anxiété", []),
    ("ADHD", "TDAH", []),
    ("Public Health", "Santé Publique", []),

    # ── Mind / growth ──────────────────────────────────────────────────────────────
    ("Success", "Succès", []),
    ("Growth", "Croissance", []),
    ("Ambition", "Ambition", []),
    ("Perseverance", "Persévérance", []),
    ("Resilience", "Résilience", []),
    ("Wisdom", "Sagesse", []),
    ("Curiosity", "Curiosité", []),
    ("Optimism", "Optimisme", []),
    ("Perspective", "Perspective", []),
    ("Reflection", "Réflexion", []),
    ("Philosophy", "Philosophie", []),

    # ── Society / world ──────────────────────────────────────────────────────────
    ("Politics", "Politique", []),
    ("Revolution", "Révolution", []),
    ("Religion", "Religion", []),
    ("History", "Histoire", []),
    ("Community", "Communauté", []),
    ("Capitalism", "Capitalisme", []),
    ("Business", "Entreprise", ["Entreprises"]),
    ("Climate", "Climat", []),

    # ── Family ─────────────────────────────────────────────────────────────────────
    ("Parent", "Parent", []),
    ("Parenting", "Parentalité", []),
    ("Child", "Enfant", ["Children", "Enfants"]),

    # ── Misc reused ──────────────────────────────────────────────────────────────
    ("Future", "Futur", []),
    ("Game", "Jeu", []),
    ("Video Game", "Jeu Vidéo", ["VideoGame", "JeuVideo", "Video Game"]),
    ("Magic", "Magie", []),
    ("Humor", "Humour", []),
    ("Life Hacks", "Life Hacks", []),
    ("Myers-Briggs", "Myers-Briggs", []),
    ("Microphone", "Microphone", []),
    ("Decluttering", "Désencombrement", []),
    ("Create", "Créer", []),
    ("Anecdotes", "Anecdotes", ["Anecdote"]),
    ("Book", "Livre", []),
    ("Prediction", "Prédiction", []),
    ("Focus", "Focus", []),
    ("Concentration", "Concentration", []),
    ("Memory", "Mémoire", []),
    ("School", "École", []),
    ("Restaurant", "Restaurant", []),
    ("Excel", "Excel", []),
    ("Science Fiction", "Science-Fiction", []),
]


def _norm(label):
    """Casefold + collapse internal whitespace — the key under which a raw label is
    matched. Returns "" for a blank label."""
    return " ".join(str(label).split()).casefold()


# concept dicts (id == en) and the raw-label -> concept index ----------------------------
CONCEPTS = [{"id": en, "en": en, "fr": fr} for (en, fr, _aliases) in _CONCEPTS]

_BY_KEY = {}
for (_en, _fr, _aliases) in _CONCEPTS:
    _concept = {"id": _en, "en": _en, "fr": _fr}
    for _raw in (_en, _fr, *_aliases):
        _key = _norm(_raw)
        if _key and _key not in _BY_KEY:        # first concept to claim a key wins
            _BY_KEY[_key] = _concept


# ========================================================================================
# Tag-string helpers (the model stores tags as one comma-separated string)
# ========================================================================================
def split(tag_string):
    """Comma-separated tag string -> list of stripped, non-empty labels."""
    return [t.strip() for t in str(tag_string or "").split(",") if t.strip()]


def join(labels):
    """List of labels -> the stored comma-separated tag string (no spaces, matching the
    Astro frontmatter `tags: [a,b,c]` style)."""
    return ",".join(labels)


# ========================================================================================
# Concept lookups
# ========================================================================================
def normalize(label):
    """The concept a raw label belongs to, or None when the label is not in the
    controlled vocabulary (an obscure one-off tag, left untouched)."""
    return _BY_KEY.get(_norm(label))


def concept_id(label):
    """The concept id (its EN label) for a raw label, or None if unknown."""
    c = normalize(label)
    return c["id"] if c else None


def label(concept_id_or_label, hl):
    """The vocabulary label for a concept in language `hl` ("fr"/"en"). Accepts a
    concept id OR any raw label of the concept. Falls back to the input (trimmed) when
    the concept is unknown, so it is always safe to call."""
    c = normalize(concept_id_or_label)
    if c is None:
        return " ".join(str(concept_id_or_label).split())
    return c["fr"] if hl == "fr" else c["en"]


def canonical_label(raw_label, hl):
    """Normalize one raw label to its vocabulary label in `hl`; unknown labels pass
    through trimmed. Used by the migration and the index to fold variants together."""
    return label(raw_label, hl)


def concepts_in(tag_string):
    """Ordered, de-duplicated list of concept ids present in a tag string (skips
    non-vocabulary tags). Drives the pair-aware twin sync."""
    out = []
    seen = set()
    for t in split(tag_string):
        cid = concept_id(t)
        if cid and cid not in seen:
            out.append(cid)
            seen.add(cid)
    return out


def labels(hl):
    """All vocabulary labels in language `hl`, in vocabulary (≈popularity) order. The
    picker uses this as the candidate universe / fallback ordering."""
    return [c["fr"] if hl == "fr" else c["en"] for c in CONCEPTS]
