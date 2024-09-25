from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from google.cloud.firestore import Client as FirestoreClient
from datetime_functions import get_current_time, parse_time, get_future_time
from state_management import category_game
from firebase_functions import https_fn
from response_format import generate_error, generate_success
from cloud_task import create_cloud_task
from constants import CATEGORIES, DIFFICULTY_TIMES
import random


def template_game_state():
    return {
        "phase": "choosingCategory",
        "phaseEnd": get_future_time(5).isoformat(),
        "positiveVotes": [],
        "negativeVotes": [],
        "neutralVotes": [],
        "lettersCovered": [],
        "category": None,
        "playersEliminated": [],
        "hintWordsUsed": [],
        "playerTurn": None,
        "categoriesCovered": [],
        "currentCategory": None,
    }


def manage_game(doc_dict: dict, doc_id: str, db: FirestoreClient) -> https_fn.Response:
    state = doc_dict.get("state")
    game_state = state.get("gameState")
    phase = game_state.get("phase")

    # if phase is None, create a new game state
    if phase is None:
        game_state = template_game_state()
        create_cloud_task(
            "game_state", doc_id, {"gameId": doc_id}, get_future_time(5), None
        )
        db.collection("games").document(doc_id).set(
            {"state": {"gameState": game_state}}, merge=True
        )
        return generate_success()

    phaseEnd = parse_time(game_state.get("phaseEnd"))
    time = get_current_time()

    if time < phaseEnd:
        create_cloud_task("game_state", doc_id, {"gameId": doc_id}, phaseEnd, None)
        return generate_success()

    match phase:
        case "choosingCategory":
            categories_covered = game_state.get("categoriesCovered")
            # Pick a category that has not been convered from the CATEGORIES list, if they have all been chosen, choose a random one
            potential_categories = (
                cat for cat in CATEGORIES if cat not in categories_covered
            )
            if potential_categories is None:
                category = random.choice(CATEGORIES)
            else:
                category = random.choice(list(potential_categories))

            # TODO add full category end condition meme
            game_state["currentCategory"] = category
            game_state["categoriesCovered"] = categories_covered.append(category)
            game_state["phase"] = "choosingPlayer"
            game_state["phaseEnd"] = get_future_time(5).isoformat()
            create_cloud_task(
                "game_state", doc_id, {"gameId": doc_id}, get_future_time(5), None
            )
            return generate_success()
        case "choosingPlayer":
            # get the next player from participants not in playersEliminated
            player_turn = game_state.get("playerTurn")
            participants = doc_dict.get("participants")
            players_eliminated = game_state.get("playersEliminated")

            if player_turn is None:
                player_turn = random.choice(participants)
            else:
                for player_eliminated in players_eliminated:
                    if player_eliminated in participants:
                        participants.remove(player_eliminated)
                # next player, not random
                player_turn = participants[
                    (participants.index(player_turn) + 1) % len(participants)
                ]

            player_doc = db.collection("players").document(player_turn).get()
            difficulty = player_doc.get("difficulty")
            
            time = DIFFICULTY_TIMES[difficulty]

            game_state["phase"] = "voting"
            game_state["phaseEnd"] = get_future_time(time).isoformat()
            create_cloud_task(
                "game_state", doc_id, {"gameId": doc_id}, get_future_time(time), None
            )

            return generate_success()
