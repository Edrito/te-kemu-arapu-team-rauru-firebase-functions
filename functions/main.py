from firebase_functions import https_fn
from firebase_admin import initialize_app,firestore
import json
from format_checker import check_format
import functions.player_actions.profile as profile
import functions.player_actions.vote as vote
import functions.player_actions.lobby as lobby
import datetime
from response_format import generate_error, generate_success


from google.cloud.firestore import Client as FirestoreClient # importing the return type of firestore.client()
db: FirestoreClient = firestore.client()




initialize_app()

def manage_game_state(request: https_fn.Request) -> https_fn.Response:
    json_data = request.json
    game_id = json_data.get("gameId")
    
    return https_fn.Response(json.dumps({}), content_type="application/json")


@https_fn.on_request()
def on_player_action(req: https_fn.Request) -> https_fn.Response:
    # Check if content type is json
    format_result = check_format(req)
    if format_result is not None:
        return format_result

    json_data = req.json
    action = json_data.get("action")
    if action is None:
        return  generate_error("No action provided", 400)
    
    action_type = action.get("type")

    match action_type:
        case "profile":
            action_result = profile.handle_action(json_data, db)

        case "vote":
            action_result = vote.handle_action(json_data, db)

        case "lobby_upsert":
            action_result = lobby.upsert(json_data, db)

        case "lobby_delete":
            action_result = lobby.delete(json_data, db)

        case "lobby_join":
            action_result = lobby.join(json_data, db)

        case "lobby_leave":
            action_result = lobby.leave(json_data, db)





    if action_result is not None:
        return action_result

    return generate_error("Unknown error.", 500)
