import firebase_admin
from firebase_admin import credentials, auth, functions, firestore
import requests
import json
import datetime
import pytz
from google.oauth2 import service_account
import uuid
import asyncio
from time import sleep
import random

potential_letters = [
                                "a",
                                "e",
                                "h",
                                "i",
                                "k",
                                "m",
                                "n",
                                "o",
                                "p",
                                "r",
                                "t",
                                "u",
                                "w"
                            ]

potential_categories = ["food", "landmarks", "nature"]

# Initialize the Firebase app
cred = credentials.Certificate(
    "keys/te-kemu-arapu-firebase-adminsdk-w5ied-5142d8099b.json"
)
firebase_admin.initialize_app(cred)


number_of_players = 3
users = {}
# Sign in anonymously
for i in range(number_of_players):
    user = auth.create_user()

    # Get the ID token
    id_token = auth.create_custom_token(user.uid)

    # Define the URL for the Firebase function
    url = "https://on-player-action-5koq7jxpyq-uc.a.run.app"
    player_id = user.uid

    users[user.uid] = {
        "player_id": player_id,
        "id_token": id_token,
    }

game_id = list(users.keys())[0]


def create_payload(playerId, actionType, details: dict):
    return {
        "playerId": playerId,
        "gameId": game_id,
        "action": {"type": actionType, "details": details},
    }


def create_category_vote_payload(playerId, category):
    return create_payload(playerId, "categoryVote", {"category": category})


def create_letter_vote(playerId, letter):
    return create_payload(playerId, "letterSelect", {"letter": letter})

def create_pass_payload(playerId):
    return create_payload(playerId, "pass", {})

def create_vote_payload(playerId, vote):
    return create_payload(playerId, actionType="vote", details={"voteType": vote})


def create_lobby(playerId):
    return create_payload(
        playerId,
        "lobbyUpsert",
        {
            "settings": {
                "games": {
                    "0": {
                        "type": "category",
                    },
                }
            },
        },
    )


def start_lobby(playerId):
    return create_payload(playerId, "lobbyStart", {})


# Make the request to the Firebase function
headers = {
    "Authorization": "Bearer " + id_token.decode("utf-8"),
    "Content-Type": "application/json",
}


def post_action(payload):
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response


turn_taken = {}
for user in users.values():
    turn_taken[user["player_id"]] = ""

global previous_message
global lobby_joined
previous_message = ""
lobby_joined = []


# Define the callback function
def stream_callback(doc_snapshot, changes, read_time):
    global previous_message
    if len(doc_snapshot) == 0:
        print("Document does not exist")
        return
    doc = doc_snapshot[0]
    if not doc.exists:
        print("Document does not exist")
        return
    data = doc.to_dict()
    is_lobby_open = data.get("isLobbyOpen")
    participants = data.get("participants")
    has_joiner = False

    if is_lobby_open:
        for user in users.values():
            if  user["player_id"] not in lobby_joined:
                has_joiner = True
                print(f"Joining lobby as {user['player_id']}")
                lobby_joined.append(user["player_id"])
                post_action(create_payload(user["player_id"], "lobbyJoin", {}))
        if has_joiner:
            return
        
    if is_lobby_open:
        print("Starting game")
        post_action(start_lobby(game_id))
        return

    state = data.get("state")
    state = {} if state is None else state
    state_phase = state.get("phase")
    game_state = state.get("gameState")
    game_state = {} if game_state is None else game_state
    game_phase = game_state.get("phase")
    categories_covered = (
        game_state.get("categoriesCovered")
        if game_state.get("categoriesCovered") is not None
        else []
    )
    letters_covered = (
        game_state.get("lettersCovered")
        if game_state.get("lettersCovered") is not None
        else []
    )

    new_message = (state_phase if state_phase else "") + (
        game_phase if game_phase else ""
    )

    if new_message != previous_message:
        previous_message = new_message
        print(f"State: {state_phase}, Game: {game_phase}")

    i = 0
    for user in users.values():
        i += 1
        player_id = user["player_id"]

        is_user_turn = player_id == game_state.get("playerTurn")
        is_lobby_host = player_id == game_id

        if turn_taken[user["player_id"]] == (state_phase if state_phase else "") + (
            game_phase if game_phase else ""
        ):
            continue

        try:
            match state_phase:
                case "loading":
                    ...
                case "playing":
                    match game_phase:
                        case "choosingCategory":
                            # sleep(random.randint(1, 3))
                            if random.choice([True, False]):
                                for category in potential_categories:
                                    if category not in categories_covered:
                                        print(
                                            f"Player {i}: Voting for category {category}"
                                        )
                                        post_action(
                                            create_category_vote_payload(
                                                player_id, category
                                            )
                                        )
                                        break
                            else:
                                print(f"Player {i}: Not voting for category")

                        case "choosingPlayer":
                            ...
                        case "letterSelection":
                            if not is_user_turn:
                                print(f"Player {i}: Not my turn")
                                continue
                            # sleep(random.randint(1, 3))

                            random_float = random.random()
                            

                            if random_float < 0.4:
                                for letter in potential_letters:
                                    if letter not in letters_covered:
                                        print(f"Player {i}: Voting for letter {letter}")
                                        post_action(
                                            create_letter_vote(player_id, letter)
                                        )
                                        break
                            elif random_float < 0.8:
                                print(f"Player {i}: Voting for random")
                                post_action(create_letter_vote(player_id, "random"))
                            elif random_float < 0.9:
                                print(f"Player {i}: Passing Letter Vote")
                                post_action(create_pass_payload(player_id))
                            else:
                                print(f"Player {i}: Not voting for letter")

                        case "voting":
                            ...
                            # sleep(random.randint(1, 3))

                            if not is_user_turn:
                                voteType = random.choice(
                                    ["positive", "negative", "neutral"]
                                )
                                print(f"Player {i}: Voting {voteType}")
                                post_action(create_vote_payload(player_id, voteType))

                            else:
                                random_float = random.random()
                                if random_float < 0.2:
                                    print(f"Player {i}: It's my turn and I'm passing")
                                    post_action(create_pass_payload(player_id))
        finally:
            turn_taken[player_id] = (state_phase if state_phase else "") + (
                game_phase if game_phase else ""
            )


doc_ref = firestore.client().collection("games").document(game_id)

doc_watch = doc_ref.on_snapshot(stream_callback)

post_action(create_lobby(playerId=game_id))


while True:
    sleep(.1)
