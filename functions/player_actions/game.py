from google.cloud.firestore import Client as FirestoreClient
from response_format import generate_error, generate_success
from firebase_admin import firestore
import datetime_functions as dtf
import cloud_task as ct

def start(data: dict, db: FirestoreClient):

    player_id = data.get("playerId")

    time_end = dtf.get_future_time(10)

    participants = data.get("participants")


    scores = {}
    for participant in participants:
        scores[participant] = 0
    db.collection("games").document(player_id).set(
        {
            "isLobbyOpen": False,
            "state": {
                "currentGame": "0",
                "phase": "loading",
                "scores":scores,
                "gameState": {
                    "phase": None,
                    "phaseEnd": None,
                },
                "phaseEnd": (
                   time_end
                ).isoformat(),
            },
        },
        merge=True,
    )

    ct.create_cloud_task( player_id, {
        "gameId": player_id
    }, time_end, None)


    return generate_success()
