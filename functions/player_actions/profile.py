from google.cloud.firestore import Client as FirestoreClient 
import datetime
from response_format import generate_error, generate_success


def handle_action(data: dict, db: FirestoreClient):
    
    action = data.get('action')
    details = action.get('details')
    if details is None:
        return generate_error("No details provided", 400)
    
    details["lastUpdated"] = datetime.datetime.now().isoformat()
    db.collection("players").document(data.get("playerId"))\
        .set(details, merge=True)

    return generate_success()