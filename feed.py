#!/usr/bin/python3
import sqlite3
import sys

print("imports done")

db = sqlite3.connect("db")
c = db.cursor()

print("db cursor acquired")


line = sys.stdin.readline()
while line:
    print(line)
    words = line.split()
    for i in range(1, len(words)):
        c.execute("INSERT INTO word_pairs (first, second) VALUES (?, ?)", (words[i-1], words[i]))
    if len(words) > 1:
        c.execute("INSERT INTO word_pairs (first) VALUES (?)", (words[-1],))
        c.execute("INSERT INTO word_pairs (second) VALUES (?)", (words[0],))
    line = sys.stdin.readline()

db.commit()
