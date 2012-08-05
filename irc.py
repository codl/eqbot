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
MSG = 2
PRIVMSG = 2
ACTION = 4
NICK= 5
MODECHANGE = 6
KICK = 7
JOIN = 8
PART = 9
QUIT = 10
TOPIC = 13
NOTICE = 11
ERROR = 12
OTHER = 0

# errors
ERR_ERRONEOUSNICK = 432
ERR_NICKALREADYINUSE = 433
ERR_CANNOTJOIN = 474 # is it only for bans?

def action(msg):
    if(isinstance(msg, str)):
        msg = msg.encode("UTF-8")
    return b"\1ACTION " + msg + b"\1"

class Error(Exception):
    def __repr__(self): return "<IRC Error>"

class CantConnectError(Error):
    def __repr__(self): return "<IRC Can't connect Error>"

class CantConnectError(Error):
    def __repr__(self): return "<IRC IncorrectNick Error>"

class Event:
    def __repr__(self):
        return "<IRC event from " + self.source + ">"

    def __init__(self, type, source=None, dest=None, msg=None, etime=None, irc=None, channel=None):
        self.type = type
        self.source = source
        self.nick = source.partition("!")[0] if source else None
        self.sourceNick = self.nick
        self.host = source.partition("@")[2] if source else None
        self.msg = msg
        self.channel = dest if dest and dest[0] in "#&" else channel
        self.dest = dest if dest else channel if channel else irc.nick if irc else None
        self.irc = irc
        self.time = float(etime) if etime else time.time()

class Irc:
    def __repr__(self):
        return "<IRC connection to " + self.host + ":" + str(self.port) + (", not connected" if self.status != CONNECTED else "") + ">"

    def __init__(self, host, port=6667):
        self.host = host
        self.port = port
        self.socket = None
        self.status = DISCONNECTED
        self.nick = "Nameless"
        self.username = "nameless"
        self.realname = "Nameless"
        self._inbuf = bytearray()

    def _send(self, data):
        if isinstance(data, str): data = data.encode("utf_8")
        if data[-1] != b'\n': data += b'\n'
        self.socket.send(data)
        print("OUT " + str(data, "utf_8")[:-1])

    def _recv(self, timeout = None):
        self.socket.settimeout(timeout)
        while self._inbuf.find(b'\n') == -1:
            try:
                self._inbuf += self.socket.recv(1024)
            except socket.timeout:
                return None
        command = ""
        for enc in ("utf_8", "latin_1"):
            try:
                command = self._inbuf.partition(b'\n')[0].decode(enc)
                break
            except UnicodeDecodeError: pass

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
                    if args[3] == ":\1ACTION":
                        args[-1] = args[-1][:-2] # remove \1\r
                        return Event(ACTION, source=args[0][1:], msg=" ".join(args[4:]), irc=self)
                    else:
                        return Event(MSG, source=args[0][1:], msg=" ".join(args[3:])[1:-1], irc=self)
                else:
                    if args[3] == ":\1ACTION":
                        args[-1] = args[-1][:-2] # remove \1\r
                        return Event(ACTION, source=args[0][1:], msg=" ".join(args[4:]), channel=args[2], irc=self)
                    else:
                        return Event(MSG, source=args[0][1:], msg=" ".join(args[3:])[1:-1], channel=args[2], irc=self)
            elif args[1] == "NICK":
                return Event(NICK, source=args[2][1:-1] + "!" + args[0].partition("!")[2], msg=args[0][1:].partition("!")[0], irc=self) #source is new nick, msg is old nick, so reply() works
            elif args[1] == "JOIN":
                return Event(JOIN, source=args[0][1:], channel=args[2][1:-1], irc=self)
            elif args[1] == "PART":
                return Event(PART, source=args[0][1:], channel=args[2][:-1], irc=self)
            elif args[1] == "QUIT":
                return Event(QUIT, source=args[0][1:], msg=" ".join(args[2:])[1:-1], irc=self)
            elif args[1] == "NOTICE":
                return Event(NOTICE, source=args[0][1:], msg=" ".join(args[3:])[1:-1], irc=self)
            elif args[1] == "TOPIC":
                return Event(TOPIC, source=args[0][1:], dest=args[2], msg=" ".join(args[3:])[1:-1], irc=self)
            #TODO parse more events
            else:
                return Event(OTHER, irc=self, msg=data)

    def join(self, chan):
        self._send("JOIN " + chan)

    def part(self, chan, reason=None):
        if reason:
            self._send("PART " + chan + " :"+reason)
        else:
            self._send("PART " + chan)

    def kick(self, chan, nick, reason=None):
        self._send("KICK " + chan + " " + nick + (" :"+reason if reason else ""))

    def sendMsg(self, dest, msg):
        if(isinstance(msg, str)):
            msg = msg.encode("UTF-8")
        if(isinstance(dest, str)):
            dest = dest.encode("UTF-8")
        self._send(b"PRIVMSG " + dest + b" :" + msg.translate(bytes.maketrans(b"\n", b" "))) # same syntax for channels and users, yay :D

    def setMode(self, mode):
        self._send("MODE " + self.nick + " " + mode)


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
        return self._recv()

    def setNick(self, nick):
        if not isinstance(nick, str): raise IncorrectNickError
        if self.status != DISCONNECTED:
            self._send("NICK " + nick)
        # TODO catch errors
        self.nick = nick;
