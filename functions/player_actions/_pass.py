from google.cloud.firestore import Client as FirestoreClient
from firebase_admin import firestore
from response_format import generate_error, generate_success


def handle_action(data: dict, db: FirestoreClient):
    game_id = data.get("gameId")
    db.collection("games").document(game_id).update(
        {f"state.gameState.playerPassed": True}
    )

    #TODO add cloud task remove

    return generate_success()
