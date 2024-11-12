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
    author_quiz INTEGER REFERENCES Users(telegram_id) ON DELETE CASCADE,
    questions_id TEXT NOT NULL,
    date_end DATETIME NOT NULL
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Lotteries (
    id INTEGER PRIMARY KEY,
    context_lottery TEXT,
    author_lot INTEGER REFERENCES Users(telegram_id) ON DELETE CASCADE,
    date_end_of_lot FLOAT NOT NULL,
    is_active BOOLEAN DEFAULT(FALSE)
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS UsersLotteries (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES Users(telegram_id) ON DELETE CASCADE,
    lottery_id INTEGER REFERENCES Lotteries(id) ON DELETE CASCADE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Channels (
    id INTEGER PRIMARY KEY,
    channel_admin INTEGER REFERENCES Users(telegram_id) ON DELETE CASCADE
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS ChannelsLotteries (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER REFERENCES Channels(id) ON DELETE CASCADE,
    lottery_id INTEGER REFERENCES Lotteries(id) ON DELETE CASCADE

)
''')

connection.commit()


def execute_query(query, params=()):
    with connection as con:
        cur = con.cursor()
        try:
            cur.execute(query, params)
            con.commit()
            return cur
        except Exception as e:
            print(f"Error executing query: {e}")
            return None


def add_user(tg_id, username):
    execute_query('''
        INSERT INTO Users (telegram_id, username) VALUES (?, ?)
        ''', (tg_id, username))


def is_user(tg_id):
    result = execute_query(f'''
        SELECT COUNT(*)  FROM Users WHERE telegram_id = ?
        ''', (tg_id,))
    return result.fetchone()[0] > 0


def get_user(tg_id):
    result = execute_query(f'''
    SELECT *  FROM Users WHERE telegram_id = ?
    ''', (tg_id,))
    return result.fetchone()


def add_channel(channel_id, tg_id):
    if is_user(tg_id):
        user_id = get_user(tg_id)[0]
        execute_query(f'''
                INSERT INTO Channels (id, channel_admin) VALUES (?, ?)
        ''', (channel_id, user_id))


def get_channel(channel_id):
    result = execute_query(f'''
    SELECT *  FROM Channels WHERE id = ?
    ''', (channel_id,))
    return result.fetchone()


def get_channels(tg_id):
    result = execute_query(f'''
        SELECT id  FROM Channels WHERE channel_admin = ?
        ''', (tg_id,))
    return result.fetchall()


def del_channel(channel_id):
    execute_query(f'''
           DELETE  FROM Channels WHERE id = ?
           ''', (channel_id,))


def add_lottery_to_db(text, author_id, date_end):
    execute_query(f'''
                INSERT INTO Lotteries (context_lottery, author_lot, date_end_of_lot) VALUES (?, ?, ?)
        ''', (text, author_id, date_end))


def get_lotteries(author_id):
    result = execute_query(f'''
        SELECT *  FROM Lotteries WHERE author_lot = ?
        ''', (author_id,))
    return result.fetchall()


def get_lottery(lottery_id):
    result = execute_query(f'''
        SELECT *  FROM Lotteries WHERE id = ?
        ''', (lottery_id,))
    return result.fetchone()


def join_user_to_lottery(user_id, lottery_id):
    execute_query(f'''
        INSERT INTO UsersLotteries (user_id, lottery_id) VALUES (?, ?)''',
                  (user_id, lottery_id))


def add_lottery_to_channel(lottery_id, channel_id):
    execute_query(f'''
            INSERT INTO ChannelsLotteries (channel_id, lottery_id) VALUES (?, ?)''',
                  (channel_id, lottery_id))


def check_lottery_in_channel(lottery_id, channel_id):
    result = execute_query(f'''
            SELECT COUNT(*) FROM ChannelsLotteries WHERE channel_id = ? AND lottery_id = ?''',
                           (channel_id, lottery_id))
    return result.fetchone()[0] > 0


def check_user_in_lottery(lottery_id, user_id):
    result = execute_query(f'''
            SELECT COUNT(*) FROM UsersLotteries WHERE user_id = ? AND lottery_id = ?''',
                           (user_id, lottery_id))
    return result.fetchone()[0] > 0


def get_channels_with_lottery(lottery_id):
    result = execute_query(f'''
            SELECT channel_id FROM ChannelsLotteries WHERE lottery_id = ?''', (lottery_id,)
                           )
    return result.fetchall()


def get_users_in_lottery(lottery_id):
    result = execute_query(f'''
                SELECT user_id FROM UsersLotteries WHERE lottery_id = ?''', (lottery_id,)
                           )
    return result.fetchall()


def delete_lottery(lottery_id):
    execute_query(f'''
                    DELETE FROM Lotteries WHERE id = ?''', (lottery_id,)
                           )


def change_lottery_status(lottery_id, status):
    execute_query(f'''
                UPDATE Lotteries SET is_active=? WHERE id=?''',
                  (status, lottery_id))
