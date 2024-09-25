import datetime
import pytz


def get_current_time() -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("NZ"))


def get_future_time(seconds: int) -> datetime.datetime:
    return datetime.datetime.now(pytz.timezone("NZ")) + datetime.timedelta(seconds=seconds)

def parse_time(time: str) -> datetime.datetime:
    if time is None:
        return None
    return datetime.datetime.fromisoformat(time)