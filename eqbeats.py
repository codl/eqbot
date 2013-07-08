import json
import urllib.request as ur
import urllib.parse as up
from urllib.error import HTTPError, URLError

def ppTrack(t, url=True):
    return t['title'] + " by " + t['artist']['name'] +\
        ((" https://eqbeats.org/track/" + str(t['id']) + "") if url else "")

seenTracks = []
def newTracks():
    global seenTracks
    newTracks = []
    try:
        page = ur.urlopen("https://eqbeats.org/tracks/latest/json")
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
    except (HTTPError, URLError, UnicodeDecodeError):
        return []
    return reversed(newTracks)

def search(q):
    page = ur.urlopen("https://eqbeats.org/tracks/search/json?%s" % up.urlencode({'q': q}))
    tracks = json.loads(page.read().decode("UTF-8"))
    return tracks

def featured(q):
    page = ur.urlopen("https://eqbeats.org/tracks/featured/json")
    tracks = json.loads(page.read().decode("UTF-8"))
    return tracks[0]

def track(id):
    try:
        page = ur.urlopen("https://eqbeats.org/track/%s/json" % (id,))
        track = json.loads(page.read().decode("UTF-8"))
        return track
    except (HTTPError, URLError, UnicodeDecodeError):
        return None

def random():
    page = ur.urlopen("https://eqbeats.org/tracks/random/json")
    tracks = json.loads(page.read().decode("UTF-8"))
    return tracks[0]
