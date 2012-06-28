#!/usr/bin/python3

import irc
import sqlite3
import sys
import os
import re
from time import strftime, time, gmtime

WORKDIR = "/srv/irclogs/"
CHANNELS = ("#bronymusic","#eqbeats")
DB = "/home/codl/dev/eqbot/db"

db = sqlite3.connect(DB)
c = db.cursor()

DAY = 60 * 60 * 24 # just for convenience

now = int(time())
start = now - 3600 - ((now - 3600) % DAY) # start of day unless <1h after midnight, then start of previous day

if "-a" in sys.argv:
    start = 0

def stripcolor(msg):
    msg = re.sub("\3[0-9]*|\2", "", msg)
    return msg

def html(msg):
    msg = re.sub("<", "&lt;", msg)
    msg = re.sub(">", "&gt;", msg)
    msg = re.sub("(https?://[^ \2\3]+[^ \2\3)])","<a href=\"\\1\">\\1</a>",msg)
    msg = re.sub("  ", "&nbsp;&nbsp;", msg)

    parts = re.split("\3", " " + msg)
    msg = parts[0]
    spancount = 0
    for part in parts[1:]:
        spancount += 1
        if part[0] == "0":
            part = part[1:]
        if part[0] in "0123456789":
            if part[0] == '1':
                if part[1] not in "012345":
                    msg += "<span class=\"black\">"
                else:
                    if part[1] == "0":
                        msg += "<span class=\"cyan\">"
                    elif part[1] == "1":
                        msg += "<span class=\"bright cyan\">"
                    elif part[1] == "2":
                        msg += "<span class=\"bright blue\">"
                    elif part[1] == "3":
                        msg += "<span class=\"bright purple\">"
                    elif part[1] == "4":
                        msg += "<span class=\"bright black\">"
                    elif part[1] == "5":
                        msg += "<span class=\"white\">"
                    part = part[1:]
            elif part[0] == '2':
                msg += "<span class=\"blue\">"
            elif part[0] == '3':
                msg += "<span class=\"green\">"
            elif part[0] == '4':
                msg += "<span class=\"bright red\">"
            elif part[0] == '5':
                msg += "<span class=\"red\">"
            elif part[0] == '6':
                msg += "<span class=\"purple\">"
            elif part[0] == '7':
                msg += "<span class=\"yellow\">"
            elif part[0] == '8':
                msg += "<span class=\"bright yellow\">"
            elif part[0] == '9':
                msg += "<span class=\"bright green\">"
            elif part[0] == '0':
                msg += "<span class=\"bright white\">"
            msg += part[1:]
        else:
            msg += "<span class=\"white\">"
            msg += part
    msg += "</span>" * spancount

    parts = re.split("\2", " " + msg)
    bopen = False
    msg = parts[0]
    for part in parts[1:]:
        msg += "</b>" if bopen else "<b>"
        msg += part
        bopen = not bopen
    if bopen: msg += "</b>"

    return msg[2:]

def flair(nick):
    if nick.lower() in ("scootaloo", "scootaloo_mobile"):
        return " scoot"
    else: return ""

index = open(WORKDIR + os.sep + "index.html", "w")
index.write("""
    <!doctype html !>
    <html>
    <head>
        <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
        <title>LOLGS</title>
        <link rel="stylesheet" type="text/css" href="style.css" />
    </head>
    <body>
        <h1>LOLGS</h1>
        <div class="inner">
            <p>All times are UTC</p>
    """)

for channel in CHANNELS:
    chandir = WORKDIR + os.sep + channel[1:]
    if not os.access(chandir , os.W_OK):
        try:
            os.makedirs(chandir)
        except os.error:
            print("Can't write or something")
            exit(1)
    index.write("""
            <a class="channel" href="%s">%s</a>
            """%(channel[1:], channel))
    chanindex = open(chandir + os.sep + "index.html", "w")
    chanindex.write("""
    <!doctype html !>
    <html>
    <head>
        <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
        <title>%s</title>
        <link rel="stylesheet" type="text/css" href="../style.css" />
    </head>
    <body>
        <a class="back" href="..">&lt; Back</a>
        <h1>%s</h1>
        <div class="inner">
    """%((channel,)*2))
    days = []
    day = 0
    linenr = 0
    c.execute("SELECT type, source, dest, msg, time FROM log WHERE dest LIKE ? AND time > ? ORDER BY time ASC", (channel, start))
    for row in c:
        e = irc.Event(*row)
        linenr += 1
        if int(e.time) - int(e.time) % DAY != day:
            linenr = 0
            day = int(e.time) - int(e.time) % DAY
            pprint = strftime("%y-%m-%d", gmtime(day))
            if len(days) > 0:
                days[-1][1].write("""
                </div>
                <p id="footer" class="I don't even know">
                <a href="%s.html">%s &gt;</a><br/>
                </p>
                </body>
                </html>
                """%((pprint,)*2))
                days[-1][1].close()
                days[-1][2].close()
            days.append((pprint,
                open(chandir + os.sep + pprint + ".html", "w"),
                open(chandir + os.sep + pprint + ".txt", "w")))
            days[-1][1].write("""
                <!doctype html !>
                <html>
                <head>
                    <meta content="text/html; charset=UTF-8" http-equiv="Content-Type">
                    <title>""" + channel + """ - """ + pprint + """</title>
                    <link rel="stylesheet" type="text/css" href="../style.css" />
                </head>
                <body>
                <a class="back" href=".">&lt; Back</a>
                <h1>"""+ channel + """ - """ + pprint + """</h1>
                <div class=\"inner\">
                """)

        if e.type == irc.JOIN and e.nick == "EqBot":
            days[-1][1].write("<hr />")
            days[-1][2].write("--\n")
        days[-1][1].write("<div class=\"event\" id=\"" + str(linenr) + "\">"+
            "<span class=\"time\"><a href=\"#"+str(linenr)+"\">"+strftime("%H:%M", gmtime(e.time))+"</a></span> ")
        days[-1][2].write("["+strftime("%H:%M", gmtime(e.time))+"] ")
        if e.type == irc.MSG:
            days[-1][1].write("<span class=\"msg\"><span class=\"brackets\">&lt;<span class=\"nick %s\">%s</span>&gt;</span> %s</span>"%(flair(e.nick), e.nick, html(e.msg)))
            days[-1][2].write("<" + e.nick + "> " + stripcolor(e.msg) + "\n")
        elif e.type == irc.ACTION:
            days[-1][1].write("<span class=\"action\"><span class=\"deco\">*</span> <span class=\"nick %s\">%s</span> %s</span>"%(flair(e.nick), e.nick, html(e.msg)))
            days[-1][2].write("* " + e.nick + " " + stripcolor(e.msg) + "\n")
        elif e.type == irc.JOIN:
            days[-1][1].write("<span class=\"join\"><span class=\"deco\">&gt;</span> <span class=\"nick %s\">%s</span> (<span class=\"host\">%s</span>) joined %s</span>"%(flair(e.nick), e.nick, e.source.partition("!")[2], e.channel))
            days[-1][2].write("> " + e.nick + " joined " + e.channel + "\n")
        elif e.type == irc.PART:
            days[-1][1].write("<span class=\"part\"><span class=\"deco\">&lt;</span> <span class=\"nick %s\">%s</span> (<span class=\"host\">%s</span>) left %s</span>"%(flair(e.nick), e.nick, e.source.partition("!")[2], e.channel))
            days[-1][2].write("< " + e.nick + " left " + e.channel + "\n")
        elif e.type == irc.QUIT:
            days[-1][1].write("<span class=\"quit\"><span class=\"deco\">&laquo;</span> <span class=\"nick %s\">%s</span> (<span class=\"host\">%s</span>) quit IRC : %s</span>"%(flair(e.nick), e.nick, e.source.partition("!")[2], e.msg))
            days[-1][2].write("< " + e.nick + " quit IRC : " + e.msg + "\n")
        elif e.type == irc.NICK:
            days[-1][1].write("<span class=\"old nick %s\">%s</span> is now <span class=\"new nick %s\">%s</span>"%(flair(e.msg), e.msg, flair(e.nick), e.nick))
            days[-1][2].write(e.msg + " is now " + e.nick + "\n")
        elif e.type == irc.TOPIC:
            days[-1][1].write("<span class=\"nick %s\">%s</span> has changed the topic to: <span class=\"topic\">%s</span>"%(flair(e.nick), e.nick, e.msg))
            days[-1][2].write(e.nick + " has changed the topic to: " + e.msg + "\n")
        else:
            days[-1][1].write("LOL I FORGOT THIDS MESSAGR TYPOE")
            days[-1][2].write("LOL Y FORGIT THIS MESAGE TYPE" + e.msg + "\n")
        days[-1][1].write("</div>")
    if len(days) > 0:
        days[-1][1].write("""
        </div>
        <p id="footer" class="I don't even know">
            <a class="hidden" href="#footer">#_^$$NO CARRIER</a>
        </p>
        </body>
        </html>
        """)
        days[-1][1].close()
        days[-1][2].close()

    pages = []
    for filename in os.listdir(chandir):
        if filename != "index.html" and filename[-5:] == ".html":
            pages.append(filename[:-5])
    #pages.reverse()
    pages.sort(reverse=True)
    for page in pages:
        chanindex.write(""" <a href="%s.html">%s</a> <small>(<a href="%s.txt">TXT</a>)</small>""" % ((page,)*3))
    chanindex.write("""
        </div>
        <p id="footer" class="I don't even know">
            <a class="hidden" href="#footer">#_^$$NO CARRIER</a>
        </p>
        </body>
        </html>
    """)





index.write("""
</div>
<p id="footer" class="I don't even know">
    <a class="hidden" href="#footer">#_^$$NO CARRIER</a>
</p>
</body>
</html>
""")
index.close()
