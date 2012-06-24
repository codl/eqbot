#!/usr/bin/python3

import bot
import irc
import eqbeats
import random
import time
import re
import urllib.request as ur
import urllib.parse as up
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
import sys
import sqlite3
import os

i = irc.Irc("irc.ponychat.net")
i.setNick("EqBot_")
if len(sys.argv) > 1 and sys.argv[1] == "live":
    i.setNick("EqBot")
i.realname = "EqBot"
i.username = "eqbot"
i.connect()
b = bot.Bot(i)

b.lastTid = None

b.userlevel = {}
b.ops = ["codl", "fmang"]
OP = 1
def auth(user, bot = b):
    try:
        return bot.userlevel[user]
    except KeyError:
        bot.sendMsg("NickServ", "acc " + user.partition("!")[0] + " *")
        for e in bot.eventLoop():
            if e.type == irc.NOTICE and e.sourceNick == "NickServ":
                args = e.msg.split()
                if args[0] == user.partition("!")[0] and args[3] == "ACC":
                    _, _, account, _, level = args[:5]
                    if int(level) == 3 and account in bot.ops:
                        bot.userlevel[user] = OP
                    else:
                        bot.userlevel[user] = 0
                    break
        return bot.userlevel[user]

def preauth(e, bot):
    auth(e.source)
b.addJoinHook(preauth, 0)

def reauth(e, bot):
    try:
        del bot.userlevel[e.msg]
    except KeyError:
        pass
    time.sleep(0.5) # NickServ lags a bit
    auth(e.source)
b.addNickHook(reauth)

def clearauth(e, bot):
    try:
        del bot.userlevel[e.source]
    except KeyError:
        pass
b.addQuitHook(clearauth, 0)

def showauths(e, bot):
    if auth(e.source) == OP:
        for nick, level in bot.userlevel.items():
            bot.reply(e, nick + ": " + str(level), hilight=False)
b.addCommandHook("showauths", showauths, 0)

def clearauths(e, bot):
    bot.userlevel = {}
b.addCommandHook("clearauths", clearauths, 0)

def say(e, bot):
    if auth(e.source) == OP:
        words = e.msg.split()
        if len(words) < 3:
            bot.reply(e, "Usage : !say #channel message")
            bot.reply(e, "        !say nick message")
        else:
            bot.sendMsg(words[1], " ".join(words[2:]))
b.addCommandHook("say", say, 0)

def do(e, bot):
    if auth(e.source) == OP:
        words = e.msg.split()
        if len(words) < 3:
            bot.reply(e, "Usage : !do #channel action")
            bot.reply(e, "        !do nick action")
        else:
            bot.sendMsg(words[1], irc.action(" ".join(words[2:])))
b.addCommandHook("do", do, 0)

def nick(e, bot):
    if auth(e.source) == OP:
        words = e.msg.split()
        if len(words) < 2:
            bot.reply(e, "Usage : !nick newnick")
        else:
            bot.irc.setNick(words[1])
b.addCommandHook("nick", nick, 0)

def join(e, bot):
    if auth(e.source) == OP:
        words = e.msg.split()
        if len(words) < 2:
            bot.reply(e, "Usage : !join #channel [loudness]")
        elif len(words) == 2:
            bot.join(words[1])
        else:
            bot.join(words[1], int(words[2]))
b.addCommandHook("join", join, 0)

def part(e, bot):
    if auth(e.source) == OP:
        words = e.msg.split()
        if len(words) < 2:
            bot.reply(e, "Usage : !part #channel")
        else:
            bot.part(words[1])
b.addCommandHook("part", part, 0)

def channels(e, bot):
    if auth(e.source) == OP:
        for channel in bot.channels:
            bot.reply(e, str(channel), hilight=False)
b.addCommandHook("channels", channels, 0)


def fetchTitle(url):
    page = ur.urlopen(ur.Request(url, headers={'User-Agent': "Mozilla/5.0"}))
    enc = page.info().get("Content-Type").partition("=")[2]
    if enc == "": enc = "utf-8"
    try:
        return " ".join(HTMLParser.unescape(HTMLParser, re.search(b"<title>(.*?)</title>", page.read().translate(None,b"\n\r\t"), flags = re.I | re.M).expand(b"\\1").decode("utf-8")).split())
        #return HTMLParser.unescape(HTMLParser, re.search("<title>(.*)</title>", page.read().decode(enc), re.I).expand("\\1"))
    except (AttributeError, HTTPError, URLError):
        return None

def ping(e, bot):
    bot.reply(e, "pong")
b.addCommandHook("ping", ping, 10)

def aeiou(e, bot):
    if random.random() < 0.5:
        bot.reply(e, random.choice(("football!", "uuuuuuuuuu", "holla holla get $", "here comes another chinese earthquake ebrbrbrbrbrbrbrbrbrbrbrbrb", "99999999999999")), hilight=False)
b.addRegexHook("aeiou", aeiou, 90)
b.addRegexHook("john madden", aeiou, 90)

def hyphen(e, bot):
    bot.reply(e, "<" + e.sourceNick + "> " + re.sub("(\w)-(ass|flank) (\w)", "\\1 \\2-\\3", e.msg, flags=re.I), hilight=False)
b.addRegexHook("\w-(ass|flank) \w", hyphen, 90)

def plot(e, bot):
    words = e.msg.split(" ")
    swapped = False
    for i in range(len(words)): # how unpythonic D:
        if words[i] == "plot":
            words[i] = "intrigue"
            swapped = True
        elif words[i] == "PLOT":
            words[i] = "INTRIGUE"
            swapped = True
    if swapped: bot.reply(e, "<" + e.sourceNick + "> " + " ".join(words), hilight=False)
b.addRegexHook("plot", plot, 90)

def _search(e, bot, q):
    if not q == "":
        tracks = eqbeats.search(q)[:3]
        for t in tracks[:2]:
            bot.reply(e, eqbeats.ppTrack(t))
        if len(tracks) == 0:
            bot.reply(e, "no tracks found.")
        elif len(tracks) == 1:
            bot.lastTid = str(tracks[0]['id'])
        elif len(tracks) == 3:
            bot.reply(e, "and more at http://eqbeats.org/tracks/search?%s" % up.urlencode({'q': q}))

def regexsearch(e, bot):
    _search(e, bot, e.groups[0])
b.addRegexHook("^\?([^ \t].*)$", regexsearch, 90)

def cmdsearch(e, bot):
    _search(e, bot, " ".join(e.msg.split()[1:]))
b.addCommandHook("eqbsearch", cmdsearch, 30)
b.addCommandHook("eqsearch", cmdsearch, 30)

def flipcoin(e, bot):
    bot.reply(e, "tails" if random.random() < 0.5 else "heads")
b.addCommandHook("flipcoin", flipcoin)



flipmap = str.maketrans("!'(.∴<?‿⁅[_acbedgfihkjmnrtwvy{¡,)˙∵>¿⁀⁆]‾ɐɔqǝpƃɟıɥʞɾɯuɹʇʍʌʎ}", "¡,)˙∵>¿⁀⁆]‾ɐɔqǝpƃɟıɥʞɾɯuɹʇʍʌʎ}!'(.∴<?‿⁅[_acbedgfihkjmnrtwvy{")
def flip(e, bot):
    if len(e.args) == 0:
        e.reply(irc.action(random.choice((
            "flips a table (╯°□°)╯︵ ┻━┻",
            "flips a table (╯°□°)╯︵ ┻━┻",
            "flips a table ┻━┻ ︵╰(°□°╰)",
            "flips a table ┻━┻ ︵╰(°□°╰)",
            "flips some tables ┻━┻ ︵╰(°□°)╯︵ ┻━┻",
            "flips a chair (╯°□°)╯︵ =|_",
            "flips a chair _|= ︵╰(°□°╰)",
            "flips some chairs _|= ︵╰(°□°)╯︵ =|_"
            ))), hilight=False)
    elif e.args[0] == "table":
        e.reply(irc.action(random.choice((
            "flips a table (╯°□°)╯︵ ┻━┻",
            "flips a table ┻━┻ ︵╰(°□°╰)",
            ))), hilight=False)
    elif e.args[0] == "tables":
        e.reply(irc.action(
            "flips some tables ┻━┻ ︵╰(°□°)╯︵ ┻━┻"
            ), hilight=False)
    elif e.args[0] == "chair":
        e.reply(irc.action(random.choice((
            "flips a chair (╯°□°)╯︵ =|_",
            "flips a chair _|= ︵╰(°□°╰)",
            ))), hilight=False)
    elif e.args[0] == "chairs":
        e.reply(irc.action(
            "flips some chairs _|= ︵╰(°□°)╯︵ =|_"
            ), hilight=False)
    else:
        flipped = list(" ".join(e.args).lower().translate(flipmap))
        flipped.reverse()
        flipped = "".join(flipped)
        e.reply(irc.action(
            "flips " +
            ("an" if e.args[0][0] in "aeiouAEIOU" else "a") + " " +
            " ".join(e.args) + " " +
            "(╯°□°)╯︵ " + flipped
            ), hilight=False)
b.addCommandHook("flip", flip, 70)

def choice(e, bot):
    choices = e.msg.split(" or ")
    choices[0] = " ".join(choices[0].split(" ")[1:])
    if len(choices) == 1:
        choices = e.msg.split()[1:]
    if any(pony in choices for pony in ("ponies", "PONIES", "pony", "PONY", "pone", "PONE", "poni", "PONI", "mlp", "MLP")):
        bot.reply(e, b"\02Ponies, obviously.")
    elif len(choices) <= 1:
        bot.reply(e, "Not much of a choice, eh?")
    else:
        bot.reply(e, random.choice(choices))
b.addCommandHook("choice", choice, 90)
b.addCommandHook("choose", choice, 90)

def newTracks(bot):
    for t in eqbeats.newTracks():
        for c in bot.channels:
            if c.level > 90:
                bot.sendMsg(c.name, "New track: " + eqbeats.ppTrack(t))
        bot.lastTid = str(t['id'])
    return 120
b.addTimeHook(3, newTracks)

def once(bot):
    bot.sendMsg("#eqbeats", random.choice(("untz", "once")))
    return random.randint(60, 86400)
b.addTimeHook(random.randint(60, 86400), once)

def roll(e, bot):
    total = 0
    msg = "Rolling "
    dice = e.msg.split()[1:]
    totaldice = 0
    for die in dice:
        try:
            spec = re.match("(\\d+)?d(\\d+)", die, re.I).groups("1")
            num, sides = int(spec[0]), int(spec[1])
            if num == 0:
                continue
            msg += str(num) + " " + str(sides) + "-sided di" + ("ce" if num > 1 else "e") + ":"
            for i in range(num):
                res = random.randint(1, sides)
                msg += " " + str(res)
                total += res
                totaldice+=1
            bot.reply(e, msg)
            msg = "        "
        except LookupError:
            pass
    if totaldice == 0:
        bot.reply(e, "Rolling nothing. Total : 0")
    if totaldice > 1:
        bot.reply(e, "Total: " + str(total))
b.addCommandHook("roll", roll, 50)

def rejoice(e, bot):
    bot.reply(e, "yay", hilight=False)
b.addCommandHook("rejoice", rejoice, 50)
b.addCommandHook("cheer", rejoice, 50)

def louder(e, bot):
    bot.reply(e, b"\002yay", hilight=False)
b.addCommandHook("louder", louder, 50)

def louder_(e, bot):
    bot.reply(e, b"\002Yay!", hilight=False)
b.addCommandHook("louder!", louder_, 50)

def kindness(e, bot):
    if(e.type == irc.ACTION and re.search("(hugs|snuggles|pets|brohoofs|pats) " + i.nick, e.msg, re.I)):
        bot.reply(e, "<3")
b.addWildHook(kindness, 30)

def violence(e, bot): # never the answer
    if(e.type == irc.ACTION and re.search("(hits|kicks|slaps|punches|crushes|maims|harms|shoots|stabs) " + i.nick, e.msg, re.I)):
        if e.channel == "#eqbeats" and random.random() < 0.1:
            bot.reply(e, "You thought you could abuse old EqBot, that pushover. Well, new EqBot is not going to have any of that!", hilight=False)
            time.sleep(0.5)
            bot.reply(e, "!kick " + e.sourceNick, hilight=False)
        else:
            bot.reply(e, random.choice((
                "Ow!",
                "Stop that!",
                "HALP!",
                ":(",
                "You broke my " + bodypart() + "!",
                "I don't like you. :(",
                irc.action("cries"),
                irc.action("flails"),
                irc.action("whimpers"),
                irc.action("whines"),
                irc.action("flees"))
            ), hilight=False)
b.addWildHook(violence, 30)

def lr(): return random.choice(("left", "right"))
def fb(): return random.choice(("front", "back"))
def bodypart():
    return random.choice(("head", "CPU", "spring-loaded boots", lr()+" ear", fb()+" "+lr()+" hoof", "butt", "hard drive", "sarcasm processing unit", "embedded duct tape dispenser", "eyes", "VGA port", "framebuffer", "33.6k modem", "cathode tube", "random number generator", "top hat", "keyboard", "skynet transmitter", "magical girl stick thing", "sticker collection", "\"take over the world\" processor", "arp generator", "!poem factory", "antenna", "teleporter", "portable hole", "ice cream machine", "floppy drive", "screwdriver", "heart"))
def adjective():
    return random.choice((
        ("a", "paltry"),
        ("a", "paltry"),
        ("a", "paltry"),
        ("a", "snappy"),
        ("a", "raging"),
        ("an", "inappropriate"),
        ("an", "awesome"),
        ("a", "clumsy"),
        ("an", "awkward"),
        ("a", "dynamic"),
        ("a", "world-breaking"),
        ("an", "impossible"),
        ("an", "uncanny"),
        ("an", "31337"),
        ("a", "silly"),
        ("a", "bad"),
        ("a", "timey wimey"),
        ("a", "ridiculous"),
        ("a", "technologic"),
        ("a", "paranormal"),
        ("a", "radical"),
        ("a", "bitchin'"),
        ("a", "cool"),
        ("a", "fabulous"),
        ("a", "delicious"),
        ("a", "rambuctious"),
        ("a", "nerve-wracking"),
        ("a", "special"),
        ("a", "tubular"),
        ("a", "gnarly"),
        ("a", "three dimensional"),
        ("a", "cockin'"),
        ("a", "fly"),
        ("a", "sharp"),
        ("a", "slow"),
        ("a", "demented"),
        ("an", "insane"),
        ("an", "uncouth"),
        ("a", "crude"),
        ("an", "entrancing"),
        ("a", "blinding"),
        ("a", "dumb"),
        ("a", "captivating"),
        ("a", "mesmerizing"),
        ("an", "horizontal"),
        ("a", "generic"),
        ("a", "genetically enhanced"),
        ("a", "blue"),
        ("a", "scrappy"),
        ("a", "scruffy"),
        ("a", "dapper"),
        ("an", "exquisite"),
        ("a", "smooth"),
        ("an", "extravagant"),
        ("a", "red"),
        ("a", "flaming"),
        ("a", "flamboyant"),
        ("a", "sweet"),
        ("an", "herbal"),
        ("a", "candid"),
        ("an", "extravagant"),
        ("a", "horsey"),
        ("a", "musical"),
        ("a", "misspeled"),
        ("a", "luxurious"),
        ("a", "puzzling"),
        ("a", "raw"),
        ("a", "deadly"),
        ("a", "god damned"),
        ("a", "motherfucking"),
        ("a", "lovable"),
        ("a", "toxic"),
        ("a", "classic"),
        ("a", "grilled cheese"),
        ("a", "racist"),
        ("a", "tiny"),
        ("a", "stupid"),
        ("a", "colorful")
    ))

b.bfcounter = 0
b.bflast = 0
def backflip(e, bot):
    if bot.bfcounter < 12:
        bot.reply(e, irc.action("does "+" ".join(adjective())+" backflip and lands on its "+bodypart()), hilight=False)
        bot.bflast = time.time()
        bot.bfcounter += 1
        if bot.bflast + 60 < time.time():
            bot.bfcounter = 1
    elif bot.bfcounter == 12:
        bot.bfcounter = 13
        bot.reply(e, irc.action("is too tired to backflip right now"), hilight=False)
        time.sleep(60)
        bot.bfcounter = 0
b.addCommandHook("backflip", backflip, 30)

def rfchelp(e, bot):
    bot.reply(e, "Syntax : rfc?ID")
b.addCommandHook("rfc", rfchelp, 30)

def rfc(e, bot):
    url = "https://tools.ietf.org/html/rfc" + e.groups[0]
    title = fetchTitle(url)
    if not title:
        bot.reply(e, "No such RFC standard.")
        return
    bot.reply(e, title + " " + url)
b.addRegexHook("rfc\?([0-9]+)", rfc, 30)

def url(e, bot):
    title = fetchTitle(e.groups[0])
    if title:
        bot.reply(e, b"\02" + title.encode("utf_8") + b"\2 posted by " + e.sourceNick.encode("utf_8"), hilight=False)
b.addRegexHook("(https?://[^ ]*)", url, 90)

def getdb():
    return sqlite3.connect("db")

def checkMail(e, bot):
    nick = e.msg if e.type == irc.NICK else e.sourceNick
    db = getdb()
    c = db.cursor()
    c.execute("SELECT source, msg, private FROM mail WHERE dest = ?", (nick,))
    messages = c.fetchall()
    c.execute("DELETE FROM mail WHERE dest = ?", (nick,))
    db.commit()
    for m in messages:
        msg = "Mail from " + m[0] + ": " + m[1]
        if m[2] or not e.channel:
            bot.sendMsg(nick, msg)
        else:
            bot.reply(e, msg)
b.addMsgHook(checkMail, 90)
b.addJoinHook(checkMail, 90)

def mail(e, bot):
    db = getdb()
    c = db.cursor()
    args = e.msg.split()
    if len(args) < 3:
        bot.reply(e, "Syntax : !mail nick message")
        return
    nick = args[1]
    msg = " ".join(args[2:])
    private = (e.channel == None)
    c.execute("INSERT INTO mail (source, dest, private, msg) VALUES (?, ?, ?, ?)", (e.sourceNick, nick, private, msg))
    db.commit()
    bot.reply(e, "Message stored!")
b.addCommandHook("mail", mail, 90)
b.addCommandHook("msg", mail, 90)
b.addCommandHook("m", mail, 90)

def mailbag(e, bot):
    db = getdb()
    c = db.cursor()
    if auth(e.source) == OP:
        c.execute("SELECT dest FROM mail GROUP BY dest;")
        rows = c.fetchall()
        e.reply("I have mail for : " + ("nopony" if len(rows) == 0 else " ".join(row[0] for row in rows)))
b.addCommandHook("mailbag", mailbag, 0)

lastmsgs = {}
def s_pre(e, bot):
    if e.type == irc.MSG and not re.search("^s(?P<delim>[^ \tA-Za-z]).*(?P=delim)", e.msg, flags=re.I):
        if e.channel:
            lastmsgs[e.channel] = "<" + e.sourceNick + "> " + e.msg
        else:
            lastmsgs[e.sourceNick] = "<" + e.sourceNick + "> " + e.msg
b.addWildHook(s_pre, 0)

def s(e, bot):
    try:
        if e.type == irc.MSG:
            if e.channel: source = e.channel
            else: source = e.sourceNick
            args = e.msg.split(e.msg[1])
            if len(args) >= 3:
                msg = re.sub(args[1], args[2], lastmsgs[source])
                lastmsgs[source] = msg
                bot.reply(e, msg, hilight=False)
    except KeyError:
        pass
b.addRegexHook("^s(?P<delim>[^ \tA-Za-z]).*(?P=delim)", s, 70)

def rand_track(e, bot):
    bot.reply(e, eqbeats.ppTrack(eqbeats.random()))
b.addCommandHook("random", rand_track, 90)
b.addCommandHook("rand", rand_track, 90)

def store_words(e, bot):
    if e.type == irc.MSG:
        db = getdb()
        c = db.cursor()
        words = e.msg.split()
        for i in range(1, len(words)):
            c.execute("INSERT INTO word_pairs (first, second) VALUES (?, ?)", (words[i-1], words[i]))
        for i in range(2, len(words)):
            c.execute("INSERT INTO word_triplets (first, second, third) VALUES (?, ?, ?)", (words[i-2], words[i-1], words[i]))
        if len(words) > 1:
            c.execute("INSERT INTO word_pairs (second) VALUES (?)", (words[0],))
            c.execute("INSERT INTO word_pairs (first) VALUES (?)", (words[-1],))
            c.execute("INSERT INTO word_triplets (second, third) VALUES (?,?)", (words[0], words[1]))
            c.execute("INSERT INTO word_triplets (first, second) VALUES (?,?)", (words[-2], words[-1]))
        db.commit()
b.addWildHook(store_words, 0)

def poemm(e, bot):
    db = getdb()
    c = db.cursor()
    words = []
    wordcount = 0
    if len(e.msg.split()) > 1:
        fromscratch = False
        words = e.msg.split()[1:]
        if len(words) < 2:
            c.execute("SELECT second FROM word_pairs WHERE first LIKE ? ORDER BY random() LIMIT 1", (words[-1],))
            word = c.fetchone()
            if word:
                wordcount += 1
                words.append(word[0])
            else:
                words.append(None)
    else:
        fromscratch = True
        c.execute("SELECT second, third FROM word_triplets WHERE first IS NULL ORDER BY random() LIMIT 1")
        row = c.fetchone()
        if row:
            words = [row[0], row[1]]
    while words[-1] != None:
        if random.random() > 0.5:
            c.execute("SELECT third FROM word_triplets WHERE first LIKE ? AND second LIKE ? AND third NOT NULL ORDER BY random() LIMIT 1", (words[-2], words[-1]))
            word = c.fetchone()
            if word:
                wordcount += 2
                words.append(word[0])
            else:
                break
        else:
            c.execute("SELECT second, third FROM word_triplets WHERE first LIKE ? ORDER BY random() LIMIT 1", (words[-1],))
            triplet = c.fetchone()
            if triplet:
                wordcount += 2
                words.append(triplet[0])
                words.append(triplet[1])
            else: break
    if wordcount == 0:
        if fromscratch and random.random() > .5:
            poemm(e, bot)
        else:
            bot.reply(e, "I'm out of inspiration, sorry.", hilight=False)
    else:
        if words[-1] == None: words = words[:-1]
        msg = " ".join(words)
        bot.reply(e, msg, hilight=False)
        if e.channel:
            lastmsgs[e.channel] = "<" + i.nick + "> " + msg
b.addCommandHook("chain", poemm)
b.addCommandHook("poem", poemm)

def dundundun(e, bot):
    bot.reply(e, "DUN DUN DUUUN", hilight=False)
b.addRegexHook("or[\. ]+(is|am|are|was|were|will|do|does|did|can|could|should|shall)[\. ]+(I|he|she|it|you|they|we)[ ?!]*$", dundundun, 70)

def batman(e, bot):
    bot.reply(e, "I'm the " + adjective()[1] + " Batman.", hilight=False)
b.addCommandHook("batman", batman)

def technothing(r=-1):
    r += 1
    if random.random() - r/10.0 > .4:
        return random.choice((
            technothing(r) + " detector",
            technothing(r) + " provider",
            technothing(r) + " scrambler",
            "streaming " + technothing(r),
            technothing(r) + " to " + technothing(r) + " adapter",
            "USB " + technothing(r),
            "internet " + technothing(r),
            "web" + technothing(r),
            "net" + technothing(r),
            "femto" + technothing(r),
            "techno" + technothing(r),
            "virtual " + technothing(r),
            "automated " + technothing(r),
            technothing(r) + " generator",
            technothing(r) + " " + technothing(r),
        ))
    else:
        return random.choice((
            "pony",
            "HTML5",
            "waveform",
            "log",
            "feet warmer",
            "video camera",
            "browser",
            "OS",
            "socket",
            "player",
            "screen",
            "database",
            "video",
            "VGA",
            "sound",
            "internet",
            "network",
            "RSS",
            "time",
            "cookies",
            "text processor",
            "encoding",
            "XML",
            "CSS3",
            "gopher",
            "computer",
            "keyboard",
            "mouse",
            "audio",
            "screen",
            "sims",
            "port",
            "memory",
            "cell",
            "youtube",
            "facebook",
            "twitter",
            "tumblr",
            "email"
        ))

def technoverb():
    return random.choice((
        "replace",
        "reconfigure",
        "calibrate",
        "bypass",
        "jailbreak",
        "unlock",
        "delete",
        "process",
        "decrypt",
        "encode",
        "unset",
        "ignore",
        "mangle",
        "relocate",
        "probe",
        "fork",
        "thread",
        "undo",
        "overwrite"
    ))

def techsupport(e, bot):
    bot.reply(e, random.choice((
        "Try to " + technoverb() + " your " + technothing() +".",
        "You could probably " + technoverb() + " the " + technothing()+".",
        "You could probably " + technoverb() + " the " + technothing()+".",
        "I think your best bet would be to " + technoverb() + " your " + technothing()+".",
        "It may fix it if you " + technoverb() + " the " + technothing() + ".",
        "Does anything happen if you " + technoverb() + " the " + technothing() + "?",
        "Don't ever " + technoverb() + " the " + technothing() + ". Things will break.",
        "Just " + technoverb() + " your " + technothing() + ". It always works."
        )))
b.addCommandHook("techsupport", techsupport)

def feature(e, bot):
    if auth(e.source) == OP:
        tids = e.msg.split()[1:]
        if len(tids) == 0 and bot.lastTid:
            print(bot.lastTid)
            tids = (bot.lastTid,)
        for tid in tids:
            try:
                int(tid)
                bot.reply(e, os.popen("sudo -u eqbeats-pub EQBEATS_DIR=/srv/eqbeats/ /srv/eqbeats/tools/fqueue " + tid + " 2>&1").read())
                #bot.reply(e, os.popen("echo " + tid).read())
            except (TypeError, ValueError):
                break
b.addCommandHook("feature", feature, 0)
b.addCommandHook("fqueue", feature, 0)

def inc(var):
    db = getdb()
    c = db.cursor()
    c.execute("SELECT 1 FROM variables WHERE name LIKE ?", (var,))
    if c.fetchone():
        c.execute("UPDATE variables SET value = value + 1 WHERE name LIKE ?", (var,))
    else:
        c.execute("INSERT INTO variables (name, value) VALUES (?,  1)", (var,))
    db.commit()

def dec(var):
    db = getdb()
    c = db.cursor()
    c.execute("SELECT 1 FROM variables WHERE name LIKE ?", (var,))
    if c.fetchone():
        c.execute("UPDATE variables SET value = value - 1 WHERE name LIKE ?", (var,))
    else:
        c.execute("INSERT INTO variables (name, value) VALUES (?, -1)", (var,))
    db.commit()

def incdec(e, bot):
    incs = re.findall("[^ \\t]+\\+\\+", e.msg)
    decs = re.findall("[^ \\t]+--", e.msg)
    for var in incs:
        var = var[:-2]
        inc(var)
    for var in decs:
        var = var[:-2]
        dec(var)
b.addRegexHook(".*?[^ \\t](?:\\+|-){2}", incdec, 0)

def getvalue(e, bot):
    variables = re.findall("[^ \\t]+==", e.msg)
    db = getdb()
    c = db.cursor()
    for var in variables:
        var = var[:-2]
        c.execute("SELECT name, value FROM variables WHERE name LIKE ?", (var,))
        row = c.fetchone()
        if row:
            var = row[0]
            val = str(row[1])
        else:
            val = "0"
        msg = "Karma for "+var+" : "+val
        bot.reply(e, msg, hilight=False)
b.addRegexHook("[^ \\t]==", getvalue, 90)

def sadtrombone(e, bot):
    bot.reply(e, "http://www.sadtrombone.com/", hilight=False)
b.addCommandHook("sadtrombone", sadtrombone, 70)

def stalk_track(e, bot):
    db = getdb()
    c = db.cursor()
    c.execute("SELECT 1 FROM nick_host WHERE nick = ? AND host = ?", (e.sourceNick, e.host))
    if c.fetchone():
        c.execute("UPDATE nick_host SET count = count +1 WHERE nick = ? AND host = ?", (e.sourceNick, e.host))
    else:
        c.execute("INSERT INTO nick_host (nick, host) VALUES (?, ?)", (e.sourceNick, e.host))
    db.commit()
b.addMsgHook(stalk_track)
b.addJoinHook(stalk_track)
b.addNickHook(stalk_track)

def stalk(e, bot):
    if len(e.args) == 0:
        e.reply("usage : "+e.msg+" <nick>")
    else:
        db = getdb()
        c = db.cursor()
        host = bot.whois(e.args[0]).host
        nicks = {e.args[0]: 1}
        hosts = {}
        if host:
            hosts[host] = 1
        print(hosts)
        for _ in range(3):
            for host in hosts.keys():
                c.execute("SELECT nick, count FROM nick_host WHERE host = ?", (host,))
                for nick, count in c:
                    try:
                        nicks[nick] = nicks[nick] + hosts[host] * count
                    except KeyError:
                        nicks[nick] = count
            for nick in nicks.keys():
                c.execute("SELECT host, count FROM nick_host WHERE nick = ?", (nick,))
                for host, count in c:
                    try:
                        hosts[host] = hosts[host] + nicks[nick] * count
                    except KeyError:
                        hosts[host] = count
            print(nicks)
            print(hosts)
        topnicks = []
        maxcount = 0
        for nick, count in nicks.items():
            if nick != e.args[0] and count > maxcount:
                topnicks.append(nick)
                maxcount = count
        topnicks.reverse()
        if len(topnicks) == 0:
            e.reply(e.args[0] + " is a mystery best left unsolved")
        else:
            e.reply(e.args[0] + " might be "+ " or ".join(topnicks[:2]) + ", but who knows really?")
b.addCommandHook("stalk", stalk, 70)

def backflop(e, bot):
    e.reply(irc.action("flops around on its back"), hilight=False)
b.addCommandHook("backflop", backflop)

time.sleep(2)
i.sendMsg("NickServ", "IDENTIFY FnkrfBPo9f-X")
i.setMode("-x")
if len(sys.argv) > 1 and sys.argv[1] == "live":
    b.join("#eqbeats", 100)
    b.join("#bronymusic", 70)
b.run()
