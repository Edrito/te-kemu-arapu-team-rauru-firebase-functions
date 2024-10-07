from google.cloud.firestore import Client as FirestoreClient
from firebase_admin import firestore
from response_format import generate_error, generate_success
from constants import HINTS


def handle_action(data: dict, db: FirestoreClient):
    game_id = data.get("gameId")
    player_id = data.get("playerId")
    action = data.get("action")
    action_details = action.get("details")
    category = action_details.get("category") if action_details.get("category") else ""
    letter = action_details.get("letter") if action_details.get("letter") else ""
    hint = HINTS.get(category, {}).get(letter, {})
    if not hint:
        return generate_error("No hint found for the given category and letter.")
    return generate_success(custom_payload=hint)
