#!/usr/bin/python3

import irc
import re
import time
import threading

class Bot:
    def __repr__(self):
        return "<Bot>"

    def __init__(self, irc):
        self.irc = irc
        self.msgQueue = []
        self.commandHooks = {}
        self.regexHooks = []
        self.timeHooks = []
        self.wildHooks = []
        self.prefix = "!"

    def react(self, e, act):
        msg = irc.action(act)
        dest = e.sourceNick
        if e.channel:
            dest = e.channel
        self.sendMsg(msg, dest)

    def reply(self, e, msg, hilight=True):
        if(isinstance(msg, str)): msg = msg.encode("utf_8")
        dest = e.sourceNick
        if e.channel:
            if hilight:
                msg = e.sourceNick.encode("utf_8") + b": " + msg
            dest = e.channel
        self.sendMsg(msg, dest)

    def sendMsg(self, msg, dest):
        self.msgQueue += [(msg, dest)];

    def processQueue(self):
        delay = 0
        while True:
            try:
                msg = self.msgQueue.pop(0)
                self.irc.sendMsg(*msg)
                time.sleep(delay)
                delay += 0.1
            except IndexError:
                time.sleep(0.1)
                delay = 0

    def runWildHooks(self, e):
        for hook in self.wildHooks:
            threading.Thread(target=hook, args=(e, self)).start()

    def runCommandHooks(self, e):
        if e.type == irc.PRIVMSG:
            try:
                threading.Thread(target=self.commandHooks[e.msg.lower().lstrip(self.prefix).split(" ")[0]], args=(e, self)).start()
            except KeyError:
                pass
        elif e.type == irc.CHANMSG and e.msg[0] == self.prefix:
            try:
                threading.Thread(target=self.commandHooks[e.msg.split(" ")[0][1:]], args=(e, self)).start()
            except KeyError:
                pass

    def runRegexHooks(self, e):
        if e.type == irc.PRIVMSG or e.type == irc.CHANMSG:
            for hook in self.regexHooks:
                match = hook[0].search(e.msg)
                if match:
                    e.match = match.group()
                    threading.Thread(target=hook[1], args=(e, self)).start()

    def runTimeHooks(self):
        for i, hook in enumerate(self.timeHooks):
            if hook[0] < time.time():
                self.timeHooks[i][0] = time.time() + hook[1](self)

    def addCommandHook(self, command, f):
        self.commandHooks.update({command: f})
    def addRegexHook(self, regex, f):
        self.regexHooks += [(re.compile(regex, re.I), f)]
    def addTimeHook(self, delay, f):
        self.timeHooks += [[time.time() + delay, f]]
    def addWildHook(self, f):
        self.wildHooks += [f,]


    def run(self):
        threading.Thread(target=self.processQueue).start()
        while True:
            e = self.irc.recv(1)
            if e:
                self.runCommandHooks(e)
                self.runRegexHooks(e)
                self.runWildHooks(e)
            self.runTimeHooks()
