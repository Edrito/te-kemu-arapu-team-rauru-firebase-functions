from firebase_admin import firestore
from google.cloud.firestore_v1 import DocumentSnapshot
from google.cloud.firestore import Client as FirestoreClient 
from datetime_functions import get_current_time, parse_time
from state_management import category_game
from firebase_functions import https_fn
from response_format import generate_error, generate_success


def manage_game(doc_dict:dict,doc_id:str, db: FirestoreClient) -> https_fn.Response:
    return generate_error("Not implemented", 501)