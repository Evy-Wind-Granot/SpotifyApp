import os
from flask import Flask, request, redirect, session, url_for
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

client_id = '2a7b04bae4144b78a22750a9f551a877'
client_secret = '3cdf9a838646484a965b437d3e9d6e42'
redirect_uri = 'http://localhost:5000/callback'
scope = 'user-modify-playback-state user-read-playback-state playlist-read-private'


cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)
sp = Spotify(auth_manager=sp_oauth)

@app.route('/')
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('current_playlist'))

@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('current_playlist'))

@app.route('/current_playlist')
def current_playlist():
    playback = sp.current_playback()

    if playback and playback['context'] and 'playlist' in playback['context']['type']:
        playlist_id = playback['context']['uri'].split(':')[-1]
        playlist = sp.playlist_tracks(playlist_id)
       
        tracks_info = []
        shortest_track = None
        shortest_duration = float('inf')

        for track in playlist['items']:
            track_name = track['track']['name']
            track_uri = track['track']['uri']
            track_duration_ms = track['track']['duration_ms']

            # Check if this is the shortest track
            if track_duration_ms < shortest_duration:
                shortest_duration = track_duration_ms
                shortest_track = track_uri

            # Collect track info for display
            track_duration_min = track_duration_ms // 60000
            track_duration_sec = (track_duration_ms // 1000) % 60
            tracks_info.append(f'{track_name} - {track_duration_min}:{track_duration_sec:02d}')
       
        tracks_html = '<br>'.join(tracks_info)
        
        if shortest_track:
            sp.start_playback(uris=[shortest_track])
            tracks_html += '<br><br>Playing the shortest song in the playlist'
                    
        return tracks_html
    else:
        return 'No playlist is currently playing.'

@app.route('/play_shortest')
def play_shortest():
    playback = sp.current_playback()

    if playback and playback['context'] and 'playlist' in playback['context']['type']:
        playlist_id = playback['context']['uri'].split(':')[-1]
        playlist = sp.playlist_tracks(playlist_id)
       
        shortest_track = None
        shortest_duration = float('inf')

        for track in playlist['items']:
            track_uri = track['track']['uri']
            track_duration_ms = track['track']['duration_ms']

            # Find the shortest track
            if track_duration_ms < shortest_duration:
                shortest_duration = track_duration_ms
                shortest_track = track_uri

        if shortest_track:
            sp.start_playback(uris=[shortest_track])
            return 'Now playing the shortest song in the playlist!'
   
    return 'No playlist is currently playing.'

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
