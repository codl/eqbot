import json
import urllib.request as ur
import urllib.parse as up

def ppTrack(t):
    return t['title'] + " by " + t['artist']['name'] + " (http://eqbeats.org/track/" + str(t['id']) + ")"

lastTrack = None
def newTracks():
    global lastTrack
    page = ur.urlopen("http://eqbeats.org/tracks/latest/json")
    tracks = json.loads(page.read().decode("UTF-8"))['tracks']
    newTracks = []
    if not lastTrack:
        lastTrack = tracks[0]['id']
    else:
        new = False
        for t in reversed(tracks):
            if new:
                lastTrack = t['id']
                newTracks += [t,]
            elif t['id'] == lastTrack:
                new = True
    return newTracks

def search(q):
    page = ur.urlopen("http://eqbeats.org/tracks/search/json?%s" % up.urlencode({'q': q}))
    tracks = json.loads(page.read().decode("UTF-8"))['tracks']
    return tracks
