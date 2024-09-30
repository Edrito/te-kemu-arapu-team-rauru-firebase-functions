from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from google.cloud.firestore import Client as FirestoreClient 
from datetime_functions import get_current_time, parse_time
from state_management import category_game, randomized_game
from player_actions import game
from firebase_functions import https_fn
from response_format import generate_error, generate_success

def manage_state(doc_dict:dict,doc_id:str, db: FirestoreClient) -> https_fn.Response:
    state = doc_dict.get("state")
    current_phase = state.get("phase")
    current_game = state.get("currentGame")

    settings = doc_dict.get('settings')

    if not settings:
        return generate_error("No settings provided", 400)
    
    games = settings.get('games')
    if not games:
        return generate_error("No games provided", 400)
    
   
    
    match current_phase:
        case "loading":
            doc_dict["state"]["phase"] = "playing"
            doc_dict['state']['phaseEnd'] = None
            db.collection("games").document(doc_id).set(doc_dict, merge=True)
        case 'end':
            #find the next [current_game] in the list of games keys
            doc_dict['state']['phaseEnd'] = None

            games_keys = games.keys()
            next_game = None
            next_key = False
            for key in games_keys:
                if next_key:
                    next_game = key
                    break
                if key == current_game:
                    next_key = True
            if not next_game:
                doc_dict["state"]["phase"] = "lobbyEnd"
                db.collection("games").document(doc_id).set(doc_dict, merge=True)
                return generate_success()
            else :
                current_game = next_game
                doc_dict["state"]["currentGame"] = current_game
                doc_dict["state"]["phase"] = "loading"
                db.collection("games").document(doc_id).set(doc_dict, merge=True)

    #TODO
    current_game_info = games.get(current_game)

    if not current_game_info:
        return generate_error("Current game does not exist", 404)
    
    game_type = current_game_info.get('type')

    match game_type:
        case "category":
            return category_game.manage_game(doc_dict, doc_id, db)
        case "randomized":
            return randomized_game.manage_game(doc_dict, doc_id, db)

