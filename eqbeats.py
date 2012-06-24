import json
import urllib.request as ur
import urllib.parse as up
from urllib.error import HTTPError, URLError

def ppTrack(t):
    return t['title'] + " by " + t['artist']['name'] + " (http://eqbeats.org/track/" + str(t['id']) + ")"

seenTracks = []
def newTracks():
    global seenTracks
    newTracks = []
    try:
        page = ur.urlopen("http://eqbeats.org/tracks/latest/json")
        tracks = json.loads(page.read().decode("UTF-8"))
        if seenTracks == []:
            seenTracks = [t['id'] for t in tracks]
        for t in tracks:
            if t["id"] not in seenTracks:
                newTracks += [t,]
                seenTracks += [t['id'],]
            else:
                break
        seenTracks += newTracks
    except (HTTPError, URLError):
        return []
    return reversed(newTracks)

def search(q):
    page = ur.urlopen("http://eqbeats.org/tracks/search/json?%s" % up.urlencode({'q': q}))
    tracks = json.loads(page.read().decode("UTF-8"))
    return tracks

def random():
    page = ur.urlopen("http://eqbeats.org/tracks/random/json")
    tracks = json.loads(page.read().decode("UTF-8"))
    return tracks[0]
