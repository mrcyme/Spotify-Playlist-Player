import json
import base64
import requests
import sys
sys.path.insert(0, "../")
from utils.custom_errors import handle_errors


CLIENT = json.load(open('spotifyAPI/keysPB.json', 'r+'))
CLIENT_ID = CLIENT['id']
CLIENT_SECRET = CLIENT['secret']
BASE64 = base64.b64encode(bytes(CLIENT_ID + ':' + CLIENT_SECRET, 'ascii'))
BASE64 = BASE64.decode('ascii')


# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)
JSON_CONTENT_TYPE = {"Content-Type": "application/json"}
JSON_ACCEPT = {"Accept": "application/json"}


CLIENT_SIDE_URL = "api.playlistmanager.xyz"
REDIRECT_URI = "http://0.0.0.0:5000/callback"


SCOPE = "user-read-recently-played user-read-playback-state user-modify-playback-state"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

# Parameters combine in one part
auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

url_args = "&".join(["{}={}".format(key, val) for key, val in auth_query_parameters.items()])
auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)


def start_playing_playlist(auth_header, playlist_uri):
    url = "{}/me/player/play".format(SPOTIFY_API_URL)
    data = {"context_uri": playlist_uri}
    data = json.dumps(data)
    resp = requests.put(url, headers=auth_header, data=data)
    handle_errors(resp)
    return resp


def get_current_user_profile(auth_header):
    url = "{}/me".format(SPOTIFY_API_URL)
    resp = requests.get(url, headers=auth_header)
    return resp.json()


def renew_token(refresh_token):
    headers = {"Authorization": "Basic {}".format(BASE64)}
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    resp = requests.post(SPOTIFY_TOKEN_URL, data=data, headers=headers)
    handle_errors(resp)
    return resp.json()


def get_current_playback(auth_header):
    url = "{}/me/player".format(SPOTIFY_API_URL)
    resp = requests.get(url, headers=auth_header)
    return resp


def skip_to_next_track(auth_header):
    url = "{}/me/player/next".format(SPOTIFY_API_URL)
    resp = requests.post(url, headers=auth_header)
    return resp.json()


def get_access_token(code):
    url = SPOTIFY_TOKEN_URL
    data = {"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI}
    headers = {"Authorization": "Basic {}".format(BASE64)}
    resp = requests.post(url, data=data, headers=headers)
    return resp.json()


def get_user_availlable_devices(auth_header):
    url = "{}/me/player/devices".format(SPOTIFY_API_URL)
    resp = requests.get(url, headers=auth_header)
    handle_errors(resp)
    return resp.json()
