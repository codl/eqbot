#!/usr/bin/python3

import time
import socket

# LET'S GET SOME CONSTANTS UP IN HERE
# status constants
DISCONNECTED = 0
CONNECTING = 1
CONNECTED = 2

# event type constants
PING = 1
CHANMSG = 2
PRIVMSG = 3
ACTION = 4
PRIVACTION = 11
NICKCHANGE = 5
MODECHANGE = 6
KICK = 7
JOIN = 8
PART = 9
QUIT = 10
OTHER = 0

# errors
ERR_ERRONEOUSNICK = 432
ERR_NICKALREADYINUSE = 433


class Error(Exception):
    def __repr__(self): return "<IRC Error>"

class CantConnectError(Error):
    def __repr__(self): return "<IRC Can't connect Error>"

class CantConnectError(Error):
    def __repr__(self): return "<IRC IncorrectNick Error>"

class Event:
    def __repr__(self):
        return "<IRC event from " + self.source + ">"

    def __init__(self, type, source=None, msg=None, channel=None, irc=None):
        self.type = type
        self.source = source
        self.sourcenick = source.partition("!")[0] if source else None
        self.msg = msg
        self.channel = channel
        self.irc = irc
        self.time = time.gmtime()

class Irc:
    def __repr__(self):
        return "<IRC connection to " + self.host + ":" + str(self.port) + (", not connected" if self.status != CONNECTED else "") + ">"

    def __init__(self, host, port=6667):
        self.host = host
        self.port = port
        self.socket = None
        self.status = DISCONNECTED
        self.nick = "NamelessBot"
        self.username = "namelessbot"
        self.realname = "Nameless bot"
        self._inbuf = bytearray()

    def _send(self, data):
        if data[-1] != "\n": data += "\n"
        print("OUT " + data[:-1])
        self.socket.send(bytes(data, "UTF-8"))

    def _recv(self, timeout = None):
        self.socket.settimeout(timeout)
        while self._inbuf.find(b'\r') == -1:
            try:
                self._inbuf += self.socket.recv(4096)
            except socket.timeout:
                return None
        command = self._inbuf.partition(b'\r')[0].decode("UTF-8")
        self._inbuf = self._inbuf.partition(b'\n')[2]
        print("IN  " + command)
        return command

    def recv(self, timeout = None):
        data = self._recv(timeout)
        if not data: return None
        if data[0:4] == "PING":
            data = "PO" + data[2:]
            self._send(data)
            return Event(PING, irc=self)
        else:
            args = data.split(" ")
            if args[1] == "PRIVMSG":
                if args[2] == self.nick:
                    return Event(PRIVMSG, args[0][1:], " ".join(args[3:]), irc=self)
                else:
                    return Event(CHANMSG, args[0][1:], " ".join(args[3:])[1:], args[2], irc=self)
            elif args[1] == "NICK":
                return Event(NICKCHANGE, args[0][1:], args[2], irc=self)
            #TODO parse more events
            else: return Event(OTHER, irc=self)

    def join(self, chan):
        self._send("JOIN " + chan)

    def sendMsg(self, msg, dest):
        self._send("PRIVMSG " + dest + " :" + msg) # same syntax for channels and users, yay :D


    def connect(self):
        self.socket = socket.socket()
        self.status = CONNECTING
        try:
            self.socket.connect((self.host, self.port))
        except socket.error:
            self.status = DISCONNECTED
            self.socket.close()
            self.socket = None
            raise CantConnectError
        self.setNick(self.nick)
        self._send("USER " + self.username + " _ _ " + self.realname);
        return self.socket

    def setNick(self, nick):
        if not isinstance(nick, str): raise IncorrectNickError
        if self.status != DISCONNECTED:
            self._send("NICK " + nick)
        # TODO catch errors
        self.nick = nick;
