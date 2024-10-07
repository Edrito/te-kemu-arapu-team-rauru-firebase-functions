from google.cloud.firestore import Client as FirestoreClient 
import datetime
from response_format import generate_error, generate_success
from firebase_admin import firestore
import random
import string
from constants import MAORI_ALPHABET, CATEGORIES,MAORI_ALPHABET_LIST


def add_categories_and_alphabet(data: dict):
    data['categories'] = CATEGORIES
    data['alphabet'] = MAORI_ALPHABET_LIST


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
    details['lobbyCode'] =  ''.join(random.choices(MAORI_ALPHABET + string.digits, k=4))
    
    details['isLobbyOpen'] = True
    details['participants'] = [
        player_id,
    ]
    details['state'] = {}

    add_categories_and_alphabet(details)

    db.collection("games").document(player_id)\
        .set(details, merge=False)

    return generate_success(
        custom_payload={
            "gameId": player_id,
            "lobbyCode": details['lobbyCode']
        }
    )


def delete(data: dict, db: FirestoreClient):
    
    player_id = data.get("playerId")

    db.collection("games").document(player_id)\
        .delete()
    
    return generate_success()

def join(data: dict, db: FirestoreClient):
    player_id = data.get("playerId")
    game_id = data.get("gameId")

    if game_id is not None:
        game = db.collection("games").document(game_id).get()

        if not game.exists:
            return generate_error("Game does not exist!", 400)
        

        db.collection("games").document(game_id)\
            .update({
                "participants": firestore.ArrayUnion([player_id])
        })

    else:
        lobby_code = data.get("lobbyCode")
        details = data.get("details")
        if lobby_code is None:
            lobby_code = details.get("lobbyCode")

        if lobby_code is None:
            return generate_error("No lobbyCode provided", 400)
        
        game = db.collection("games").where("lobbyCode", "==", lobby_code).get()
        if len(game) == 0:
            return generate_error("Game does not exist!", 400)
        
        game_id = game[0].id

        db.collection("games").document(game_id).update({
                "participants": firestore.ArrayUnion([player_id])
            })
    
    return generate_success()
    

def leave(data: dict, db: FirestoreClient):
    
    player_id = data.get("playerId")

    game_id = data.get("gameId")

    if game_id is None:
        return generate_error("No game id provided", 400)
    
    db.collection("games").document(game_id)\
        .update({
            "participants": firestore.ArrayRemove([player_id])
        })
 
    
    return generate_success()