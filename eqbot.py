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
import json
import os
import threading
import pickle

LIVE = False

i = irc.Irc("irc.ponychat.net")
i.setNick("EqB0t")
if len(sys.argv) > 1 and sys.argv[1] == "live":
    i.setNick("EqBot")
    LIVE = True
i.realname = "EqBot"
i.username = "EqBot"
i.connect()
b = bot.Bot(i)

b.lastTid = None

b.ignore = ["DIVINE_JUDGEMENT", "Seraphim"]

b.userlevel = {}
b.acc = {}
b.ops = ["codl"]
b.hops = ["fmang", "Kipje", "sci", "Valodim", "djazz"]
HOP = 1
OP = 2
def fetchacc(user, bot = b):
    bot.sendMsg("NickServ", "acc " + user.partition("!")[0] + " *")
    for e in bot.eventLoop():
        if e.type == irc.NOTICE and e.sourceNick == "NickServ":
            args = e.msg.split()
            if args[0] == user.partition("!")[0] and args[3] == "ACC":
                _, _, account, _, level = args[:5]
                bot.acc[user] = account
                bot.userlevel[user] = 0
                if int(level) == 3:
                    if account in bot.ops:
                        bot.userlevel[user] = OP
                    if account in bot.hops:
                        bot.userlevel[user] = HOP
                break
def acc(user, bot = b):
    try:
        return bot.acc[user]
    except KeyError:
        fetchacc(user, bot)
        return bot.acc[user]

def auth(user, bot = b):
    try:
        return bot.userlevel[user]
    except KeyError:
        fetchacc(user, bot)
        return bot.userlevel[user]

def nick_clearauth(e, bot):
    try:
        del bot.userlevel[e.msg + "!" + e.source.partition("!")[2]]
        del bot.acc[e.msg + "!" + e.source.partition("!")[2]]
    except KeyError:
        pass
b.addNickHook(nick_clearauth)

def clearauth(e, bot):
    try:
        del bot.userlevel[e.source]
        del bot.acc[e.source]
    except KeyError:
        pass
b.addQuitHook(clearauth, 0)

def debug_auths(e, bot):
    if auth(e.source) == OP:
        for nick, level in bot.userlevel.items():
            bot.reply(e, nick + ": " + str(level))
b.addCommandHook("auths", debug_auths, 0)

def clearauths(e, bot):
    bot.userlevel = {}
b.addCommandHook("clearauths", clearauths, 0)

def say(e, bot):
    words = e.msg.split()
    if len(words) < 3:
        bot.reply(e, "Usage : !say #channel message")
        if auth(e.source) >= HOP:
            bot.reply(e, "        !say nick message")
        return
    if auth(e.source) >= HOP or e.args[0][0] in "#&":
        if words[1].lower() == "chanserv" and words[2].lower() == "kick" and words[3].lower() == "#eqbeats":
            e.reply("Do it yourself.")
        else:
            bot.sendMsg(words[1], " ".join(words[2:]))
b.addCommandHook("say", say, 100)

def do(e, bot):
    words = e.msg.split()
    if len(words) < 3:
        bot.reply(e, "Usage : !do #channel action")
        if auth(e.source) >= HOP:
            bot.reply(e, "        !do nick action")
        return
    if auth(e.source) >= HOP or e.args[0][0] in "#&":
        bot.sendMsg(words[1], irc.action(" ".join(words[2:])))
b.addCommandHook("do", do, 100)

def nick(e, bot):
    if auth(e.source) >= HOP:
        words = e.msg.split()
        if len(words) < 2:
            bot.reply(e, "Usage : !nick newnick")
        else:
            bot.irc.setNick(words[1])
b.addCommandHook("nick", nick, 0)

def join(e, bot):
    if auth(e.source) >= HOP:
        words = e.msg.split()
        if len(words) < 2:
            bot.reply(e, "Usage : !join #channel [loudness]")
        elif len(words) == 2:
            bot.join(words[1])
        else:
            bot.join(words[1], int(words[2]))
b.addCommandHook("join", join, 0)

def part(e, bot):
    if auth(e.source) >= HOP:
        words = e.msg.split()
        if len(words) < 2:
            bot.reply(e, "Usage : !part #channel")
        else:
            bot.part(words[1])
b.addCommandHook("part", part, 0)

def channels(e, bot):
    if auth(e.source) >= HOP:
        for channel in bot.channels:
            bot.reply(e, str(channel))
b.addCommandHook("channels", channels, 0)


def fetchTitle(url):
    page = ur.urlopen(ur.Request(url, data=None,
        headers={'User-Agent': "Mozilla/5.0 Python-urllib/2.6 EqBot"}))
    enc = page.info().get("Content-Type").partition("=")[2]
    if enc == "": enc = "utf-8"
    try:
        return " ".join(HTMLParser.unescape(HTMLParser, re.search(b"<title>(.*?)</title>", page.read(10000).translate(None,b"\n\r\t"), flags = re.I | re.M).expand(b"\\1").decode("utf-8")).split())
    except (AttributeError, HTTPError, URLError):
        return None

def ping(e, bot):
    bot.reply(e, "pong")
b.addCommandHook("ping", ping, 10)

def aeiou(e, bot):
    if random.random() < 0.5:
        bot.reply(e, random.choice(("football!", "uuuuuuuuuu", "holla holla get $", "here comes another chinese earthquake ebrbrbrbrbrbrbrbrbrbrbrbrb", "99999999999999")))
b.addRegexHook("aeiou", aeiou, 90)
b.addRegexHook("john madden", aeiou, 70)

def hyphen(e, bot):
    bot.reply(e, "<" + e.sourceNick + "> " + re.sub("(\w)-(ass|flank) (\w)", "\\1 \\2-\\3", e.msg, flags=re.I))
b.addRegexHook("\w-(ass|flank) \w", hyphen, 70)

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
    if swapped: bot.reply(e, "<" + e.sourceNick + "> " + " ".join(words))
b.addRegexHook("plot", plot, 90)

def lightsaber(e, bot):
    words = e.msg.split(" ")
    swapped = False
    for i in range(len(words)):
        if words[i] in ("VIBRATOR", "DILDO"):
            words[i] = "LIGHTSABER"
            swapped = True
        elif words[i] in ("VIBRATORS", "DILDOS"):
            words[i] = "LIGHTSABERS"
            swapped = True
        elif words[i].lower() in ("vibrator", "dildo"):
            words[i] = "lightsaber"
            swapped = True
        elif words[i].lower() in ("vibrators", "dildos"):
            words[i] = "lightsabers"
            swapped = True
    if swapped: bot.reply(e, "<" + e.sourceNick + "> " + " ".join(words))
b.addRegexHook("dildo|vibrator", lightsaber, 70)

def _search(e, bot, q):
    try:
        id = int(q)
        t = eqbeats.track(id)
        if t:
            e.reply(eqbeats.ppTrack(t))
            bot.lastTid = str(id)
            return
        else:
            e.reply("No tracks found.")
    except ValueError:
        if not q == "":
            tracks = eqbeats.search(q)[:3]
            for t in tracks[:2]:
                bot.reply(e, eqbeats.ppTrack(t))
            if len(tracks) == 0:
                bot.reply(e, "No tracks found.")
            elif len(tracks) == 1:
                bot.lastTid = str(tracks[0]['id'])
            elif len(tracks) == 3:
                bot.reply(e, "and more at https://eqbeats.org/tracks/search?%s" % up.urlencode({'q': q}))

def regexsearch(e, bot):
    _search(e, bot, e.groups[0])
b.addRegexHook("^\?([^ \t!?].*)$", regexsearch, 90)

def cmdsearch(e, bot):
    _search(e, bot, " ".join(e.msg.split()[1:]))
b.addCommandHook("eqsearch", cmdsearch, 30)

def flipcoin(e, bot):
    bot.reply(e, "tails" if random.random() < 0.5 else "heads")
b.addCommandHook("flipcoin", flipcoin)


flipmap = str.maketrans("!'(.∴<?‿⁅[_acbedgfihkjmnrtwvy{¡,)˙∵>¿⁀⁆]‾ɐɔqǝpƃɟıɥʞɾɯuɹʇʍʌʎ}lן697Ɫᔭ43Ɛ¯ɓ/⁄\\", 
        "¡,)˙∵>¿⁀⁆]‾ɐɔqǝpƃɟıɥʞɾɯuɹʇʍʌʎ}!'(.∴<?‿⁅[_acbedgfihkjmnrtwvy{ןl96Ɫ74ᔭƐ3_g\\\\/")
def flip(e, bot, flip="flip"):
    if len(e.args) == 0:
        e.reply(irc.action(random.choice((
            flip + "s a table (╯°□°)╯︵ ┻━┻",
            flip + "s a table (╯°□°)╯︵ ┻━┻",
            flip + "s a table ┻━┻ ︵╰(°□°╰)",
            flip + "s a table ┻━┻ ︵╰(°□°╰)",
            flip + "s some tables ┻━┻ ︵╰(°□°)╯︵ ┻━┻",
            flip + "s a chair (╯°□°)╯︵ =|_",
            flip + "s a chair _|= ︵╰(°□°╰)",
            flip + "s some chairs _|= ︵╰(°□°)╯︵ =|_"
            ))))
    elif e.args[0] == "table":
        e.reply(irc.action(random.choice((
            flip + "s a table (╯°□°)╯︵ ┻━┻",
            flip + "s a table ┻━┻ ︵╰(°□°╰)",
            ))))
    elif e.args[0] == "tables":
        e.reply(irc.action(
            flip + "s some tables ┻━┻ ︵╰(°□°)╯︵ ┻━┻"
            ))
    elif e.args[0] == "chair":
        e.reply(irc.action(random.choice((
            flip + "s a chair (╯°□°)╯︵ =|_",
            flip + "s a chair _|= ︵╰(°□°╰)",
            ))))
    elif e.args[0] == "chairs":
        e.reply(irc.action(
            flip + "s some chairs _|= ︵╰(°□°)╯︵ =|_"
            ))
    elif e.args[0] == "back":
        if flip == "flop":
            backflop(e, bot)
        else:
            backflip(e, bot)
    else:
        flipped = list(" ".join(e.args).lower().translate(flipmap))
        flipped.reverse()
        flipped = "".join(flipped)
        e.reply(irc.action(
            flip + "s " +
            ("an" if e.args[0][0] in "aeiouAEIOU" else "a") + " " +
            " ".join(e.args) + " " +
            "(╯°□°)╯︵ " + flipped
            ))
b.addCommandHook("flip", flip, 70)

def flop(e, bot):
    flip(e, bot, "flop")
b.addCommandHook("flop", flop, 70)

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
            if c.level >= 90:
                bot.sendMsg(c.name, "New track: " + eqbeats.ppTrack(t))
        bot.lastTid = str(t['id'])
    return 120
b.addTimeHook(3, newTracks)

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
            if sides >= 100:
                e.reply("That die is way too big. How do you expect me to even lift it?")
                return
            msg += str(num) + " " + str(sides) + "-sided di" + ("ce" if num > 1 else "e") + ":"
            for i in range(num):
                res = random.randint(1, sides)
                msg += " " + str(res)
                total += res
                totaldice+=1
                if totaldice >= 100:
                    e.reply("Rolling a few handfuls of dice: Total: a few millions, maybe more")
                    return
            bot.reply(e, msg)
            msg = "        " # for alignment
        except LookupError:
            pass
    if totaldice > 1:
        bot.reply(e, "Total: " + str(total))
b.addCommandHook("roll", roll, 50)

def rejoice(e, bot):
    bot.reply(e, "yay")
b.addCommandHook("rejoice", rejoice, 50)
b.addCommandHook("cheer", rejoice, 50)

def louder(e, bot):
    bot.reply(e, b"\002yay")
b.addCommandHook("louder", louder, 50)

def louder_(e, bot):
    bot.reply(e, b"\002Yay!")
b.addCommandHook("louder!", louder_, 50)

def kindness(e, bot):
    if(e.type == irc.ACTION and re.search("(hugs|snuggles|pets|brohoofs|pats) " + i.nick, e.msg, re.I)):
        bot.reply(e, "<3")
b.addWildHook(kindness, 30)

def violence(e, bot): # never the answer
    if(e.type == irc.ACTION and re.search("(hits|kicks|slaps|punches|crushes|maims|harms|shoots|stabs) " + i.nick, e.msg, re.I)):
        if e.channel == "#eqbeats" and random.random() < 0.1:
            bot.reply(e, "You thought you could abuse old EqBot, that pushover. Well, new EqBot is not going to have any of that!")
            time.sleep(0.5)
            bot.sendMsg("ChanServ", "kick #eqbeats " + e.sourceNick)
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
            ))
b.addWildHook(violence, 30)

def lr(): return random.choice(("left", "right"))
def fb(): return random.choice(("front", "back"))
def bodypart():
    return random.choice(("head", "CPU", "spring-loaded boots", lr()+" ear", fb()+" "+lr()+" hoof", "butt", "hard drive", "sarcasm processing unit", "embedded duct tape dispenser", "eyes", "VGA port", "framebuffer", "33.6k modem", "cathode tube", "random number generator", "top hat", "keyboard", "skynet transmitter", "magical girl stick thing", "sticker collection", "\"take over the world\" processor", "arp generator", "!poem factory", "antenna", "teleporter", "portable hole", "ice cream machine", "floppy drive", "screwdriver", "heart"))
def adjective():
    return random.choice((
        ("a", "bad"),
        ("a", "bitchin'"),
        ("a", "blinding"),
        ("a", "blue"),
        ("a", "candid"),
        ("a", "captivating"),
        ("a", "classic"),
        ("a", "clumsy"),
        ("a", "cockin'"),
        ("a", "colorful"),
        ("a", "cool"),
        ("a", "crude"),
        ("a", "dapper"),
        ("a", "deadly"),
        ("a", "delicious"),
        ("a", "demented"),
        ("a", "dumb"),
        ("a", "dynamic"),
        ("a", "fabulous"),
        ("a", "flamboyant"),
        ("a", "flaming"),
        ("a", "fly"),
        ("a", "generic"),
        ("a", "genetically enhanced"),
        ("a", "gnarly"),
        ("a", "god damned"),
        ("a", "grilled cheese"),
        ("a", "heartrending"),
        ("a", "horsey"),
        ("a", "lovable"),
        ("a", "luxurious"),
        ("a", "mesmerizing"),
        ("a", "misspeled"),
        ("a", "motherfucking"),
        ("a", "musical"),
        ("a", "nerve-wracking"),
        ("a", "paltry"),
        ("a", "paranormal"),
        ("a", "politically correct"),
        ("a", "puzzling"),
        ("a", "racist"),
        ("a", "radical"),
        ("a", "raging"),
        ("a", "rambuctious"),
        ("a", "raw"),
        ("a", "red"),
        ("a", "ridiculous"),
        ("a", "scrappy"),
        ("a", "scruffy"),
        ("a", "sharp"),
        ("a", "silly"),
        ("a", "slow"),
        ("a", "smooth"),
        ("a", "snappy"),
        ("a", "special"),
        ("a", "stupid"),
        ("a", "sweet"),
        ("a", "technologic"),
        ("a", "three dimensional"),
        ("a", "tiny"),
        ("a", "toxic"),
        ("a", "tubular"),
        ("a", "world-breaking"),
        ("an", "31337"),
        ("an", "awesome"),
        ("an", "awkward"),
        ("an", "entrancing"),
        ("an", "exquisite"),
        ("an", "extravagant"),
        ("an", "extravagant"),
        ("an", "herbal"),
        ("an", "horizontal"),
        ("an", "impossible"),
        ("an", "inappropriate"),
        ("an", "insane"),
        ("an", "uncanny"),
        ("an", "uncouth")
    ))

b.bfcounter = 0
b.bflast = 0
def backflip(e, bot):
    if bot.bfcounter < 12:
        bot.reply(e, irc.action("does "+" ".join(adjective())+" backflip and lands on its "+bodypart()))
        bot.bflast = time.time()
        bot.bfcounter += 1
        if bot.bflast + 60 < time.time():
            bot.bfcounter = 1
    elif bot.bfcounter == 12:
        bot.bfcounter = 13
        bot.reply(e, irc.action("is too tired to backflip right now"))
        time.sleep(60)
        bot.bfcounter = 0
b.addCommandHook("backflip", backflip, 30)

def rfc(e, bot):
    if len(e.args != 1):
        e.reply("Usage: !rfc <ID>")
        return
    url = "https://tools.ietf.org/html/rfc" + e.args[0]
    title = fetchTitle(url)
    if not title:
        bot.reply(e, "No such RFC standard.")
        return
    bot.reply(e, title + " " + url)
b.addCommandHook("rfc", rfc, 30)

def url(e, bot):
    title = fetchTitle(e.groups[0])
    if title:
        bot.reply(e, b"\02" + title.encode("utf_8") + b"\2 posted by " + e.sourceNick.encode("utf_8"))
b.addRegexHook("(https?://[^ ]*)", url, 90)

def getdb():
    return sqlite3.connect("db")

def deliverMail(e, bot):
    nick = e.msg if e.type == irc.NICK else e.sourceNick
    db = getdb()
    c = db.cursor()
    c.execute("SELECT source, msg, private, time FROM mail WHERE dest LIKE ?", (nick,))
    messages = c.fetchall()
    c.execute("DELETE FROM mail WHERE dest LIKE ?", (nick,))
    for m in messages:
        msg = nick + ": Mail from " + m[0]
        if m[3]:
            msg += " sent %s ago" % (relativetime(time.time() - int(m[3])))
        msg += ": " + m[1]
        if m[2] or not e.channel:
            bot.sendMsg(nick, msg)
        else:
            bot.reply(e, msg)
    db.commit()
b.addMsgHook(deliverMail, 70)
b.addJoinHook(deliverMail, 70)

def mail(e, bot):
    db = getdb()
    c = db.cursor()
    if len(e.args) < 2:
        bot.reply(e, "Syntax : !mail nick message")
        return
    nick = e.args[0]
    msg = " ".join(e.msg.split(" ")[2:]) # avoid collapsing whitespace
    private = (e.channel == None)
    c.execute("INSERT INTO mail (source, dest, private, msg, time) VALUES (?, ?, ?, ?, ?)", (e.sourceNick, nick, private, msg, time.time()))
    db.commit()
    bot.reply(e, "Message stored!")
b.addCommandHook("mail", mail, 90)
b.addCommandHook("msg", mail, 90)
b.addCommandHook("m", mail, 90)

def mailbag(e, bot):
    db = getdb()
    c = db.cursor()
    c.execute("SELECT dest FROM mail GROUP BY dest;")
    rows = c.fetchall()
    e.reply("I have mail for : " + ("nopony" if len(rows) == 0 else " ".join(row[0] for row in rows)))
b.addCommandHook("mailbag", mailbag, 90)
b.addCommandHook("mailbox", mailbag, 90)

def substitute(e, bot):
    global buffer
    if e.type == irc.MSG:
        if e.channel: source = e.channel
        else: source = e.sourceNick
        args = e.msg.split(e.msg[1])
        if len(args) >= 3:
            flags = re.I
            count = 1
            if len(args) >= 4:
                if "I" in args[3]:
                    flags ^= re.I
                if "g" in args[3]:
                    count = 0

            bufferlock.acquire()
            try:
                if source in buffer:
                    for e_ in buffer[source]:
                        text = None
                        if e_.type == irc.PRIVMSG and not re.match("s(?P<delim>[^ \tA-Za-z0-9]).*(?P=delim)", e_.msg):
                            if e_.nick == e.irc.nick and re.match("<.*>", e_.msg):
                                text = e_.msg
                            else:
                                text = "<%s> %s" % (e_.nick, e_.msg)
                        elif e_.type == irc.ACTION:
                            text = "* %s %s" % (e_.nick, e_.msg)
                        if text and re.search(args[1], text, flags=flags):
                            e.reply(re.sub(args[1], args[2], text, flags=flags, count=count))
                            break
            except (re.error):
                pass
            bufferlock.release()

b.addRegexHook("^s(?P<delim>[^ \tA-Za-z0-9]).*(?P=delim)", substitute, 70)

def rand_track(e, bot):
    bot.reply(e, eqbeats.ppTrack(eqbeats.random()))
b.addCommandHook("random", rand_track, 90)
b.addCommandHook("rand", rand_track, 90)

def tripletadd(left, right):
    tripletlock.acquire()
    left = left.lower()
    if left in triplets:
        if right != "" or "" not in triplets[left]:
            triplets[left].append(right);
    else:
        triplets[left]= [right];
    tripletlock.release()

def tripletget(left):
    left = left.lower()
    tripletlock.acquire()
    try:
        ret = random.choice(triplets[left])
    except KeyError:
        ret = ""
    tripletlock.release()
    return ret

def _store_words(line):
    words = line.split()
    for i in range(2, len(words)):
        tripletadd(words[i-2] + " " + words[i-1], words[i])
    if len(words) > 1:
        tripletadd(words[0], words[1])
        tripletadd(words[-2] + " " + words[-1], "")
        startingwords.append(words[0])

def store_words(e, bot):
    if e.type == irc.MSG:
        _store_words(e.msg);
b.addWildHook(store_words, 0)

def poemm(e, bot):
    words = e.msg.split()[1:]
    if len(words) < 1:
        words.append(random.choice(startingwords))
    while len(words) == 0 or words[-1] != "":
        words.append(tripletget(" ".join(words[-2:])))
    if words[-1] == "": words = words[:-1]
    msg = " ".join(words)
    bot.reply(e, msg)
b.addCommandHook("chain", poemm)
b.addCommandHook("poem", poemm)

def feed(e, bot):
    if auth(e.source) == OP:
        if len(e.args) != 1:
            e.reply("Syntax: !feed url")
            return
        page = open(e.args[0], "r")
        line = page.readline(1000)
        while(line):
            _store_words(line)
            line = page.readline(1000)
b.addCommandHook("feed", feed, 0)

def dundundun(e, bot):
    bot.reply(e, "DUN DUN DUUUN")
b.addRegexHook("or[\. ]+(is|am|are|was|were|will|do|does|did|can|could|should|shall|would)[\. ]+(I|he|she|it|you|they|we)( have)?[ ?!]*$", dundundun, 70)

def parensdundundun(e, bot):
    bot.reply(e, "(dun dun duuun)")
b.addRegexHook("\(or\)[\. ]+(is|am|are|was|were|will|do|does|did|can|could|should|shall|would)[\. ]+(I|he|she|it|you|they|we)( have)?[ ?!]*$", parensdundundun, 70)
b.addRegexHook("\(or[\. ]+(is|am|are|was|were|will|do|does|did|can|could|should|shall|would)[\. ]+(I|he|she|it|you|they|we)( have)?[ ?!]*\)$", parensdundundun, 70)

def batman(e, bot):
    bot.reply(e, "I'm the " + adjective()[1] + " Batman.")
b.addCommandHook("batman", batman)

def technothing():
    thing = random.choice((
        "%s %s %s",
        "%s %s %s",
        "%s %s",
        "%s %s",
        "%s %s",
        "%s %s",
        "%s %s",
        "%s %s",
        "%s analyzer",
        "%s detector",
        "%s generator",
        "%s log",
        "%s-o-matic",
        "%s provider",
        "%s reader",
        "%s scrambler",
        "%s to %s adapter",
        "%s warmer",
        "%s%s",
        "%s%s",
        "CSS3",
        "HTML5",
        "OS",
        "PocketPC™"
        "RSS",
        "USB %s",
        "VGA",
        "XML",
        "audio",
        "automated %s",
        "browser",
        "camera",
        "cat",
        "cell",
        "computer",
        "cookies",
        "data",
        "database",
        "database",
        "email",
        "encoding",
        "facebook",
        "feet",
        "femto%s",
        "friendster", #olol
        "gibson",
        "gopher",
        "granular %s",
        "internet %s",
        "internet",
        "keyboard",
        "mainframe",
        "memory",
        "mouse",
        "net%s",
        "network",
        "player",
        "pony",
        "port",
        "screen",
        "screen",
        "security",
        "sims",
        "socket",
        "sound",
        "streaming %s",
        "synthesis",
        "tablet",
        "techno%s",
        "text processor",
        "time",
        "toaster",
        "tumblr",
        "twitter",
        "vegetable",
        "video",
        "video",
        "virtual %s",
        "waveform",
        "web%s",
        "youtube"
    ))
    while "%s" in thing:
        thing = thing.partition("%s") # ghetto string formatting :>
        thing = thing[0] + technothing() + thing[2]
    return thing

def technoverb():
    return random.choice((
        "bypass",
        "calibrate",
        "decrypt",
        "delete",
        "encode",
        "fork",
        "hack",
        "ignore",
        "jailbreak",
        "mangle",
        "overwrite",
        "probe",
        "process",
        "reconfigure",
        "relocate",
        "replace",
        "thread",
        "undo",
        "unlock",
        "unset"
    ))

def techsupport(e, bot):
    e.reply(random.choice((
        "Try to %s your %s.",
        "You could probably %s the %s.",
        "I think your best bet would be to %s your %s.",
        "It may fix it if you %s the %s.",
        "Does anything happen if you %s the %s?",
        "Don't %s the %s. Things will break.",
        "Don't ever %s the %s or bad things will happen.",
        "Just %s your %s. It always works."
        )) % (technoverb(), technothing()))
b.addCommandHook("techsupport", techsupport)

def ffeature(e, bot):
    if auth(e.source) >= HOP:
        tids = e.args
        if len(tids) == 0 and bot.lastTid:
            tids = (bot.lastTid,)
        with open("/var/spool/eqbeats/feature.queue", "a") as f:
            for tid in tids:
                t = eqbeats.track(tid)
                if(t):
                    f.write("%d %s - %s\n" % (t['id'], t['artist']['name'], t['title']))
                    e.reply("queued %s forcefully\n" % (eqbeats.ppTrack(t)))
b.addCommandHook("ffeature", ffeature, 0)

def feature(e, bot):
    if auth(e.source) >= HOP:
        tids = e.args
        if len(tids) == 0 and bot.lastTid:
            tids = (bot.lastTid,)
        for tid in tids:
            try:
                int(tid)
                bot.reply(e, os.popen("sudo -u eqbeats-pub EQBEATS_DIR=/var/lib/eqbeats /opt/eqbeats/libexec/eqbeats/fqueue " + tid + " 2>&1").read())
            except (TypeError, ValueError):
                continue
b.addCommandHook("feature", feature, 0)

def fetchTid(e, bot):
    bot.lastTid = e.groups[0]
b.addRegexHook("https?://(?:www\\.)?eqbeats\\.org/track/([0-9]+)", fetchTid)

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
        bot.reply(e, msg)
b.addRegexHook("[^ \\t]==", getvalue, 90)

def backflop(e, bot):
    e.reply(irc.action("flops around on its back"))
b.addCommandHook("backflop", backflop, 70)

def log(e, bot):
    global buffer
    if e.type in (irc.MSG, irc.ACTION):
        buf = e.channel if e.channel else e.source
        bufferlock.acquire()
        if buf not in buffer:
            buffer[buf] = []
        buffer[buf].insert(0, e)
        if len(buffer[buf]) > 500:
            buffer[buf] = buffer[buf][:500]
        bufferlock.release()

    global lastseen
    if e.nick:
        seenlock.acquire()
        lastseen[e.nick.lower()] = e
        if e.type == irc.NICK:
            lastseen[e.msg.lower()] = e
        seenlock.release()

b.addWildHook(log, 30)
b.addOutmsgHook(log, 30)
b.addIgnoreHook(log, 30)

def whatis(e, bot):
    if len(e.args) == 0:
        e.reply("Usage : !whatis <thing>")
        return
    thing = " ".join(e.args)
    db = getdb()
    c = db.cursor()
    c.execute("SELECT thing, definition FROM definitions WHERE thing LIKE ? ORDER BY length(thing) ASC, random() LIMIT 1", ("%"+thing+"%",))
    row = c.fetchone()
    if row:
        e.reply(row[0]  + " " + row[1])
    else:
        verb = "are" if e.msg.split()[0][-3:] == "are" else "is"
        e.reply(thing + " " + verb + random.choice((
            " A DIRTY COMMUNIST",
            " A SINGULARITY OF SELF-DEPRECIATION",
            " ADOPTED",
            " AN ABOMINATION OF THIS EARTH",
            " BAD AND YOU SHOULD FEEL BAD",
            " CURRENTLY IN THERAPY BECAUSE OF YOU",
            " FUCK YOUR !WHATIS",
            " GOD'S MISTAKE",
            " NOT INTERESTED, STOP CALLING",
            " NOT WORTH ANYONE'S TIME",
            " NOTHING ANYONE CARES ABOUT",
            " THE REASON YOU SUCK",
            " YOUR FACE",
            " YOUR MOM",
            " a butt fart"
        )))
b.addCommandHook("whatis", whatis, 70)
b.addCommandHook("whois", whatis, 70)
b.addCommandHook("whatare", whatis, 70)
b.addCommandHook("whoare", whatis, 70)

def thatis(e, bot):
    db = getdb()
    c = db.cursor()
    thing = " ".join(e.groups[0].split()) # collapse whitespace
    c.execute("INSERT INTO definitions (definition, thing, source) VALUES (?, ?, ?)", (e.groups[1], thing, e.source))
    db.commit()
b.addRegexHook("(.+) +((?:is|are|could be|might be) +.+)", thatis, 70)

def relativetime(lapse):
    if lapse < 1:
        return "some milliseconds"
    elif lapse < 120: # 2 minutes
        return "%s seconds" % (int(lapse),)
    elif lapse < 60 * 60 * 2: # 2 hours
        return "%s minutes" % (int(lapse / 60),)
    elif lapse < 60 * 60 * 24: # 1 day
        return "%s hours and %s minutes" % (int(lapse / 60 / 60), int((lapse/60) % 60))
    elif lapse < 60 * 60 * 24 * 2: # 2 days
        return "%s hours" % (int(lapse / 60 / 60),)
    elif lapse < 60 * 60 * 24 * 61: # 2 months
        return "%s days" % (int(lapse / 60 / 60 / 24),)
    else:
        return "%s months" % (int(lapse / 60 / 60 / 24 / 30.5),) # wonky but who cares


def seen(e, bot):
    global lastseen
    if len(e.args) != 1:
        e.reply("Usage : !seen <nick>")
        return
    nick = e.args[0]
    if nick.lower() == e.nick.lower():
        e.reply(nick + " was last seen right here, right now, asking dumb questions.")
        return
    elif nick.lower() == e.irc.nick.lower():
        e.reply("I'm right here, hello.")
        return
    if nick.lower() in lastseen:
        e_ = lastseen[nick.lower()]
        msg = nick + " was last seen " + relativetime(time.time() - e_.time) + " ago, "
        if e_.type == irc.QUIT:
            msg += "quitting irc with message \"%s\"" % (e_.msg,)
        elif e_.type == irc.JOIN:
            msg += "joining %s." % (e_.channel,)
        elif e_.type == irc.PART:
            msg += "leaving %s." % (e_.channel,)
        elif e_.type == irc.NICK:
            msg += "changing their nick "
            if e_.nick.lower() == nick.lower():
                msg += "from %s." % (e_.msg,)
            else:
                msg += "to %s." % (e_.nick,)
        elif e_.type in (irc.MSG, irc.ACTION):
            if e_.channel:
                if e_.type == irc.MSG:
                    msg += "in %s: <%s> %s" % (e_.channel, e_.nick, e_.msg)
                else:
                    msg += "in %s: * %s %s" % (e_.channel, e_.nick, e_.msg)
            else:
                msg += "via query."
        else:
            msg += "doing something unusual."
        e.reply(msg)
    else:
        e.reply("As far as I know, " + nick + " is just an urban legend.")
b.addCommandHook("seen", seen, 90)

def info(e, bot):
    e.reply("Hello! I am a bot for EqBeats. My only useful command is !eqsearch. Blame codl for all this.")
b.addCommandHook("eqbot", info, 0)
b.addCommandHook("help", info, 90)

def once(bot):
    for channel in bot.channels:
        if channel.level >= 90:
            bot.sendMsg(channel.name, "once")
    return random.randint(30, 172800) # 48h :D
b.addTimeHook(random.randint(120, 172800), once)

def fun(e, bot):
    e.reply("Fun!")
b.addCommandHook("fun", fun, 70)

funcount=0

def fun_(e, bot):
    global funcount
    if funcount < 5:
        e.reply("Fun!")
        funcount += 1
b.addRegexHook("^fun[!? ]*$", fun_, 70)

def funreset(bot):
    global funcount
    if funcount > 0:
        funcount -= 1
    return 20
b.addTimeHook(20, funreset)

def save(bot):
    seenlock.acquire()
    try:
        with open("seen.json", "w") as f:
            json.dump(lastseen, f, indent=4, cls=irc.EventEncoder)
    except OSError:
        print("Cannot open seen.json for writing")
    seenlock.release()

    tripletlock.acquire()
    try:
        with open("triplets.pickle", "wb") as f:
            pickle.dump([triplets, startingwords], f)
    except OSError:
        print("Cannot open triplets.pickle for writing")
    tripletlock.release()

    return 300
b.addTimeHook(20, save)


triplets = dict()
startingwords = list()
tripletlock = threading.Lock()
tripletlock.acquire()
try:
    with open("triplets.pickle", "rb") as f:
        triplets, startingwords = pickle.load(f)
except (OSError, ValueError):
    print("Cannot open triplets.json for reading")
tripletlock.release()

buffer = {}
bufferlock = threading.Lock()

lastseen = {}
seenlock = threading.Lock()
seenlock.acquire()
try:
    f = open("seen.json", "r")
    lastseen = json.load(f, object_hook=irc.Event.from_dict)
    f.close()
except (OSError, ValueError):
    print("Cannot open seen.json for reading")
    lastseen = {}
seenlock.release()

i.recv()
i.recv()
i.recv()
i.recv()
if os.getenv("NICKSERV_PASSWORD"):
    i.sendMsg("NickServ", "IDENTIFY EqBot %s" % os.getenv("NICKSERV_PASSWORD"))
i.setMode("-x")
b.join("#eqbot", 100)
if LIVE:
    b.join("#eqbeats", 90)
    b.join("#bronymusic", 70)
    b.join("#toastbeard", 70)
b.run()
