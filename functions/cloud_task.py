from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import json
import datetime
import uuid
from google.cloud.firestore import Client as FirestoreClient
from google.auth.transport.requests import Request
from google.oauth2 import id_token

def get_queue_path(client: tasks_v2.CloudTasksClient) -> str:
    project_id = 'te-kemu-arapu'
    queue_name = 'te-kemu-arapu-queue'
    location = 'us-central1'
    parent = client.queue_path(project_id, location, queue_name)
    return parent

def delete_cloud_task(gameId, taskId):
    try:
        # Create a client using default credentials
        client = tasks_v2.CloudTasksClient()
        parent = get_queue_path(client)
        # Check if task exists before trying to delete
        task = client.get_task(name=parent + "/tasks/" + gameId + "_" + taskId)
        if task:
            client.delete_task(name=parent + "/tasks/" + gameId + "_" + taskId)
    except Exception as e:
        print(f"Error deleting task: {e}")


def manage_cloud_task(gameId, payload, time_to_execute: datetime.datetime, db: FirestoreClient = None, deleteOnly: bool = False, previous_task_id=None):
    project_id = 'te-kemu-arapu'
    location = 'us-central1'

    previous_task_id = db.collection('games').document(gameId).get().to_dict().get("taskId") if previous_task_id is None else previous_task_id
    if previous_task_id:
        delete_cloud_task(gameId, taskId=previous_task_id)

    if deleteOnly:
        return

    task_id = str(uuid.uuid4())
    id = gameId + "_" + task_id
    db.collection('games').document(gameId).set({"taskId": task_id}, merge=True)

    # Create a client using default credentials
    client = tasks_v2.CloudTasksClient()

    # Construct the fully qualified queue name
    parent = get_queue_path(client)

    url = f'https://{location}-{project_id}.cloudfunctions.net/manage_game_state'

    # Generate an ID token
    audience = url
    id_token_credentials = id_token.fetch_id_token(Request(), audience)

    # Construct the request body
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': url,
            'headers': {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {id_token_credentials}'
            }
        },
        "name": parent + "/tasks/" + id
    }

    print(f"Task name: {task['name']}")

    # Add the payload to the request
    if payload is not None:
        converted_payload = json.dumps(payload).encode()
        task['http_request']['body'] = converted_payload

    # Set the task delay or future execution time
    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromDatetime(time_to_execute)
    task['schedule_time'] = timestamp

    # Use the client to build and send the task
    try:
        response = client.create_task(parent=parent, task=task)
        print(f'Task created: {response.name}')
    except Exception as e:
        print(f"Error creating task: {e}")