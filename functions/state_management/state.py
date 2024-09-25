from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from google.cloud.firestore import Client as FirestoreClient 
from datetime_functions import get_current_time, parse_time
from state_management import category_game, randomized_game
from firebase_functions import https_fn
from response_format import generate_error, generate_success

def manage_state(doc_dict:dict,doc_id:str, db: FirestoreClient) -> https_fn.Response:
    current_state = doc_dict.get("state")
    current_phase = current_state.get("phase")
    current_game = current_state.get("currentGame")

    match current_phase:
        case "loading":
            doc_dict["state"]["phase"] = "playing"
            doc_dict['state']['phaseEnd'] = None
        
    #TODO
    #add end condition checking

    db.collection("games").document(doc_id).set(doc_dict, merge=True)
    settings = doc_dict.get('settings')

    if not settings:
        return generate_error("No settings provided", 400)
    
    games = settings.get('games')

    if not games:
        return generate_error("No games provided", 400)
    
    current_game = games.get(current_game)
    if not current_game:
        return generate_error("Current game does not exist", 404)

    game_type = current_game.get('type')

    match game_type:
        case "category":
            return category_game.manage_game(doc_dict, doc_id, db)
        case "randomized":
            return randomized_game.manage_game(doc_dict, doc_id, db)

