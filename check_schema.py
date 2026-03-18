import sqlite3
c=sqlite3.connect('data/tracker.db').cursor()
c.execute("SELECT sql FROM sqlite_master WHERE name='sessions'")
print(c.fetchone()[0])