#!/usr/bin/python3

import bot
import irc
import eqbeats
import random
import time
import re

i = irc.Irc("irc.ponychat.net")
i.setNick("EqBot")
i.realname = "EqBot"
i.username = "eqbot"
i.connect()
b = bot.Bot(i)

def polo(e, bot):
    bot.reply(e, "POLO!", hilight=False)
b.addRegexHook("^marco!?$", polo)

def aeiou(e, bot):
    if random.random() < 0.5:
        bot.reply(e, random.choice(("football!", "uuuuuuuuuu", "holla holla get $", "here comes another chinese earthquake ebrbrbrbrbrbrbrbrbrbrbrbrb", "99999999999999")), hilight=False)
b.addRegexHook("aeiou", aeiou)
b.addRegexHook("john madden", aeiou)

def hyphen(e, bot):
    bot.reply(e, re.sub("(\w)-(ass|flank) (\w)", "\\1 \\2-\\3", e.msg, flags=re.I), hilight=False)
b.addRegexHook("\w-(ass|flank) \w", hyphen)

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

def newTracks(bot):
    for t in eqbeats.newTracks():
        bot.sendMsg("New track : " + eqbeats.ppTrack(t), "#eqbeats")
    return 120
b.addTimeHook(120, newTracks)

def once(bot):
    bot.sendMsg("once", "#eqbeats")
    return random.randint(60, 86400)
b.addTimeHook(random.randint(60, 86400), once)

time.sleep(2)
i.join("#eqbeats")
b.run()
