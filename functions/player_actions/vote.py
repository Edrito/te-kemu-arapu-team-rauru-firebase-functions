from google.cloud.firestore import Client as FirestoreClient 

def handle_action(data: dict, db: FirestoreClient):

    return {"status":"success"}