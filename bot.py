#!/usr/bin/python3

import irc
import re
import time
import threading

class Channel:
    def __init__(self, name, level=50):
        self.name = name
        self.level = level

    def __repr__(self):
        return("<Channel: " + self.name + " at level " + str(self.level) + ">")

class Hook:
    def __init__(self, func, level=50):
        self.func = func
        self.level = level

    def __repr__(self):
        return("<Hook: " + self.func.__name__ + " at level " + str(self.level) + ">")

class Whois:
    def __init__(self, nick, bot=None):
        if not isinstance(nick, str): raise TypeError
        self.nick = nick
        self.user = None
        self.host = None
        self.realname = None
        self.server = None
        self.serverdesc = None
        if bot:
            bot.irc._send("WHOIS " + nick)
            for e in bot.eventLoop():
                if e.type == irc.OTHER:
                    args = e.msg.split()
                    try:
                        if args[3].lower() == self.nick.lower():
                            if args[1] == "318": # ENDOFWHOIS
                                break
                            elif args[1] == "401": # NOSUCHNICK
                                nick = None
                                break
                            elif args[1] == "311": # WHOISUSER
                                self.nick = args[3]
                                self.user = args[4]
                                self.host = args[5]
                                self.realname = " ".join(args[7:])[1:]
                            elif args[1] == "312": # WHOISSERVER
                                self.server = args[5]
                                self.serverdesc = " ".join(args[6])[1:]
                    except IndexError:
                        pass


    def __repr__(self):
        return("<Whois: " + self.nick + ">")

class Bot:
    def __repr__(self):
        return "<Bot>"

    def __init__(self, irc):
        self.irc = irc
        self.msgQueue = []
        self.commandHooks = {}
        self.regexHooks = []
        self.timeHooks = []
        self.noticeHooks = []
        self.wildHooks = []
        self.nickHooks = []
        self.joinHooks = []
        self.partHooks = []
        self.quitHooks = []
        self.msgHooks = []
        self.prefix = "!"
        self.channels = []
        self.eventQueues = []

    def join(self, channel, level=50):
        for c in self.channels:
            if c.name == channel:
                c.level = level
                return
        self.irc.join(channel)
        self.channels.append(Channel(channel, level))

    def part(self, channel):
        for i in range(len(self.channels)):
            if self.channels[i].name == channel:
                del self.channels[i]
        self.irc.part(channel)

    def level(self, channel):
        for c in self.channels:
            if c.name == channel:
                return c.level
        else: return -1

    def react(self, e, act):
        msg = irc.action(act)
        dest = e.sourceNick
        if e.channel:
            dest = e.channel
        self.sendMsg(dest, msg)

    def reply(self, e, msg, hilight=True):
        if(isinstance(msg, str)): msg = msg.encode("utf_8")
        dest = e.sourceNick
        if e.channel:
            #if hilight:
            #    msg = e.sourceNick.encode("utf_8") + b": " + msg
            dest = e.channel
        self.sendMsg(dest, msg)

    def sendMsg(self, dest, msg):
        self.msgQueue += [(dest, msg)];

    def whois(self, nick):
        return Whois(nick, self)

    def processQueue(self):
        delay = 0.3
        while True:
            try:
                msg = self.msgQueue.pop(0)
                self.irc.sendMsg(*msg)
                print("Sleeping for " + str(delay) + " seconds")
                time.sleep(delay)
                delay *= 1.5
                if delay > 5: delay = 5
            except IndexError:
                time.sleep(0.3)
                delay = 0.3

    def eventLoop(self):
        queue = []
        self.eventQueues.append(queue)
        try:
            while True:
                if len(queue) != 0:
                    yield queue.pop(0)
                else:
                    time.sleep(0.1)
        finally:
            self.eventQueues.remove(queue)

    def runEventHooks(self, e):
        if e.type == irc.MSG:
            def f(msg, hilight=False): self.reply(e, msg, hilight=hilight)
            e.reply = f
            for hook in self.msgHooks:
                if not e.channel or self.level(e.channel) >= hook.level:
                    threading.Thread(target=hook.func, args=(e, self)).start()
            for hook in self.regexHooks:
                if not e.channel or self.level(e.channel) >= hook[1].level:
                    match = hook[0].search(e.msg)
                    if match:
                        e.groups = match.groups()
                        threading.Thread(target=hook[1].func, args=(e, self)).start()
            if not e.channel:
                try:
                    e.args = e.msg.split()[1:]
                    threading.Thread(target=self.commandHooks[e.msg.lower().lstrip(self.prefix).split(" ")[0]].func, args=(e, self)).start()
                except KeyError:
                    pass
            elif e.msg[0] == self.prefix:
                try:
                    e.args = e.msg.split()[1:]
                    hook = self.commandHooks[e.msg.split()[0][1:].lower()]
                    if self.level(e.channel) >= hook.level:
                        threading.Thread(target=hook.func, args=(e, self)).start()
                except KeyError:
                    pass
        elif e.type == irc.NOTICE:
            for hook in self.noticeHooks:
                threading.Thread(target=hook, args=(e, self)).start()
        elif e.type == irc.JOIN:
            for hook in self.joinHooks:
                if not e.channel or self.level(e.channel) >= hook.level:
                    threading.Thread(target=hook.func, args=(e, self)).start()
        elif e.type == irc.PART:
            for hook in self.partHooks:
                if not e.channel or self.level(e.channel) >= hook.level:
                    threading.Thread(target=hook.func, args=(e, self)).start()
        elif e.type == irc.QUIT:
            for hook in self.quitHooks:
                if not e.channel or self.level(e.channel) >= hook.level:
                    threading.Thread(target=hook.func, args=(e, self)).start()
        elif e.type == irc.NICK:
            for hook in self.nickHooks:
                threading.Thread(target=hook, args=(e, self)).start()

        for hook in self.wildHooks:
            if not e.channel or self.level(e.channel) >= hook.level:
                threading.Thread(target=hook.func, args=(e, self)).start()

    def runTimeHooks(self):
        for i, hook in enumerate(self.timeHooks):
            if hook[0] < time.time():
                self.timeHooks[i][0] = time.time() + hook[1](self)


    def addCommandHook(self, command, f, level=50):
        self.commandHooks.update({command: Hook(f, level)})
    def addRegexHook(self, regex, f, level=50):
        self.regexHooks += [(re.compile(regex, re.I), Hook(f, level))]
    def addWildHook(self, f, level=50):
        self.wildHooks += [Hook(f,level),]
    def addJoinHook(self, f, level=50):
        self.joinHooks += [Hook(f,level),]
    def addPartHook(self, f, level=50):
        self.partHooks += [Hook(f,level),]
    def addQuitHook(self, f, level=50):
        self.quitHooks += [Hook(f,level),]
    def addMsgHook(self, f, level=50):
        self.msgHooks += [Hook(f,level),]

    def addNoticeHook(self, f):
        self.noticeHooks += [f,]
    def addNickHook(self, f):
        self.nickHooks += [f,]
    def addTimeHook(self, delay, f):
        self.timeHooks += [[time.time() + delay, f]]


    def run(self):
        threading.Thread(target=self.processQueue).start()
        while True:
            e = self.irc.recv(1)
            if e:
                self.runEventHooks(e)
                for queue in self.eventQueues:
                    queue.append(e)
            self.runTimeHooks()
