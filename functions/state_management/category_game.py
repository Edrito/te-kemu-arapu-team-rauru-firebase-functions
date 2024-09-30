from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from google.cloud.firestore import Client as FirestoreClient
from datetime_functions import get_current_time, parse_time, get_future_time
from state_management import category_game
from firebase_functions import https_fn
from response_format import generate_error, generate_success
from cloud_task import create_cloud_task
from constants import CATEGORIES, DIFFICULTY_TIMES, MAORI_ALPHABET
import random
from datetime import datetime


def template_game_state(datetime: datetime) -> dict:
    return {
        "phase": "choosingCategory",
        "phaseEnd": datetime.isoformat(),
        "positiveVotes": [],
        "negativeVotes": [],
        "neutralVotes": [],
        "lettersCovered": [],
        "playersEliminated": [],
        "hintWordsUsed": [],
        "playerTurn": None,
        "categoriesCovered": [],
        "currentCategory": None,
        "selectedLetter": None,
    }

def reset_votes(data: dict) -> dict:
    data["positiveVotes"] = []
    data["negativeVotes"] = []
    data["neutralVotes"] = []

    return data

def queue_game_state_call(
    game_state: dict, state: dict, doc_id: str, db: FirestoreClient, time: datetime, merge: bool = True
):
    create_cloud_task(
        doc_id, {"gameId": doc_id}, get_future_time(time), None
    )
    state["gameState"] = game_state
    db.collection("games").document(doc_id).set(state, merge=merge)

def game_end(doc_dict: dict, doc_id: str, db: FirestoreClient) -> https_fn.Response:
    state = doc_dict.get("state")
    state['phase'] = 'end'
    end_time = get_future_time(15)
    state['phaseEnd'] = end_time.isoformat()

    queue_game_state_call({}, state, doc_id, db, end_time)

    return generate_success()



def manage_game(doc_dict: dict, doc_id: str, db: FirestoreClient) -> https_fn.Response:
    state = doc_dict.get("state")
    game_state = state.get("gameState")
    phase = game_state.get("phase")

    # if phase is None, create a new game state
    if phase is None:
        end_time = get_future_time(5)
        game_state = template_game_state(end_time)
        queue_game_state_call(game_state, state, doc_id, db, end_time)
        return generate_success()

    phaseEnd = parse_time(game_state.get("phaseEnd"))
    time = get_current_time()

    if time < phaseEnd:
        queue_game_state_call(game_state, state, doc_id, db, phaseEnd)
        return generate_success()

    match phase:
        case "choosingCategory":
            categories_covered = game_state.get("categoriesCovered")
            # Pick a category that has not been convered from the CATEGORIES list, if they have all been chosen, choose a random one
            potential_categories = (
                cat for cat in CATEGORIES if cat not in categories_covered
            )
            if potential_categories is None:

                state['phase'] = 'end'
                end_time = get_future_time(15)
                state['phaseEnd'] = end_time.isoformat()
                queue_game_state_call(game_state, state, doc_id, db, end_time, merge= False)

                return generate_success()
            else:
                category = random.choice(list(potential_categories))

            # TODO add full category end condition meme
            game_state["currentCategory"] = category
            game_state["categoriesCovered"] = categories_covered.append(category)
            game_state["phase"] = "choosingPlayer"
            end_time = get_future_time(5)
            game_state["phaseEnd"] = end_time.isoformat()

            queue_game_state_call(game_state, state, doc_id, db, end_time)
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

            game_state["phase"] = "letterSelection"
            end_time = get_future_time(10)

            game_state["phaseEnd"] = end_time.isoformat()
            queue_game_state_call(game_state, state, doc_id, db, end_time)

            return generate_success()

        case "letterSelection":
            # get the next player from participants not in playersEliminated
            player_turn = game_state.get("playerTurn")
            selected_letter = game_state.get("selectedLetter")
            if selected_letter is None:
                players_eliminated = game_state.get("playersEliminated")
                player_eliminated.append(player_turn)
                game_state["phase"] = "choosingPlayer"

                end_time = get_future_time(5)
                game_state["phaseEnd"] = end_time.isoformat()

                queue_game_state_call(game_state, state, doc_id, db, end_time)
                return generate_success()

            elif selected_letter == "random":
                selected_letter = random.choice(MAORI_ALPHABET)

            player_doc = db.collection("profile").document(player_turn).get()
            difficulty = player_doc.get("difficulty")

            time = DIFFICULTY_TIMES[difficulty]

            game_state["phase"] = "voting"
            game_state = reset_votes(game_state)
            end_time = get_future_time(time)
            game_state["phaseEnd"] = end_time.isoformat()

            queue_game_state_call(game_state, state, doc_id, db, end_time)

            return generate_success()

        case "voting":
            # get the next player from participants not in playersEliminated
            player_turn = game_state.get("playerTurn")
            postive_votes = game_state.get("positiveVotes")
            negative_votes = game_state.get("negativeVotes")
            neutral_votes = game_state.get("neutralVotes")

            gets_point = None

            if len(postive_votes) > len(negative_votes):
                gets_point = True
            elif len(postive_votes) < len(negative_votes):
                gets_point = False
            else:
                gets_point = random.choice([True, False])

            if gets_point:
                scores = state.get("scores")
                if scores is None:
                    scores = {}
                if player_turn in scores:
                    scores[player_turn] += 1
                else:
                    scores[player_turn] = 1

            game_state = reset_votes(game_state)

            letters_covered = game_state.get("lettersCovered")
            selected_letter = game_state.get("selectedLetter")
            letters_covered.append(selected_letter)

            if len(letters_covered) == len(MAORI_ALPHABET):
                categories_covered = game_state.get("categoriesCovered")
                current_category = game_state.get("currentCategory")
                categories_covered.append(current_category)

                game_state["categoriesCovered"] = categories_covered
                game_state["phase"] = "choosingCategory"

            else:
                game_state["phase"] = "choosingPlayer"

            end_time = get_future_time(5)
            game_state["phaseEnd"] = end_time.isoformat()

            queue_game_state_call(game_state, state, doc_id, db, end_time)

            return generate_success()
