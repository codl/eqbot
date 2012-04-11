#!/usr/bin/python3

import bot
import irc
import eqbeats
import random
import time
import re
import urllib as ul
import sys

i = irc.Irc("irc.ponychat.net")
i.setNick("EqBot_")
if len(sys.argv) > 1 and sys.argv[1] == "live":
    i.setNick("EqBot")
i.realname = "EqBot"
i.username = "eqbot"
i.connect()
b = bot.Bot(i)

def ping(e, bot):
    bot.reply(e, "pong")
b.addCommandHook("ping", ping)

def aeiou(e, bot):
    if random.random() < 0.5:
        bot.reply(e, random.choice(("football!", "uuuuuuuuuu", "holla holla get $", "here comes another chinese earthquake ebrbrbrbrbrbrbrbrbrbrbrbrb", "99999999999999")), hilight=False)
b.addRegexHook("aeiou", aeiou)
b.addRegexHook("john madden", aeiou)

def hyphen(e, bot):
    bot.reply(e, "<" + e.sourceNick + "> " + re.sub("(\w)-(ass|flank) (\w)", "\\1 \\2-\\3", e.msg, flags=re.I), hilight=False)
b.addRegexHook("\w-(ass|flank) \w", hyphen)

def plot(e, bot):
    bot.reply(e, "<" + e.sourceNick + "> " + re.sub("plot", "intrigue", re.sub("PLOT", "INTRIGUE", e.msg), re.I), hilight=False)
b.addRegexHook("plot", plot)

def search(e, bot):
    tracks = eqbeats.search(e.msg[1:])[:5]
    for t in tracks:
        bot.reply(e, eqbeats.ppTrack(t))
    if len(tracks) == 0:
        bot.reply(e, "No tracks found.")
b.addRegexHook("^\?\w", search)

def flipcoin(e, bot):
    bot.reply(e, "tails" if random.random() < 0.5 else "heads")
b.addCommandHook("flipcoin", flipcoin)
b.addCommandHook("flip", flipcoin)
b.addCommandHook("coin", flipcoin)

def choice(e, bot):
    choices = e.msg.split()[1:]
    if any(pony in choices for pony in ("ponies", "PONIES", "pony", "PONY", "pone", "PONE", "poni", "PONI")):
        bot.reply(e, b"\02Ponies, obviously.")
    elif len(choices) <= 1:
        bot.reply(e, "Not much of a choice, eh?")
    else:
        bot.reply(e, random.choice(choices))
b.addCommandHook("choice", choice)
b.addCommandHook("choose", choice)

def newTracks(bot):
    for t in eqbeats.newTracks():
        bot.sendMsg("New track : " + eqbeats.ppTrack(t), "#eqbeats")
    return 120
b.addTimeHook(120, newTracks)

def once(bot):
    bot.sendMsg(random.choice(("untz", "once")), "#eqbeats")
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
b.addCommandHook("roll", roll)

def rejoice(e, bot):
    bot.reply(e, "yay", hilight=False)
b.addCommandHook("rejoice", rejoice)
b.addCommandHook("cheer", rejoice)

def louder(e, bot):
    bot.reply(e, b"\002yay", hilight=False)
b.addCommandHook("louder", louder)

def louder_(e, bot):
    bot.reply(e, b"\002Yay!", hilight=False)
b.addCommandHook("louder!", louder_)

if len(sys.argv) > 1 and sys.argv[1] == "live":
    time.sleep(2)
    i.sendMsg("IDENTIFY FnkrfBPo9f-X", "NickServ")
    i.join("#eqbeats")
b.run()
