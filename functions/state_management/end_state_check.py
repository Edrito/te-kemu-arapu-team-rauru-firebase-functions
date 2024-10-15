from firebase_functions import https_fn, options
from firebase_admin import firestore
import firebase_admin
import json
from format_checker import check_format
import player_actions.profile as profile
import player_actions.vote as vote
import player_actions.lobby as lobby
import player_actions.game as game
import player_actions.categoryVote as categoryVote
import player_actions._pass as _pass
import player_actions.letterSelect as letterSelect
import player_actions.hint as hint
from response_format import generate_error, generate_success
from datetime_functions import get_future_time, get_current_time, parse_time
from google.cloud.firestore import Client as FirestoreClient 
from cloud_task import manage_cloud_task

def end_game(doc_dict:dict,doc_id:str, db: FirestoreClient)  -> https_fn.Response:
    doc_dict["state"]["phase"] = "lobbyEnd"
    doc_dict["state"]["phaseEnd"] = None
    db.collection("games").document(doc_id).set(doc_dict, merge=True)
    db.collection("gamesArchive").document(doc_id).set(doc_dict)
    manage_cloud_task(doc_id,"",None,db,deleteOnly=True, previous_task_id=doc_dict.get("taskId"))
    
    return generate_success("Game Ended", 200)

def end_state_check(doc_dict, document_id, db) -> https_fn.Response:
    settings = doc_dict.get("settings")
    state = doc_dict.get("state")
    if settings is None:
        return None
    lobby_end_conditions = settings.get("endConditions")
    if lobby_end_conditions is None:
        return None
    player_score = lobby_end_conditions.get("playerScore")
    total_score = lobby_end_conditions.get("score")
    time_minutes = lobby_end_conditions.get("time")
    
    player_scores = state.get("scores") # {playerId: score}
    if player_scores is None:
        return None
    
    if player_score is not None:
        for player_id, score in player_scores.items():
            if score >= player_score:
                end_game(doc_dict, document_id, db)
                return generate_success("Max player score reached", 200)
            
    if total_score is not None:
        total = 0
        for player_id, score in player_scores.items():
            total += score
        if total >= total_score:
            end_game(doc_dict, document_id, db)
            return generate_success("Max total score reached", 200)
        
    if time_minutes is not None:
        phase_end = parse_time(doc_dict.get('timeStarted'))
        if phase_end is not None:
            if abs((get_current_time() - phase_end).min) > time_minutes :
                end_game(doc_dict, document_id, db)
                return generate_success("Time limit reached", 200)
            
    return None