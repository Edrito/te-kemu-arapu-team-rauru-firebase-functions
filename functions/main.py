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
from response_format import generate_error, generate_success
from datetime_functions import get_future_time, get_current_time, parse_time
import cloud_task as ct
import state_management.state as state
from google.cloud.firestore import (
    Client as FirestoreClient,
)  # importing the return type of firestore.client()

app = firebase_admin.initialize_app()


@https_fn.on_request(
    region="us-central1",
)
def manage_game_state(request: https_fn.Request) -> https_fn.Response:
    json_data = request.json
    game_id = json_data.get("gameId")
    db: FirestoreClient = firestore.client()
    document = db.collection("games").document(game_id).get()
    doc_dict = document.to_dict()
    time = get_current_time()
    phase_end = parse_time(doc_dict.get("state").get("phaseEnd"))

    if not phase_end or time > phase_end:

        result = state.manage_state(doc_dict, document.id, db)

        if result.status_code != 200:
            doc_dict["errors"] = (
                doc_dict.get("errors") + 1 if doc_dict.get("errors") is not None else 1
            )
            db.collection("games").document(game_id).set(doc_dict, merge=True)
            ct.create_cloud_task(
             game_id, {"gameId": game_id}, get_future_time(5), None
            )
            #TODO if errors > 5, end game
            return result
        else:
            return result

    else:
        ct.create_cloud_task(
         game_id, {"gameId": game_id}, phase_end, None
        )

    return https_fn.Response(json.dumps({}), content_type="application/json")


@https_fn.on_request(
    region="us-central1",
    cors=options.CorsOptions(
        cors_origins="*",
        cors_methods=["get", "post",],)
)
def on_player_action(req: https_fn.Request) -> https_fn.Response:

    try:

        db: FirestoreClient = firestore.client()
        # Check if content type is json
        format_result = check_format(req)
        if format_result is not None:
            return format_result

        json_data = req.json
        action = json_data.get("action")
        if action is None:
            return generate_error("No action provided", 400)

        action_type = action.get("type")

        match action_type:
            case "profile":
                #May not be used
                action_result = profile.handle_action(json_data, db)

            case "vote":
                action_result = vote.handle_action(json_data, db)

            case "lobbyUpsert":
                action_result = lobby.upsert(json_data, db)

            case "lobbyDelete":
                action_result = lobby.delete(json_data, db)

            case "lobbyJoin":
                action_result = lobby.join(json_data, db)

            case "lobbyLeave":
                action_result = lobby.leave(json_data, db)

            case "lobbyStart":
                action_result = game.start(json_data, db)

            case "categoryVote":
                action_result = categoryVote.handle_action(json_data, db)

            case "letterSelect":
                action_result = letterSelect.handle_action(json_data, db)
            case "pass":
                action_result = _pass.handle_action(json_data, db)

        if action_result is not None:
            return action_result

        return generate_error(f"Unknown player action -> {action_type}", 500)
    

    except Exception as e:
        raise e
        
