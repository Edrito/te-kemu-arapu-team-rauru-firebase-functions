from google.cloud.firestore import Client as FirestoreClient
from firebase_admin import firestore
from response_format import generate_error, generate_success


def handle_action(data: dict, db: FirestoreClient):
    game_id = data.get("gameId")
    player_id = data.get("playerId")
    action = data.get("action")
    action_details = action.get("details")
    vote_type = action_details.get("voteType")
    db.collection("games").document(game_id).update(
                {f"state.gameState.votes.{player_id}": vote_type},
    )
    

    return generate_success()
