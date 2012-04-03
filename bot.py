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
        self.prefix = "!"

    def reply(self, e, msg, hilight=True):
        dest = e.sourceNick
        if e.type == irc.CHANMSG:
            if hilight:
                msg = e.sourceNick + ": " + msg
            dest = e.channel
        self.sendMsg(msg, dest)

    def sendMsg(self, msg, dest):
        self.msgQueue += [(msg, dest)];

    def processQueue(self):
        while True:
            try:
                msg = self.msgQueue.pop()
                self.irc.sendMsg(*msg)
            except IndexError:
                time.sleep(0.1)

    def runCommandHooks(self, e):
        if e.type == irc.PRIVMSG:
            try:
                threading.Thread(target=self.commandHooks[e.msg.split(" ")[0]], args=(e, self)).start()
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
                if hook[0].search(e.msg):
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


    def run(self):
        threading.Thread(target=self.processQueue).start()
        while True:
            e = self.irc.recv(1)
            if e:
                self.runCommandHooks(e)
                self.runRegexHooks(e)
            self.runTimeHooks()
