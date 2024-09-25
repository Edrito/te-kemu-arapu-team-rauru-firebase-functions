from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
import json
import datetime


def get_queue_path( client:tasks_v2.CloudTasksClient)-> str:
    project_id = 'te-kemu-arapu'
    queue_name = 'te-kemu-arapu-queue'
    location = 'us-central1' 
    # Create a client
    parent = client.queue_path(project_id, location, queue_name)
    return parent 

def delete_cloud_task(cred, gameId):
    # Create a client
    client = tasks_v2.CloudTasksClient(credentials=cred)
    parent = get_queue_path(client)
    client.delete_task(name=parent + "/tasks/"+gameId)

def create_cloud_task( type,gameId, payload,time_to_execute:datetime.datetime, cred):
    project_id = 'te-kemu-arapu'
    location = 'us-central1' 
    
    # Create a client
    client = tasks_v2.CloudTasksClient(credentials=cred)

    # Construct the fully qualified queue name
    parent = get_queue_path(client)
    # client.create_queue(parent=parent, queue={"name": parent})

    match type:
        case "game_state":
            url = f'https://{location}-{project_id}.cloudfunctions.net/game_state'
        case "player_action":
            url = "https://webhook.site/3ea89678-34dc-42b0-8ad7-6c45bcf06fc1"

    # Construct the request body
    task = {
        'http_request': {  
            'http_method': tasks_v2.HttpMethod.POST,
            'url': url
        },
        "name" :parent + "/tasks/"+gameId
    }


    print(task['name'])

    # Add the payload to the request
    if payload is not None:
        converted_payload = json.dumps(payload).encode()
        task['http_request']['body'] = converted_payload
        task['http_request']['headers'] = {'Content-Type': 'application/json'}

    # Optionally set a task delay or future execution time
    # In this example, we're scheduling the task to run immediately
    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromDatetime(time_to_execute)
    task['schedule_time'] = timestamp

    # Use the client to build and send the task
    response = client.create_task(
        parent=parent, task=task)
    
    print(f'Task created: {response.name}')


