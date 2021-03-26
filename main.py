import kivy
import requests
import webbrowser
import random
import spotifyAPI.spotify_api_utils as SPOTIFY
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.storage.jsonstore import JsonStore
from kivy.properties import ListProperty
from kivy.clock import Clock
from functools import partial
from flask import Flask
from flask import request
from eventlet import wsgi
from time import sleep
from utils.custom_errors import handle_errors, TokenError, ResourceNotFoundError
from utils.custom_decorators import token_auto_refresh
from threading import Thread
kivy.require('1.10.0')

store = JsonStore('tokens.json')
PLAYSWAP_API_URL = "https://api.playlistmanager.xyz/playlister"


def renew_token():
    refreshToken = store.get('tokens')['refreshToken']
    name = store.get('tokens')['name']
    resp = SPOTIFY.renew_token(refreshToken)
    store.put('tokens', accessToken=resp['accessToken'], refreshToken=resp['refreshToken'], name=name)

def get_playlist_list(self):
    url = "{}/ak4!a0ZEà-(".format(PLAYSWAP_API_URL)
    playlists = [p for p in requests.get(url).json() if p['get_length'] != 0]
    uris = ['spotify:playlist:{}'.format(p['spotifyId']) for p in playlists]
    ids = [p['spotifyId'] for p in playlists]
    names = [p['name'] for p in playlists]
    random.shuffle(uris)
    return uris, ids, names

class MyApp(App):
    title = 'Playlist Player'
    playlists = ListProperty([])
    tracks = ListProperty([])
    connection = ListProperty([])

    def build(self):
        Clock.schedule_interval(self.consume_playlists, 0)
        Clock.schedule_interval(self.consume_tracks, 0)
        root = BoxLayout(orientation='vertical')
        wid = Widget()
        connectionLayout = BoxLayout(size_hint=(1, 0.25))
        if not store.exists('tokens'):
            labelConnection = Label(text='Waiting for connection')
            Clock.schedule_interval(self.consume_connection, 0)
        else:
            userName = store.get('tokens')['name']
            labelConnection = Label(text="Connected as {}".format(userName))
        btnConnect = Button(text='Connect', on_press=partial(self.connect))
        btnDisconnect = Button(text='Disconnect', on_press=partial(self.disconnect, labelConnection))
        if not store.exists('tokens'):
            connectionLayout.add_widget(btnConnect)

        connectionLayout.add_widget(btnDisconnect)
        connectionLayout.add_widget(labelConnection)

        devicesLayout = BoxLayout(size_hint=(1, 0.25))
        labelDevices = Label(text='No active devices please scan')

        btnScan = Button(text='Scan for device',
                         on_press=partial(self.get_devices, labelDevices))
        devicesLayout.add_widget(btnScan)
        devicesLayout.add_widget(labelDevices)

        labelPlay = Label(text='Not playling')
        playLayout = BoxLayout(size_hint=(1, 0.5))
        btnStart = Button(text='Start Playing', on_press=partial(self.start_playing, labelPlay))
        playLayout.add_widget(btnStart)
        playLayout.add_widget(labelPlay)

        screenPlaylistsLayout = BoxLayout(size_hint=(1, 0.25))
        labelPlaylistsScreen = Label(text='inactive')
        screenPlaylistsLayout.add_widget(labelPlaylistsScreen)

        screenTracksLayout = BoxLayout(size_hint=(1, 0.25))
        labelTracksScreen = Label(text='')
        screenTracksLayout.add_widget(labelTracksScreen)

        root.add_widget(playLayout)
        root.add_widget(devicesLayout)
        root.add_widget(connectionLayout)
        root.add_widget(screenPlaylistsLayout)
        root.add_widget(screenTracksLayout)
        root.add_widget(wid)
        return root

    def consume_playlists(self, *args):
        while self.playlists:
            item = self.playlists.pop(0)
            self.root.children[2].children[0].text = item

    def consume_tracks(self, *args):
        while self.tracks:
            item = self.tracks.pop(0)
            self.root.children[1].children[0].text = item

    def consume_connection(self, *args):
        while self.connection:
            item = self.connection.pop(0)
            self.root.children[3].children[0].text = item

    def connect(self, *args):
        self.start_flask()
        webbrowser.open(SPOTIFY.auth_url)

    def disconnect(self, label, *args):
        try:
            store.delete('tokens')
        except KeyError:
            pass
        label.text = "You're disconnected, please restart to connect"

    @token_auto_refresh(on_token_error=renew_token)
    def get_devices(self, label, *args):
        if not store.exists('tokens'):
            App.get_running_app().playlists.append("You are not connected to spotify")
        else:
            auth_header = {"Authorization": "Bearer {}".format(store.get('tokens')['accessToken'])}
            resp = SPOTIFY.get_user_availlable_devices(auth_header)
            if 'devices' in resp:
                devices = [x['name'] for x in resp['devices'] if x['is_active']==True]
                if devices:
                    label.text = "devices : {}".format(",".join(devices))
                else:
                    label.text = "Found device but inactive. \n Please start playling something on spotify"
            else:
                label.text = "No active devises found please launch spotify"

    def start_playing(self, label, *args):
        if not store.exists('tokens'):
            App.get_running_app().playlists.append("You are not connected to spotify")
        else:
            label.text = "playing"
            global t1
            t1 = Thread(target=self.play, daemon=True)
            t1.start()

    def play(self):
        playling = True
        auth_header = {"Authorization": "Bearer {}".format(store.get('tokens')['accessToken'])}
        while playling:
            uris, ids, names = self.get_playlist_list()
            for uri, id, name in zip(uris, ids, names):
                try:
                    resp = SPOTIFY.start_playing_playlist(auth_header, uri)
                    handle_errors(resp)
                    App.get_running_app().playlists.append("Start playling playlist {}, id : {}".format(name,id))
                    sleep(2)
                except TokenError:
                    self.renew_token()
                    continue
                except ResourceNotFoundError:
                    App.get_running_app().playlists.append("No active device found")
                    playling = False
                    break
                except Exception as e:
                    App.get_running_app().playlists.append(str(e))
                    playling = False
                    break
                numberOfSongPass = random.randint(0, 10)
                for i in range(numberOfSongPass):
                    duration = random.randint(4, 200)
                    try:
                        resp = SPOTIFY.get_current_playback(auth_header)
                        handle_errors(resp)
                        if resp.status_code == 204:
                            App.get_running_app().tracks.append("You have quitted your sotify player please open and retry")
                        else:
                            track_name = resp.json()['item']['name']
                            App.get_running_app().tracks.append("playing track {} for {} seconds".format(track_name,duration))
                    except TokenError:
                        self.renew_token()
                        continue
                    except Exception as e:
                        App.get_running_app().tracks.append(str(e))
                        break
                    sleep(duration)
                    try:
                        resp = SPOTIFY.skip_to_next_track(auth_header)
                        handle_errors(resp)
                        App.get_running_app().tracks.append("Skipping to next track")
                        sleep(2)
                    except TokenError:
                        self.renew_token()
                        continue
                    except Exception as e:
                        App.get_running_app().tracks.append(str(e))

    def start_flask_server(self):
        app = Flask(__name__)
        @app.route('/callback/', methods=['GET'])
        def get_auth():
            if ('code' in request.args):
                code = request.args.get('code')
                resp = SPOTIFY.get_access_token(code)
                auth_header = {"Authorization": "Bearer {}".format(resp["access_token"])}
                spotifyinfo = SPOTIFY.get_current_user_profile(auth_header)
                store.put('tokens', accessToken=resp["access_token"], refreshToken=resp["refresh_token"], name=spotifyinfo['display_name'])
                App.get_running_app().connection.append("Connected as {}".format(spotifyinfo['display_name']))
            else:
                return "something wrong"
            return "you're good"
        #wsgi.server(eventlet.listen(('', 5000)), app)
        app.run("0.0.0.0")

    def start_flask(self):
        global p1
        p1 = Thread(target=self.start_flask_server, daemon=True)
        p1.start()

if __name__ == '__main__':
    MyApp().run()
