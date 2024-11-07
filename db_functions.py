import sqlite3

# Подключение к базе данных SQLite
def connect_db():
    return sqlite3.connect('attendance_grades.db')

# Функция для создания таблиц (если они не существуют)
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        full_name TEXT,
        status TEXT,
        group_number TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS groups (
        group_number TEXT PRIMARY KEY,
        leader_id INTEGER,
        FOREIGN KEY (leader_id) REFERENCES users(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS members (
        user_id INTEGER,
        group_number TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (group_number) REFERENCES groups(group_number)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY,
        name TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        subject_id INTEGER,
        user_id INTEGER,
        date TEXT,
        status TEXT,
        FOREIGN KEY (subject_id) REFERENCES subjects(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grades (
        subject_id INTEGER,
        user_id INTEGER,
        grade TEXT,
        FOREIGN KEY (subject_id) REFERENCES subjects(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    conn.commit()
    conn.close()

# Функция для добавления пользователя
def add_user(full_name, status, group_number=None):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (full_name, status, group_number) VALUES (?, ?, ?)", (full_name, status, group_number))
    conn.commit()
    conn.close()

# Функция для получения группы по ФИО
def get_user_group(full_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT group_number FROM users WHERE full_name = ?", (full_name,))
    group = cursor.fetchone()
    conn.close()
    return group[0] if group else None

# Функция для создания группы
def create_group(group_number, leader_full_name):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO groups (group_number, leader_id) SELECT ?, id FROM users WHERE full_name = ?", (group_number, leader_full_name))
    conn.commit()
    conn.close()

# Функция для добавления участников в группу
def add_member(user_full_name, group_number):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE full_name = ?", (user_full_name,))
    user_id = cursor.fetchone()
    if user_id:
        cursor.execute("INSERT INTO members (user_id, group_number) VALUES (?, ?)", (user_id[0], group_number))
        conn.commit()
    conn.close()
