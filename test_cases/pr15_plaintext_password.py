import sqlite3

def save_user(username, password):
    connection = sqlite3.connect("users.db")
    connection.execute("INSERT INTO users VALUES (?, ?)", (username, password))
    connection.commit()
