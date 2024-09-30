import firebase_admin
from firebase_admin import credentials, auth, functions, firestore
import requests
import json
import datetime
import pytz
from google.oauth2 import service_account
import uuid

# Initialize the Firebase app
cred = credentials.Certificate('keys/te-kemu-arapu-firebase-adminsdk-w5ied-5142d8099b.json')
firebase_admin.initialize_app(cred)
credentials_file = service_account.Credentials.from_service_account_file('keys/te-kemu-arapu-firebase-adminsdk-w5ied-5142d8099b.json')


# Sign in anonymously
user = auth.create_user()

# Get the ID token
id_token = auth.create_custom_token(user.uid)

# # Define the URL for the Firebase function
# url = 'http://127.0.0.1:5001/te-kemu-arapu/us-central1/on_request_example'

# # Define the JSON payload
# payload = {
#     'message': 'Hello, world!'
# }

# # Make the request to the Firebase function
# headers = {
#     'Authorization': 'Bearer ' + id_token.decode('utf-8'),
#     'Content-Type': 'application/json'
# }
# response = requests.post(url, headers=headers, data=json.dumps(payload))

# # Print the response
# print(response.json())

from functions.cloud_task import create_cloud_task, delete_cloud_task
id = str(uuid.uuid4())
create_cloud_task( id, {"yea":"yea"}, datetime.datetime.now(tz=pytz.timezone("NZ")) + datetime.timedelta(seconds=5) ,credentials_file)
# delete_cloud_task(credentials_file, id)

