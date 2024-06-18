import _requests

def get(str url):
    str resp = _requests.get(url)
    return resp
