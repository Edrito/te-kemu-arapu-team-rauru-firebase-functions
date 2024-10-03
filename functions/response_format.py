from firebase_functions import https_fn
import json
import datetime

def generate_error(msg:str, code:int)-> https_fn.Response:
    return https_fn.Response(
        json.dumps(
            {
                "error": {
                    "errorMessage": msg,
                    "timestamp": datetime.datetime.now().isoformat(),
                }
            }
        ),
        status=code,
        mimetype="application/json",
    )

def generate_success(msg:str = None, custom_payload:dict = None)-> https_fn.Response:
    return https_fn.Response(
        json.dumps(
            {
                "status": msg if msg is not None else "success",
            } if custom_payload is None else custom_payload
        ),
        status=200,
        mimetype="application/json",
   )