from google.cloud.firestore import Client as FirestoreClient 
import datetime
from response_format import generate_error, generate_success
from firebase_admin import firestore
import random
import string

def upsert(data: dict, db: FirestoreClient):
    
    action = data.get('action')
    details = action.get('details')
    if details is None:
        return generate_error("No details provided", 400)
    player_id = data.get("playerId")

    settings = details.get("settings")
    if settings is None:
        return generate_error("No settings provided", 400)
    
    games = settings.get("games")
    if games is None:
        return generate_error("No games provided", 400)

    details["lastUpdated"] = datetime.datetime.now().isoformat()
    
    details['gameId'] = player_id
    #Generate random 4 digit code with letters and numbers
    details['lobbyCode'] =  ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    details['isLobbyOpen'] = True
    details['participants'] = [
        player_id,
    ]
    details['state'] = {}

    db.collection("games").document(player_id)\
        .set(details, merge=True)

    return generate_success()


def delete(data: dict, db: FirestoreClient):
    
    action = data.get('action')
    details = action.get('details')
    if details is None:
        return generate_error("No details provided", 400)
    
    player_id = data.get("playerId")

    db.collection("games").document(player_id)\
        .delete()
    
    return generate_success()

def join(data: dict, db: FirestoreClient):
    
    action = data.get('action')
    details = action.get('details')
    if details is None:
        return generate_error("No details provided", 400)
    
    player_id = data.get("playerId")

    game_id = details.get("gameId")
    if game_id is None:
        return generate_error("No game id provided", 400)
    
    game = db.collection("games").document(game_id).get()
    if not game.exists:
        return generate_error("Game does not exist", 400)
    
    game_data = game.to_dict()

    participants = game_data.get("participants")
    if not participants:
        participants = []

    db.collection("games").document(game_id)\
        .update({
            "participants": firestore.ArrayUnion([player_id])
        })
    
    return generate_success()

def leave(data: dict, db: FirestoreClient):
    
    action = data.get('action')
    details = action.get('details')
    if details is None:
        return generate_error("No details provided", 400)
    
    player_id = data.get("playerId")

    game_id = details.get("gameId")
    if game_id is None:
        return generate_error("No game id provided", 400)
    
    game = db.collection("games").document(game_id).get()
    if not game.exists:
        return generate_error("Game does not exist", 400)
    
    game_data = game.to_dict()

    participants = game_data.get("participants")
    if not participants:
        participants = []

    db.collection("games").document(game_id)\
        .update({
            "participants": firestore.ArrayRemove([player_id])
        })
    
    return generate_success()