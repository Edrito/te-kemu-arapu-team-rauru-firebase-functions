from google.cloud.firestore import Client as FirestoreClient
from firebase_admin import firestore
from response_format import generate_error, generate_success
from datetime_functions import parse_time, get_current_time, get_future_time
from cloud_task import manage_cloud_task


def handle_action(data: dict, db: FirestoreClient):
    game_id = data.get("gameId")
    player_id = data.get("playerId")
    action = data.get("action")
    action_details = action.get("details")
    letter = action_details.get("letter")
  
    game = db.collection("games").document(game_id).get()
    game_dict = game.to_dict()
    state = game_dict.get("state") if game_dict.get("state") else {}
    gameState = state.get("gameState") if state.get("gameState") else {}

    player_turn = gameState.get("playerTurn")

    if player_turn != player_id:
        return generate_error("Not your turn!")

    phaseEnd = gameState.get("phaseEnd") 
    time = parse_time(phaseEnd)
    if time:
        current_time = get_current_time()
        difference = time - current_time
        if difference.total_seconds() > 2:
                future_time = get_future_time(2)
                manage_cloud_task(game_id, 
                                payload={"gameId": game_id}, 
                                time_to_execute=future_time, 
                                db=db,
                                previous_task_id=game_dict.get("taskId"),
                                )
                gameState["phaseEnd"] = future_time.isoformat()

    gameState["selectedLetter"] = letter
    
    db.collection("games").document(game_id).update(
                {f"state.gameState": gameState},
    )



    return generate_success()
