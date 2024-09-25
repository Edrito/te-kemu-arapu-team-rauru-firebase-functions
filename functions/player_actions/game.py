from google.cloud.firestore import Client as FirestoreClient
import datetime
from response_format import generate_error, generate_success
from firebase_admin import firestore


def start(data: dict, db: FirestoreClient):

    player_id = data.get("playerId")

    db.collection("games").document(player_id).set(
        {
            "isLobbyOpen": False,
            "state": {
                "phase": "loading",
                "nextPhase":"chosingCategory",
                "phaseEnd": (
                    datetime.datetime.now() + datetime.timedelta(seconds=5)
                ).isoformat(),
            },
        
        },
        merge=True,
    )

    return generate_success()
