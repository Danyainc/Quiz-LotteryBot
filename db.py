import sqlite3

connection = sqlite3.connect('my_database.db', check_same_thread=False)
cursor = connection.cursor()
# Создаем таблицу Users
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Quizzes (
    id INTEGER PRIMARY KEY,
    author_quiz INTEGER REFERENCES Users(telegram_id) ON UPDATE CASCADE,
    questions_id TEXT NOT NULL,
    date_end DATETIME NOT NULL
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Lotteries (
    id INTEGER PRIMARY KEY,
    author_lot INTEGER REFERENCES Users(telegram_id) ON UPDATE CASCADE,
    date_end_of_lot DATETIME NOT NULL
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Channels (
    id INTEGER PRIMARY KEY,
    channel_admin INTEGER REFERENCES Users(telegram_id) ON UPDATE CASCADE
)
''')

connection.commit()


def add_user(tg_id, username):
    with connection as con:
        cur = con.cursor()
        cur.execute('''
        INSERT INTO Users (telegram_id, username) VALUES (?, ?)
        ''', (tg_id, username))
        con.commit()
        print('all_good')


def is_user(tg_id):
    with connection as con:
        cur = con.cursor()
        cur.execute(f'''
        SELECT COUNT(*)  FROM Users WHERE telegram_id = ?
        ''', (tg_id,))
        count = cur.fetchone()[0]
        return count > 0


def get_user(tg_id):
    with connection as con:
        cur = con.cursor()
        cur.execute(f'''
        SELECT *  FROM Users WHERE telegram_id = ?
        ''', (tg_id,))
        return cur.fetchone()[0]


def add_channel(channel_id, tg_id):
    if is_user(tg_id):
        with connection as con:
            user_id = get_user(tg_id)
            cur = con.cursor()
            cur.execute(f'''
                    INSERT INTO Channels (id, channel_admin) VALUES (?, ?)
            ''', (channel_id, user_id))
            print('good')
            con.commit()


def get_channel(channel_id):
    with connection as con:
        cur = con.cursor()
        cur.execute(f'''
        SELECT *  FROM Channels WHERE id = ?
        ''', (channel_id,))
        return cur.fetchone()


def get_channels(tg_id):
    with connection as con:
        cur = con.cursor()
        cur.execute(f'''
        SELECT id  FROM Channels WHERE channel_admin = ?
        ''', (tg_id,))
        return cur.fetchall()


def del_channel(channel_id):
    with connection as con:
        cur = con.cursor()
        cur.execute(f'''
           DELETE  FROM Channels WHERE id = ?
           ''', (channel_id,))
        return cur.fetchall()
