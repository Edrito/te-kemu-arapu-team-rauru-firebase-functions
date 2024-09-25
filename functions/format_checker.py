from firebase_functions import https_fn
import json


def check_format(req: https_fn.Request):
    if req.headers.get("Content-Type") != "application/json":
        return https_fn.Response(
            json.dumps({"error": "Content-Type must be application/json"}), 
            status=400,
            mimetype="application/json")
    return None