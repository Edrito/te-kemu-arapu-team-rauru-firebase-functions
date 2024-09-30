from google.cloud.firestore import Client as FirestoreClient
from firebase_admin import firestore
from response_format import generate_error, generate_success


def handle_action(data: dict, db: FirestoreClient):
    game_id = data.get("gameId")
    player_id = data.get("playerId")
    action = data.get("action")
    action_details = action.get("details")
    vote_type = action_details.get("voteType")

    match vote_type:
        case "positive":
            db.collection("games").document(game_id).update(
                {"positiveVotes": firestore.ArrayUnion([player_id])}
            )

            db.collection("games").document(game_id).update(
                {"negativeVotes": firestore.ArrayRemove([player_id])}
            )

            db.collection("games").document(game_id).update(
                {"neutralVotes": firestore.ArrayRemove([player_id])}
            )

        case "negative":
            db.collection("games").document(game_id).update(
                {"positiveVotes": firestore.ArrayRemove([player_id])}
            )

            db.collection("games").document(game_id).update(
                {"negativeVotes": firestore.ArrayUnion([player_id])}
            )

            db.collection("games").document(game_id).update(
                {"neutralVotes": firestore.ArrayRemove([player_id])}
            )

        case "neutral":
            db.collection("games").document(game_id).update(
                {"positiveVotes": firestore.ArrayRemove([player_id])}
            )

            db.collection("games").document(game_id).update(
                {"negativeVotes": firestore.ArrayRemove([player_id])}
            )

            db.collection("games").document(game_id).update(
                {"neutralVotes": firestore.ArrayUnion([player_id])}
            )

    return generate_success()
