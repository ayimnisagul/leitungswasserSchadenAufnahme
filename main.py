# main.py
import json
from copy import deepcopy
from flask import Flask, request, jsonify

app = Flask(__name__)


# --- Simplified ClaimsContext structures -----------------------

# In a real implementation, you could directly import your Pydantic models
# from tapwater_damages.py, admin.py, claims_context.py, etc.
# For now we create a minimal JSON-based representation.

EMPTY_ADMIN = {
    "schadenursache": "LEITUNGSWASSER",  # fix for this bot
    "schadendatum": {
        "datum": None,
        "fiktiv": None,
    },
    "anrufer_verhaeltnis_zum_vn": None,
    "anrufer_person": None,
    "schadenort": None,
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


def empty_claims_context():
    return {
        "admin": deepcopy(EMPTY_ADMIN),
        "tapwater_damages": deepcopy(EMPTY_TAPWATER_DAMAGES),
        # you could add extraction / interpretation domains here as needed
    }


# --- Question catalog and ordering (simplified) ----------------

# Map from question_id -> question metadata (for Leitungswasser)
QUESTION_CATALOG = [
    {
        "question_id": "/admin/schadendatum/datum",
        "field_path": ["admin", "schadendatum", "datum"],
        "text": "An welchem Datum ist der Schaden aufgetreten?",
        "mandatory": True,
        "section": "Admin",
        "weight": 100,
    },
    {
        "question_id": "/tapwater_damages/schadenbeschreibung_schadenursache",
        "field_path": ["tapwater_damages", "schadenbeschreibung_schadenursache"],
        "text": "Bitte schildern Sie kurz die Schadenursache.",
        "mandatory": True,
        "section": "Leitungswasserschaden",
        "weight": 90,
    },
    {
        "question_id": "/tapwater_damages/schadenbeschreibung_folgeschaeden",
        "field_path": ["tapwater_damages", "schadenbeschreibung_folgeschaeden"],
        "text": "Bitte schildern Sie kurz die Folgeschäden (z.B. betroffene Räume, Flächen, Möbel).",
        "mandatory": True,
        "section": "Leitungswasserschaden",
        "weight": 85,
    },
    {
        "question_id": "/tapwater_damages/schimmel_vorhanden",
        "field_path": ["tapwater_damages", "schimmel_vorhanden"],
        "text": "Ist Schimmel sichtbar?",
        "mandatory": False,
        "section": "Leitungswasserschaden",
        "weight": 70,
    },
    {
        "question_id": "/tapwater_damages/leckortung_benoetigt",
        "field_path": ["tapwater_damages", "leckortung_benoetigt"],
        "text": "Wird Ihrer Einschätzung nach eine Leckortung benötigt?",
        "mandatory": False,
        "section": "Leitungswasserschaden",
        "weight": 60,
    },
    {
        "question_id": "/tapwater_damages/trocknung_benoetigt",
        "field_path": ["tapwater_damages", "trocknung_benoetigt"],
        "text": "Wird eine Trocknung benötigt oder ist bereits eine Trocknung im Gange?",
        "mandatory": False,
        "section": "Leitungswasserschaden",
        "weight": 55,
    },
    {
        "question_id": "/tapwater_damages/hausrat_betroffen",
        "field_path": ["tapwater_damages", "hausrat_betroffen"],
        "text": "Ist Hausrat durch den Schaden betroffen (z.B. Möbel, Elektrogeräte)?",
        "mandatory": False,
        "section": "Leitungswasserschaden",
        "weight": 50,
    },
]


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


# --- Simple extraction logic -----------------------------------
# For now, this is extremely naive:
# - If the user just answered a specific question, we store the full text as the answer.
# - In a more advanced setup, you would:
#   - Use LLM calls to parse the transcript and fill multiple fields at once,
#   - Mirror your domain extraction logic from tapwater_damages.py etc.

def update_claims_from_answer(claims_context, last_question_id, user_text):
    if not last_question_id:
        # No last question context -> either initial turn or free talk.
        # In a more advanced version, you'd parse user_text with LLM here.
        return claims_context

    # find the corresponding question
    for q in QUESTION_CATALOG:
        if q["question_id"] == last_question_id:
            set_nested_value(claims_context, q["field_path"], user_text)
            break
    return claims_context


# --- Next best question selection (simplified) -----------------

def compute_next_question(claims_context):
    # replicate "next best" logic: highest weight unanswered, mandatory first
    candidates = []
    for q in QUESTION_CATALOG:
        value = get_nested_value(claims_context, q["field_path"])
        if value in (None, ""):
            candidates.append(q)

    if not candidates:
        return None

    # sort by mandatory desc, then weight desc
    candidates.sort(
        key=lambda x: (not x["mandatory"], -x["weight"])
    )
    return candidates[0]


# --- Helper: build summary text --------------------------------

def build_summary(claims_context):
    admin = claims_context["admin"]
    tap = claims_context["tapwater_damages"]

    parts = []

    if admin["schadendatum"]["datum"]:
        parts.append(f"Schadendatum: {admin['schadendatum']['datum']}")
    if tap["schadenbeschreibung_schadenursache"]:
        parts.append(
            "Schadenursache: "
            + tap["schadenbeschreibung_schadenursache"]
        )
    if tap["schadenbeschreibung_folgeschaeden"]:
        parts.append(
            "Folgeschäden: "
            + tap["schadenbeschreibung_folgeschaeden"]
        )
    if tap["schimmel_vorhanden"] not in (None, ""):
        parts.append(f"Schimmel vorhanden: {tap['schimmel_vorhanden']}")
    if tap["leckortung_benoetigt"] not in (None, ""):
        parts.append(f"Leckortung benötigt: {tap['leckortung_benoetigt']}")
    if tap["trocknung_benoetigt"] not in (None, ""):
        parts.append(f"Trocknung benötigt: {tap['trocknung_benoetigt']}")
    if tap["hausrat_betroffen"] not in (None, ""):
        parts.append(f"Hausrat betroffen: {tap['hausrat_betroffen']}")

    if not parts:
        return "Bisher liegen noch keine strukturierten Angaben vor."
    return "Zusammenfassung der bisherigen Angaben:\n- " + "\n- ".join(parts)


# --- Dialogflow CX webhook handlers -----------------------------

@app.route("/start_intake", methods=["POST"])
def start_intake():
    """Initialize a new Leitungswasserschaden intake."""
    # Parse Dialogflow CX webhook request
    body = request.get_json(silent=True) or {}
    session_info = body.get("sessionInfo", {})
    parameters = session_info.get("parameters", {})

    # Initialize claims context
    claims_context = empty_claims_context()
    # Optional: if vsnr or schadenursache already set as CX parameters, use them.
    if "schadenursache" in parameters:
        claims_context["admin"]["schadenursache"] = parameters["schadenursache"]

    # Choose first question
    next_q = compute_next_question(claims_context)
    if next_q:
        reply_text = next_q["text"]
        next_question_id = next_q["question_id"]
        is_done = False
    else:
        reply_text = "Ich konnte keine Fragen für die Schadenaufnahme finden."
        next_question_id = None
        is_done = True

    # Pack state into a single JSON string to store in CX session parameters
    claims_state = {
        "claims_context": claims_context,
        "last_question_id": next_question_id,
    }

    response = {
        "fulfillment_response": {
            "messages": [
                {
                    "text": {
                        "text": [reply_text]
                    }
                }
            ]
        },
        "sessionInfo": {
            "parameters": {
                "claims_state": json.dumps(claims_state),
                "is_done": is_done,
            }
        }
    }
    return jsonify(response)


@app.route("/process_answer", methods=["POST"])
def process_answer():
    """Process user's answer, update claim, and ask next question."""
    body = request.get_json(silent=True) or {}
    session_info = body.get("sessionInfo", {})
    parameters = session_info.get("parameters", {})

    # Extract user text (Dialogflow CX passes it in different places;
    # simplest is via 'text' in last input) – but we can also extract from 'intentInfo'.
    text_payloads = (
        body.get("text") or
        body.get("fulfillmentInfo", {}).get("tag")  # fallback
    )

    # In CX webhook v3, actual user text is in `body['text']` only for some channels;
    # more robust: use queryResult or detectIntent output, but we keep it simple:
    user_text = None
    if isinstance(text_payloads, str):
        user_text = text_payloads
    else:
        # As a fallback, try to read from `intentInfo.parameters` if needed
        pass

    # If not found, try from body.payload (depending on integration)
    if user_text is None:
        user_text = ""  # avoid crash

    # Load existing claims state
    claims_state_raw = parameters.get("claims_state")
    if claims_state_raw:
        claims_state = json.loads(claims_state_raw)
    else:
        claims_state = {
            "claims_context": empty_claims_context(),
            "last_question_id": None,
        }

    claims_context = claims_state.get("claims_context", empty_claims_context())
    last_question_id = claims_state.get("last_question_id")

    # Update context with this answer
    claims_context = update_claims_from_answer(
        claims_context, last_question_id, user_text
    )

    # Decide next question
    next_q = compute_next_question(claims_context)
    is_done = False

    if next_q:
        reply_text = next_q["text"]
        next_question_id = next_q["question_id"]
    else:
        # If no more questions, send summary and mark done
        summary = build_summary(claims_context)
        reply_text = (
            summary
            + "\n\nVielen Dank, ich habe alle notwendigen Informationen für den Leitungswasserschaden aufgenommen."
        )
        next_question_id = None
        is_done = True

    # Update state
    claims_state["claims_context"] = claims_context
    claims_state["last_question_id"] = next_question_id

    response = {
        "fulfillment_response": {
            "messages": [
                {
                    "text": {
                        "text": [reply_text]
                    }
                }
            ]
        },
        "sessionInfo": {
            "parameters": {
                "claims_state": json.dumps(claims_state),
                "is_done": is_done,
            }
        }
    }
    return jsonify(response)


@app.route("/")
def health_check():
    return "OK", 200


if __name__ == "__main__":
    # For local testing only. On Cloud Run we use gunicorn.
    app.run(host="0.0.0.0", port=8080, debug=True)
