# main.py
import json
from copy import deepcopy
from flask import Flask, request, jsonify

app = Flask(__name__)

# -------------------------------------------------------------------
# 1. Shared "claims context" skeletons for different damage types
# -------------------------------------------------------------------

EMPTY_ADMIN = {
    "schadenursache": None,  # will be set based on type
    "schadendatum": {
        "datum": None,
        "fiktiv": None,
    },
}

EMPTY_TAPWATER_DAMAGES = {
    "schadenbeschreibung_schadenursache": None,
    "schadenbeschreibung_folgeschaeden": None,
    "schadenursache_ermittelt": None,
    "liste_betroffener_etagen": None,
    "liste_betroffener_raeume": None,
    "liste_betroffener_flaechen": None,
    "liste_betroffener_bodenbelaege": None,
    "groesse_betroffener_flaechen": None,
    "schimmel_vorhanden": None,
    "leckortung_benoetigt": None,
    "trocknung_benoetigt": None,
    "rueckbau_benoetigt": None,
    "sanierung_benoetigt": None,
    "hausrat_betroffen": None,
}

EMPTY_GLASS_DAMAGES = {
    "schadenbeschreibung_schadenursache": None,
    "schadenbeschreibung_folgeschaeden": None,
    "gebaeudeverglasung_betroffen": None,
    "mobiliarverglasung_betroffen": None,
}

EMPTY_STORM_DAMAGES = {
    "schadenbeschreibung_schadenursache": None,
    "schadenbeschreibung_folgeschaeden": None,
    "dachschaden": {
        "dach_beschaedigt": None,
        "dachkategorien": None,
        "dachform_hauptgebaeude": None,
        "dachmaterial": None,
        "anzahl_beschaedigter_dachziegel": None,
        "dachschaden_flaeche_qm": None,
    },
    "naesseschaden": {
        "wassereintritt_ins_gebaeude": None,
        "stelle_wassereintritt": None,
        "sturmbedingte_oeffnung": None,
        "liste_betroffener_etagen": None,
        "liste_betroffener_raeume": None,
        "liste_nasser_flaechen": None,
        "nasse_flaeche_qm": None,
    },
    "baumschaden": {
        "liegt_baumschaden_vor": None,
        "baum_droht_umzukippen": None,
        "gefaehrdeter_baum_auf_eigenem_grundstueck": None,
        "gefaehrdeter_baum_bedroht_versichertes_gebaeude": None,
    },
}

EMPTY_ELEMENTAR_DAMAGES = {
    "schadenbeschreibung_schadenursache": None,
    "schadenbeschreibung_folgeschaeden": None,
    "ist_ueberschwemmung_oder_rueckstau": None,
    "natural_hazards_ueberschwemmung": {},
    "natural_hazards_rueckstau": {},
    "schaden_innen_oder_aussen": None,
    "liste_betroffener_etagen": None,
    "liste_betroffener_raeume": None,
    "liste_betroffener_flaechen": None,
    "liste_betroffener_bodenbelaege": None,
    "nasse_flaeche_qm": None,
    "wasserhoehe_cm_innen": None,
    "unbewohnbar": None,
    "feuerwehr_vor_ort": None,
}

EMPTY_ROBBERY_THEFT_DAMAGES = {
    "diebstahl_hergang_beschreibung": None,
    "gestohlene_gegenstaende_schadenbeschreibung": None,
    "gestohlene_gegenstaende_wert": None,
    "polizeiliche_akte_vorhanden": None,
    "polizeiliches_aktenzeichen": None,
    "polizeidienststelle_ort": None,
    "polizei_meldung_zeitpunkt": None,
    "zugang_und_sicherung_beschreibung": None,
    "einbruchspuren_vorhanden": None,
    "fotos_von_einbruchspuren_vorhanden": None,
    "stehlgutliste_vorhanden": None,
    "belege_rechnungen_vorhanden": None,
    "taeter_ermittelt": None,
    "taeter_angaben": None,
    "schadenminderungsmassnahmen": None,
    "fahrrad_abgeschlossen": None,
}


def empty_claims_context(damage_type: str):
    admin = deepcopy(EMPTY_ADMIN)
    if damage_type == "tapwater":
        admin["schadenursache"] = "LEITUNGSASSER"
        return {
            "admin": admin,
            "tapwater_damages": deepcopy(EMPTY_TAPWATER_DAMAGES),
        }
    if damage_type == "glass":
        admin["schadenursache"] = "GLAS"
        return {
            "admin": admin,
            "glass_damages": deepcopy(EMPTY_GLASS_DAMAGES),
        }
    if damage_type == "storm":
        admin["schadenursache"] = "STURM"
        return {
            "admin": admin,
            "storm_damages": deepcopy(EMPTY_STORM_DAMAGES),
        }
    if damage_type == "elementar":
        admin["schadenursache"] = "ELEMENTARE_NATURGEFAHREN"
        return {
            "admin": admin,
            "natural_hazards": deepcopy(EMPTY_ELEMENTAR_DAMAGES),
        }
    if damage_type == "robbery":
        admin["schadenursache"] = "DIEBSTAHL_RAUB"
        return {
            "admin": admin,
            "robbery_theft": deepcopy(EMPTY_ROBBERY_THEFT_DAMAGES),
        }
    # fallback: generic
    admin["schadenursache"] = "SONSTIGES"
    return {
        "admin": admin,
        "generic_damages": {
            "schadenbeschreibung_schadenursache": None,
            "schadenbeschreibung_folgeschaeden": None,
        },
    }


# -------------------------------------------------------------------
# 2. Question catalogs per damage type (minimal examples)
# -------------------------------------------------------------------

TAPWATER_QUESTIONS = [
    {
        "question_id": "/admin/schadendatum/datum",
        "field_path": ["admin", "schadendatum", "datum"],
        "text": "An welchem Datum ist der Leitungswasserschaden aufgetreten?",
        "mandatory": True,
        "weight": 100,
    },
    {
        "question_id": "/tapwater_damages/schadenbeschreibung_schadenursache",
        "field_path": ["tapwater_damages", "schadenbeschreibung_schadenursache"],
        "text": "Bitte schildern Sie kurz die Schadenursache (z.B. Rohrbruch, undichte Armatur).",
        "mandatory": True,
        "weight": 90,
    },
    {
        "question_id": "/tapwater_damages/schadenbeschreibung_folgeschaeden",
        "field_path": ["tapwater_damages", "schadenbeschreibung_folgeschaeden"],
        "text": "Bitte schildern Sie kurz die Folgeschäden (z.B. betroffene Räume, Böden, Möbel).",
        "mandatory": True,
        "weight": 85,
    },
]

GLASS_QUESTIONS = [
    {
        "question_id": "/admin/schadendatum/datum",
        "field_path": ["admin", "schadendatum", "datum"],
        "text": "An welchem Datum ist der Glasschaden aufgetreten?",
        "mandatory": True,
        "weight": 100,
    },
    {
        "question_id": "/glass_damages/schadenbeschreibung_schadenursache",
        "field_path": ["glass_damages", "schadenbeschreibung_schadenursache"],
        "text": "Bitte schildern Sie kurz, wie der Glasschaden entstanden ist.",
        "mandatory": True,
        "weight": 90,
    },
    {
        "question_id": "/glass_damages/schadenbeschreibung_folgeschaeden",
        "field_path": ["glass_damages", "schadenbeschreibung_folgeschaeden"],
        "text": "Welche Folgeschäden sind entstanden (z.B. Scherben, beschädigte Möbel)?",
        "mandatory": False,
        "weight": 70,
    },
]

STORM_QUESTIONS = [
    {
        "question_id": "/admin/schadendatum/datum",
        "field_path": ["admin", "schadendatum", "datum"],
        "text": "An welchem Datum hat der Sturm den Schaden verursacht?",
        "mandatory": True,
        "weight": 100,
    },
    {
        "question_id": "/storm_damages/schadenbeschreibung_schadenursache",
        "field_path": ["storm_damages", "schadenbeschreibung_schadenursache"],
        "text": "Bitte schildern Sie kurz, wie der Sturmschaden entstanden ist (z.B. Dachziegel abgedeckt, Baum umgestürzt).",
        "mandatory": True,
        "weight": 90,
    },
    {
        "question_id": "/storm_damages/schadenbeschreibung_folgeschaeden",
        "field_path": ["storm_damages", "schadenbeschreibung_folgeschaeden"],
        "text": "Welche Folgeschäden sind entstanden (z.B. Wassereintritt, beschädigte Räume, Hausrat)?",
        "mandatory": False,
        "weight": 80,
    },
]

ELEMENTAR_QUESTIONS = [
    {
        "question_id": "/admin/schadendatum/datum",
        "field_path": ["admin", "schadendatum", "datum"],
        "text": "An welchem Datum ist der Elementarschaden (z.B. Überschwemmung, Rückstau) eingetreten?",
        "mandatory": True,
        "weight": 100,
    },
    {
        "question_id": "/natural_hazards/schadenbeschreibung_schadenursache",
        "field_path": ["natural_hazards", "schadenbeschreibung_schursache"],
        "text": "Bitte schildern Sie kurz die Schadenursache (z.B. Hochwasser, Rückstau aus Abfluss).",
        "mandatory": True,
        "weight": 90,
    },
    {
        "question_id": "/natural_hazards/schadenbeschreibung_folgeschaeden",
        "field_path": ["natural_hazards", "schadenbeschreibung_folgeschaeden"],
        "text": "Bitte schildern Sie kurz die Folgeschäden (z.B. vollgelaufener Keller, überflutetes Grundstück).",
        "mandatory": False,
        "weight": 80,
    },
]

ROBBERY_QUESTIONS = [
    {
        "question_id": "/admin/schadendatum/datum",
        "field_path": ["admin", "schadendatum", "datum"],
        "text": "An welchem Datum fand der Diebstahl / Raub statt?",
        "mandatory": True,
        "weight": 100,
    },
    {
        "question_id": "/robbery_theft/diebstahl_hergang_beschreibung",
        "field_path": ["robbery_theft", "diebstahl_hergang_beschreibung"],
        "text": "Bitte schildern Sie kurz den Hergang des Diebstahls / Raubs.",
        "mandatory": True,
        "weight": 90,
    },
    {
        "question_id": "/robbery_theft/gestohlene_gegenstaende_schadenbeschreibung",
        "field_path": ["robbery_theft", "gestohlene_gegenstaende_schadenbeschreibung"],
        "text": "Welche Gegenstände wurden gestohlen oder beschädigt?",
        "mandatory": True,
        "weight": 85,
    },
]


def get_question_catalog(damage_type: str):
    if damage_type == "tapwater":
        return TAPWATER_QUESTIONS
    if damage_type == "glass":
        return GLASS_QUESTIONS
    if damage_type == "storm":
        return STORM_QUESTIONS
    if damage_type == "elementar":
        return ELEMENTAR_QUESTIONS
    if damage_type == "robbery":
        return ROBBERY_QUESTIONS
    return TAPWATER_QUESTIONS


# -------------------------------------------------------------------
# 3. Generic helpers to update state and pick next question
# -------------------------------------------------------------------

def get_nested_value(obj, path):
    ref = obj
    for p in path:
        if ref is None:
            return None
        ref = ref.get(p)
    return ref


def set_nested_value(obj, path, value):
    ref = obj
    for p in path[:-1]:
        if p not in ref or ref[p] is None:
            ref[p] = {}
        ref = ref[p]
    ref[path[-1]] = value


def update_claims_from_answer(claims_context, last_question_id, user_text, damage_type):
    if not last_question_id:
        # no specific question context -> simple heuristic
        # you could plug in LLM extraction here later
        return claims_context

    for q in get_question_catalog(damage_type):
        if q["question_id"] == last_question_id:
            set_nested_value(claims_context, q["field_path"], user_text)
            break
    return claims_context


def compute_next_question(claims_context, damage_type):
    catalog = get_question_catalog(damage_type)
    candidates = []
    for q in catalog:
        value = get_nested_value(claims_context, q["field_path"])
        if value in (None, ""):
            candidates.append(q)
    if not candidates:
        return None
    candidates.sort(key=lambda x: (not x["mandatory"], -x["weight"]))
    return candidates[0]


def build_summary(claims_context, damage_type):
    admin = claims_context["admin"]
    parts = []
    if admin["schadendatum"]["datum"]:
        parts.append(f"Schadendatum: {admin['schadendatum']['datum']}")

    if damage_type == "tapwater":
        tap = claims_context["tapwater_damages"]
        if tap["schadenbeschreibung_schadenursache"]:
            parts.append("Leitungswasserschaden: " + tap["schadenbeschreibung_schadenursache"])
        if tap["schadenbeschreibung_folgeschaeden"]:
            parts.append("Folgeschäden: " + tap["schadenbeschreibung_folgeschaeden"])
    elif damage_type == "glass":
        glass = claims_context["glass_damages"]
        if glass["schadenbeschreibung_schadenursache"]:
            parts.append("Glasschaden: " + glass["schadenbeschreibung_schadenursache"])
        if glass["schadenbeschreibung_folgeschaeden"]:
            parts.append("Folgeschäden: " + glass["schadenbeschreibung_folgeschaeden"])
    elif damage_type == "storm":
        storm = claims_context["storm_damages"]
        if storm["schadenbeschreibung_schadenursache"]:
            parts.append("Sturmschaden: " + storm["schadenbeschreibung_schadenursache"])
        if storm["schadenbeschreibung_folgeschaeden"]:
            parts.append("Folgeschäden: " + storm["schadenbeschreibung_folgeschaeden"])
    elif damage_type == "elementar":
        nh = claims_context["natural_hazards"]
        if nh["schadenbeschreibung_schadenursache"]:
            parts.append("Elementarschaden: " + nh["schadenbeschreibung_schadenursache"])
        if nh["schadenbeschreibung_folgeschaeden"]:
            parts.append("Folgeschäden: " + nh["schadenbeschreibung_folgeschaeden"])
    elif damage_type == "robbery":
        rb = claims_context["robbery_theft"]
        if rb["diebstahl_hergang_beschreibung"]:
            parts.append("Vorfall: " + rb["diebstahl_hergang_beschreibung"])
        if rb["gestohlene_gegenstaende_schadenbeschreibung"]:
            parts.append("Gestohlene Gegenstände: " + rb["gestohlene_gegenstaende_schadenbeschreibung"])
    else:
        gen = claims_context.get("generic_damages", {})
        if gen.get("schadenbeschreibung_schadenursache"):
            parts.append("Schadenursache: " + gen["schadenbeschreibung_schadenursache"])
        if gen.get("schadenbeschreibung_folgeschaeden"):
            parts.append("Folgeschäden: " + gen["schadenbeschreibung_folgeschaeden"])

    if not parts:
        return "Bisher liegen noch keine strukturierten Angaben vor."
    return "Zusammenfassung der bisherigen Angaben:\n- " + "\n- ".join(parts)


# -------------------------------------------------------------------
# 4. Generic intake handlers per damage type
# -------------------------------------------------------------------

def handle_start_intake(damage_type: str):
    body = request.get_json(silent=True) or {}
    session_info = body.get("sessionInfo", {})
    parameters = session_info.get("parameters", {})

    claims_context = empty_claims_context(damage_type)
    next_q = compute_next_question(claims_context, damage_type)

    if next_q:
        reply_text = next_q["text"]
        next_question_id = next_q["question_id"]
        is_done = False
    else:
        reply_text = "Ich konnte keine Fragen für die Schadenaufnahme finden."
        next_question_id = None
        is_done = True

    claims_state = {
        "damage_type": damage_type,
        "claims_context": claims_context,
        "last_question_id": next_question_id,
    }

    response = {
        "fulfillment_response": {
            "messages": [
                {"text": {"text": [reply_text]}}
            ]
        },
        "sessionInfo": {
            "parameters": {
                "claims_state": json.dumps(claims_state),
                "is_done": is_done,
            }
        },
    }
    return jsonify(response)


def handle_process_answer(damage_type: str):
    body = request.get_json(silent=True) or {}
    session_info = body.get("sessionInfo", {})
    parameters = session_info.get("parameters", {})

    user_text = parameters.get("user_text", "")
    claims_state_raw = parameters.get("claims_state")
    if claims_state_raw:
        claims_state = json.loads(claims_state_raw)
    else:
        claims_state = {
            "damage_type": damage_type,
            "claims_context": empty_claims_context(damage_type),
            "last_question_id": None,
        }

    claims_context = claims_state.get("claims_context", empty_claims_context(damage_type))
    last_question_id = claims_state.get("last_question_id")

    claims_context = update_claims_from_answer(
        claims_context, last_question_id, user_text, damage_type
    )

    next_q = compute_next_question(claims_context, damage_type)
    is_done = False

    if next_q:
        reply_text = next_q["text"]
        next_question_id = next_q["question_id"]
    else:
        summary = build_summary(claims_context, damage_type)
        reply_text = (
            summary
            + "\n\nVielen Dank, ich habe die wichtigsten Informationen zur Schadenmeldung aufgenommen."
        )
        next_question_id = None
        is_done = True

    claims_state["claims_context"] = claims_context
    claims_state["last_question_id"] = next_question_id

    response = {
        "fulfillment_response": {
            "messages": [
                {"text": {"text": [reply_text]}}
            ]
        },
        "sessionInfo": {
            "parameters": {
                "claims_state": json.dumps(claims_state),
                "is_done": is_done,
            }
        },
    }
    return jsonify(response)


# -------------------------------------------------------------------
# 5. Flask routes per damage type
# -------------------------------------------------------------------

@app.route("/tapwater/start_intake", methods=["POST"])
def tapwater_start():
    return handle_start_intake("tapwater")


@app.route("/tapwater/process_answer", methods=["POST"])
def tapwater_process():
    return handle_process_answer("tapwater")


@app.route("/glass/start_intake", methods=["POST"])
def glass_start():
    return handle_start_intake("glass")


@app.route("/glass/process_answer", methods=["POST"])
def glass_process():
    return handle_process_answer("glass")


@app.route("/storm/start_intake", methods=["POST"])
def storm_start():
    return handle_start_intake("storm")


@app.route("/storm/process_answer", methods=["POST"])
def storm_process():
    return handle_process_answer("storm")


@app.route("/elementar/start_intake", methods=["POST"])
def elementar_start():
    return handle_start_intake("elementar")


@app.route("/elementar/process_answer", methods=["POST"])
def elementar_process():
    return handle_process_answer("elementar")


@app.route("/robbery/start_intake", methods=["POST"])
def robbery_start():
    return handle_start_intake("robbery")


@app.route("/robbery/process_answer", methods=["POST"])
def robbery_process():
    return handle_process_answer("robbery")


# -------------------------------------------------------------------
# 6. Optional: simple intent classifier endpoint (rule-based)
# -------------------------------------------------------------------

@app.route("/classify_intent", methods=["POST"])
def classify_intent():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").lower()

    if any(k in text for k in ["rohr", "leitung", "wasserfleck", "leck", "leitungswasser"]):
        damage_type = "tapwater"
    elif any(k in text for k in ["fenster", "scheibe", "glas", "glastisch"]):
        damage_type = "glass"
    elif any(k in text for k in ["sturm", "hagel", "starkwind", "dach", "baum umgestürzt"]):
        damage_type = "storm"
    elif any(k in text for k in ["hochwasser", "überschwemmung", "rückstau", "abfluss"]):
        damage_type = "elementar"
    elif any(k in text for k in ["diebstahl", "raub", "einbruch", "fahrrad gestohlen"]):
        damage_type = "robbery"
    else:
        damage_type = "generic"

    return jsonify({"damage_type": damage_type})


@app.route("/")
def health_check():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
