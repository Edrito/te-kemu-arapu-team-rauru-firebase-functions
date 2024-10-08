from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from google.cloud.firestore import Client as FirestoreClient
from datetime_functions import get_current_time, parse_time, get_future_time
from state_management import category_game
from firebase_functions import https_fn
from response_format import generate_error, generate_success
from cloud_task import manage_cloud_task
from constants import CATEGORIES, DIFFICULTY_TIMES, MAORI_ALPHABET_LIST, TIMES
import random
from datetime import datetime


def template_game_state(datetime: datetime) -> dict:
    return {
        "phase": "choosingCategory",
        "phaseEnd": datetime.isoformat(),
        "categoryVotes": {},
        "votes": {},
        "lettersCovered": [],
        "playersEliminated": [],
        # "hintWordsUsed": [],
        "playerTurn": None,
        "playerPassed": None,
        "categoriesCovered": [],
        "currentCategory": None,
        "selectedLetter": None,
    }


def queue_game_state_call(
    game_state: dict,
    state: dict,
    doc_id: str,
    db: FirestoreClient,
    end_time: datetime,
    doc_data: dict | None = None,
    merge: bool = True,
):
    state["gameState"] = game_state

    if not merge and doc_data:
        doc_data["state"] = state
        db.collection("games").document(doc_id).set(doc_data)
    else:
        db.collection("games").document(doc_id).set({"state": state}, merge=True)
    
    manage_cloud_task(doc_id, {"gameId": doc_id}, end_time, db=db)


def end_game(doc_dict: dict, doc_id: str, db: FirestoreClient) -> https_fn.Response:
    state = doc_dict.get("state")
    state["phase"] = "end"
    end_time = get_future_time(TIMES.end)
    state["phaseEnd"] = end_time.isoformat()

    queue_game_state_call(
        game_state={},
        state=state,
        doc_id=doc_id,
        db=db,
        end_time=end_time,
        merge=False,
        doc_data=doc_dict,
    )

    return generate_success()


def eliminate_player(
    doc_dict: dict, doc_id: str, db: FirestoreClient
) -> https_fn.Response:

    state = doc_dict.get("state")
    game_state = state.get("gameState")
    game_state["phase"] = "choosingPlayer"


    
    player_turn = game_state.get("playerTurn")

    players_eliminated = game_state.get("playersEliminated")
    players_eliminated.append(player_turn)
    game_state["playersEliminated"] = players_eliminated
    if len(players_eliminated) == len(doc_dict.get("participants")):
        return manage_game(doc_dict, doc_id, db)
    

    
    end_time = get_future_time(TIMES.choosing_player)
    game_state["phaseEnd"] = end_time.isoformat()

    game_state["votes"] = {}
    game_state["playerPassed"] = None
    game_state["selectedLetter"] = None

    queue_game_state_call(
        game_state=game_state,
        state=state,
        doc_id=doc_id,
        db=db,
        end_time=end_time,
    )

    return generate_success()


def complete_category(
    doc_dict: dict, state: dict, game_state: dict, doc_id: str, db: FirestoreClient
) -> https_fn.Response:
    game_state["votes"] = {}
    game_state["playerPassed"] = None
    game_state["selectedLetter"] = None
    game_state["lettersCovered"] = []
    game_state["phase"] = "choosingCategory"

    if len(game_state.get("categoriesCovered")) == len(CATEGORIES):
        doc_dict["state"] = state
        return end_game(doc_dict, doc_id, db)

    end_time = get_future_time(TIMES.choosing_category)
    game_state["phaseEnd"] = end_time.isoformat()

    queue_game_state_call(
        game_state=game_state,
        state=state,
        doc_id=doc_id,
        db=db,
        end_time=end_time,
    )

    return generate_success()


def manage_game(doc_dict: dict, doc_id: str, db: FirestoreClient) -> https_fn.Response:
    state = doc_dict.get("state")
    game_state = state.get("gameState")
    phase = game_state.get("phase")

    # if phase is None, create a new game state
    if phase is None:
        end_time = get_future_time(TIMES.choosing_category)
        game_state = template_game_state(end_time)
        queue_game_state_call(
            game_state=game_state,
            state=state,
            doc_id=doc_id,
            db=db,
            end_time=end_time,
        )
        return generate_success()

    phaseEnd = parse_time(game_state.get("phaseEnd"))
    time = get_current_time()

    if time < phaseEnd:
        queue_game_state_call(
            game_state=game_state,
            state=state,
            doc_id=doc_id,
            db=db,
            end_time=phaseEnd,
        )
        return generate_success()

    match phase:
        case "choosingCategory":
            categories_covered = (
                game_state.get("categoriesCovered")
                if game_state.get("categoriesCovered") is not None
                else []
            )
            category_votes = (
                game_state.get("categoryVotes")
                if game_state.get("categoryVotes") is not None
                else {}
            )
            categories = category_votes.values()

            game_state["categoryVotes"] = {}
            counts = {}

            for category in categories:
                if category in counts:
                    counts[category] += 1
                else:
                    counts[category] = 1

            most_voted_category = max(counts, key=counts.get) if counts else None

            if most_voted_category is None or most_voted_category in categories_covered:
                potential_categories = (
                    cat for cat in CATEGORIES if cat not in categories_covered
                )
                if potential_categories is None:
                    return end_game(doc_dict, doc_id, db)
                else:
                    most_voted_category = random.choice(list(potential_categories))

            game_state["currentCategory"] = most_voted_category
            categories_covered.append(most_voted_category)
            game_state["categoriesCovered"] = categories_covered
            game_state["phase"] = "choosingPlayer"
            end_time = get_future_time(TIMES.choosing_player)
            game_state["phaseEnd"] = end_time.isoformat()
            game_state["categoryVotes"] = {}

            queue_game_state_call(
                game_state=game_state,
                state=state,
                doc_id=doc_id,
                db=db,
                end_time=end_time,
            )
            return generate_success()

        case "choosingPlayer":
            # get the next player from participants not in playersEliminated
            player_turn = game_state.get("playerTurn")

            participants = []
            # copy
            if doc_dict.get("participants") is not None:
                for player in doc_dict.get("participants"):
                    participants.append(player)

            players_eliminated = (
                game_state.get("playersEliminated")
                if game_state.get("playersEliminated") is not None
                else []
            )

            players_remaining = [
                player for player in participants if player not in players_eliminated
            ]

            if len(players_remaining) == 0:
                game_state["playersEliminated"] = []
                return complete_category(
                    doc_dict=doc_dict,
                    doc_id=doc_id,
                    state=state,
                    game_state=game_state,
                    db=db,
                )

            if player_turn is None:
                player_turn = random.choice(list(players_remaining))
            else:
                for player_eliminated in players_eliminated:
                    # remove eliminated players from participants, but not the previous player turn
                    # so we know whos next
                    if (
                        player_eliminated in participants
                        and player_eliminated != player_turn
                    ):
                        participants.remove(player_eliminated)

                player_turn = participants[
                    (participants.index(player_turn) + 1) % len(participants)
                ]

            game_state["phase"] = "letterSelection"
            game_state["playerTurn"] = player_turn
            end_time = get_future_time(TIMES.letter_selection)

            game_state["phaseEnd"] = end_time.isoformat()
            queue_game_state_call(
                game_state=game_state,
                state=state,
                doc_id=doc_id,
                db=db,
                end_time=end_time,
            )

            return generate_success()

        case "letterSelection":
            # get the next player from participants not in playersEliminated
            player_turn = game_state.get("playerTurn")
            selected_letter = game_state.get("selectedLetter")
            player_pass = game_state.get("playerPassed")
            if selected_letter is None or player_pass:
                return eliminate_player(doc_dict, doc_id, db)

            elif selected_letter == "random":
                selected_letter = random.choice(MAORI_ALPHABET_LIST)

            player_doc = db.collection("profile").document(player_turn).get()
            if not player_doc.exists:
                difficulty = "Beginner"
            else:
                difficulty = player_doc.get("difficulty")

            time = DIFFICULTY_TIMES[difficulty]

            game_state["phase"] = "voting"
            game_state["selectedLetter"] = selected_letter
            game_state["votes"] = {}
            end_time = get_future_time(time)
            game_state["phaseEnd"] = end_time.isoformat()

            queue_game_state_call(
                game_state=game_state,
                state=state,
                doc_id=doc_id,
                db=db,
                end_time=end_time,
            )

            return generate_success()

        case "voting":
            player_passed = game_state.get("playerPassed")

            if player_passed:
                return eliminate_player(doc_dict, doc_id, db)

            # get the next player from participants not in playersEliminated
            player_turn = game_state.get("playerTurn")

            votes = game_state.get("votes")
            postive_votes = [vote for vote in votes.values() if vote == "positive"]
            negative_votes = [vote for vote in votes.values() if vote == "negative"]

            gets_point = None

            if len(postive_votes) > len(negative_votes):
                gets_point = True
            elif len(postive_votes) < len(negative_votes):
                gets_point = False
            else:
                gets_point = True


            if gets_point:
                scores = state.get("scores")
                if scores is None:
                    scores = {}
                if player_turn in scores:
                    scores[player_turn] += 1
                else:
                    scores[player_turn] = 1

            game_state["votes"] = {}

            letters_covered = game_state.get("lettersCovered")
            selected_letter = game_state.get("selectedLetter")
            letters_covered.append(selected_letter)

            if len(letters_covered) == len(MAORI_ALPHABET_LIST):
                return complete_category(
                    doc_dict=doc_dict,
                    doc_id=doc_id,
                    state=state,
                    game_state=game_state,
                    db=db,
                )
            else:
                game_state["phase"] = "choosingPlayer"

            end_time = get_future_time(TIMES.choosing_player)
            game_state["phaseEnd"] = end_time.isoformat()

            queue_game_state_call(
                game_state=game_state,
                state=state,
                doc_id=doc_id,
                db=db,
                end_time=end_time,
            )

            return generate_success()
