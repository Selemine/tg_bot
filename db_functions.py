from datetime import datetime
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

def create_tables():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    logger.debug("Создание таблиц, если они не существуют")
    
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student TEXT,
            subject TEXT,
            teacher_name TEXT,
            group_number TEXT,  
            date TEXT,
            mark INTEGER
        )
    """)
    
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS groups (
            group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_number TEXT,
            leader_name TEXT
        )
    """)
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS members (
            member_id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_number TEXT,
            member_name TEXT
        )
    """)
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT,
            teacher_name TEXT
        )
    """)
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS group_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_number TEXT,
            subject_name TEXT
        )
    """)
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_name TEXT PRIMARY KEY,
            chat_id INTEGER
        )
    """)
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS student_marks (
            student_name TEXT PRIMARY KEY,
            mark TEXT
        )
    """)

    conn.commit()
    conn.close()

def connect_to_database():
    """Подключение к базе данных SQLite."""
    return sqlite3.connect('database.db')  # Укажите путь к вашей базе данных

def create_group(group_number, leader_name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        logger.debug(f"Попытка создания группы {group_number} с лидером {leader_name}")
        cursor.execute("INSERT INTO groups (group_number, leader_name) VALUES (?, ?)", (group_number, leader_name))
        conn.commit()
        logger.debug(f"Группа {group_number} успешно создана с лидером {leader_name}")

        logger.debug(f"Попытка добавления старосты {leader_name} в таблицу members для группы {group_number}")
        cursor.execute("INSERT INTO members (member_name, group_number) VALUES (?, ?)", (leader_name, group_number))
        conn.commit()
        logger.debug(f"Староста {leader_name} успешно добавлен в таблицу members в группу {group_number}")
    except sqlite3.IntegrityError as e:
        logger.error(f"Ошибка при создании группы: {e}")
    finally:
        conn.close()

def add_member(member_name, group_number):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO members (member_name, group_number) VALUES (?, ?)", (member_name, group_number))
    conn.commit()
    conn.close()

def add_subject(subject_name, teacher_name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subjects (subject_name, teacher_name) VALUES (?, ?)", (subject_name, teacher_name))
    conn.commit()
    conn.close()

def get_subjects():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT subject_name FROM subjects")
    subjects = cursor.fetchall()
    conn.close()
    return [subject[0] for subject in subjects]

def get_group_subjects(group_number):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT subject_name FROM group_subjects WHERE group_number = ?", (group_number,))
    subjects = cursor.fetchall()
    conn.close()
    return [subject[0] for subject in subjects]

def get_all_subjects_with_teachers():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT subject_name, teacher_name FROM subjects")
    subjects = cursor.fetchall()
    conn.close()
    return subjects 

def add_group_to_subject(group_number, subject_name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO group_subjects (group_number, subject_name) VALUES (?, ?)", (group_number, subject_name))
        conn.commit()
        logger.debug(f"Группа {group_number} добавлена к дисциплине {subject_name}")
    except sqlite3.IntegrityError as e:
        logger.error(f"Ошибка при добавлении группы к дисциплине: {e}")
    finally:
        conn.close()

def get_teacher_by_subject(subject_name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT teacher_name FROM subjects WHERE subject_name = ?", (subject_name,))
    teacher = cursor.fetchone()
    conn.close()
    return teacher[0] if teacher else None

def get_teacher_chat_id(teacher_name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM teachers WHERE teacher_name = ?", (teacher_name,))
    teacher = cursor.fetchone()
    conn.close()
    return teacher[0] if teacher else None

def add_teacher(teacher_name, chat_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO teachers (teacher_name, chat_id) 
        VALUES (?, ?)
        ON CONFLICT(teacher_name) DO UPDATE SET chat_id = ?
    """, (teacher_name, chat_id, chat_id))
    conn.commit()
    conn.close()

def update_teacher_chat_id(teacher_name, chat_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE teachers SET chat_id = ? WHERE teacher_name = ?", (chat_id, teacher_name))
    conn.commit()
    conn.close()

def get_leader_chat_id(group_number):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT leader_name FROM groups WHERE group_number = ?", (group_number,))
        leader = cursor.fetchone()
        logger.debug(f"Староста группы {group_number}: {leader}")

        if leader:
            cursor.execute("SELECT chat_id FROM teachers WHERE teacher_name = ?", (leader[0],))
            chat_id = cursor.fetchone()
            logger.debug(f"Chat ID старосты: {chat_id}")

            return chat_id[0] if chat_id else None
    except sqlite3.IntegrityError as e:
        logger.error(f"Ошибка при получении chat ID старосты: {e}")
    finally:
        conn.close()
    return None

def get_student_group(full_name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT group_number FROM members WHERE member_name = ?", (full_name,))
        group = cursor.fetchone()
        return group[0] if group else None
    except sqlite3.Error as e:
        logger.error(f"Ошибка при извлечении группы для студента {full_name}: {e}")
        return None
    finally:
        conn.close()

def get_student_group_info(full_name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    logger.debug(f"Поиск информации о группе для: {full_name}")

    cursor.execute("""
        SELECT group_number
        FROM members
        WHERE member_name = ?
    """, (full_name,))
    group_numbers = cursor.fetchall()

    logger.debug(f"Группы, найденные для студента {full_name}: {group_numbers}")

    if group_numbers:
        groups_info = []
        for group_number in group_numbers:
            group_number = group_number[0]

            cursor.execute("""
                SELECT leader_name
                FROM groups
                WHERE group_number = ?
            """, (group_number,))
            leader = cursor.fetchone()

            logger.debug(f"Староста группы {group_number}: {leader}")

            if leader:
                leader = leader[0]
            else:
                logger.debug(f"Староста не найден для группы {group_number}")
                leader = "Нет старосты"

            cursor.execute("""
                SELECT member_name
                FROM members
                WHERE group_number = ?
            """, (group_number,))
            members = cursor.fetchall()

            logger.debug(f"Участники группы {group_number}: {members}, Староста: {leader}")

            number_of_members = len(members)
            group_info_text = f"     <u>{group_number}</u>     \n"
            group_info_text += "\n"
            group_info_text += f"<i>Список группы ({number_of_members})</i>\n"
            group_info_text += "\n"
            sorted_members = sorted([member[0] for member in members])
            for member in sorted_members:
                if member == leader:
                    group_info_text += f"<b>{member}</b>  👨‍🎓\n"
                else:
                    group_info_text += f"{member}\n"
            groups_info.append(group_info_text)

        conn.close()
        return "\n\n".join(groups_info)

    conn.close()
    return None

def is_group_already_joined(group_number, subject):
    conn = sqlite3.connect('database.db')  
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM group_subjects WHERE group_number = ? AND subject_name = ?", (group_number, subject))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def check_table_exists():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='group_subjects'")
    table = cursor.fetchone()
    conn.close()
    if table:
        print("Таблица group_subjects существует")
    else:
        print("Таблица group_subjects не существует")

check_table_exists()

def get_subjects_for_group(group_number):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = """
        SELECT subject_name
        FROM group_subjects
        WHERE group_number = ?
    """
    cursor.execute(query, (group_number,))
    subjects = cursor.fetchall()
    
    conn.close()

    # Возвращаем список названий предметов
    return [subject[0] for subject in subjects]

def get_subjects_by_teacher(teacher_name):
    all_subjects_with_teachers = get_all_subjects_with_teachers()
    subjects = [subject for subject, teacher in all_subjects_with_teachers if teacher == teacher_name]
    return subjects

def get_groups_by_subject(subject_name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        logger.debug(f"Получение списка групп, присоединенных к дисциплине: {subject_name}")
        cursor.execute("""
            SELECT DISTINCT group_number
            FROM group_subjects
            WHERE subject_name = ?
        """, (subject_name,))
        result = cursor.fetchall()
        logger.debug(f"Найдены группы для дисциплины {subject_name}: {result}")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении групп для дисциплины {subject_name}: {e}")
        return []
    finally:
        conn.close()
    
    # Преобразование результата в список номеров групп
    return [row[0] for row in result]

def get_students_by_group(group_number):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        logger.info(f"Извлечение студентов для группы: {group_number}")  
        cursor.execute("SELECT member_name FROM members WHERE group_number = ?", (group_number,))
        students = cursor.fetchall()
        if not students:
            logger.warning(f"Для группы {group_number} не найдено студентов.")
        else:
            logger.info(f"Найдено студентов: {len(students)}. Список: {[student[0] for student in students]}")

        return [student[0] for student in students]  
    except sqlite3.Error as e:
        logger.error(f"Ошибка при извлечении студентов для группы {group_number}: {e}")
        return []
    finally:
        conn.close()
        logger.info(f"Соединение с базой данных закрыто.")

def mark_student(student_name, mark):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        current_date = datetime.now().strftime('%Y-%m-%d')

        cursor.execute("""
            INSERT INTO student_marks (student_name, mark)
            VALUES (?, ?)
            ON CONFLICT(student_name) DO UPDATE SET mark = ?, date = ?
        """, (student_name, mark, mark, current_date))
        conn.commit()
        logger.debug(f"Оценка {mark} для студента {student_name} успешно сохранена с датой {current_date}.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при сохранении оценки для студента {student_name}: {e}")
    finally:
        conn.close()

def save_mark(student_name, subject, mark):
    try:
        current_date = datetime.now().strftime('%Y-%m-%d')
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO marks (student, subject, date, mark) 
            VALUES (?, ?, ?, ?)
        """, (student_name, subject, current_date, mark))
        connection.commit()
        connection.close()
        logger.debug(f"Оценка {mark} для студента {student_name} по предмету {subject} успешно сохранена с датой {current_date}.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении оценки для студента {student_name}: {e}")

def add_student_column_if_needed():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(marks)")
    columns = cursor.fetchall()
    if not any(col[1] == 'student' for col in columns):
        logger.debug("Столбец 'student' отсутствует. Добавляем его в таблицу 'marks'.")
        cursor.execute("ALTER TABLE marks ADD COLUMN student TEXT")
        conn.commit()
    
    conn.close()

def get_student_grades(student_name):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        logger.debug(f"Запрос оценок для студента: {student_name}")
        cursor.execute("SELECT subject, date, mark FROM marks WHERE student = ?", (student_name,))
        grades = cursor.fetchall()
        logger.debug(f"Найдено оценок для студента {student_name}: {grades}")
        return grades  
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении оценок для студента {student_name}: {e}")
        return []
    finally:
        conn.close()

def get_group_subjects_with_grades(group_number):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT subject_name, student, mark, date 
        FROM marks 
        WHERE group_number = ?
    """, (group_number,))
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return []
    
    subjects_with_grades = {}
    for subject, student, mark, date in rows:
        if subject not in subjects_with_grades:
            subjects_with_grades[subject] = []
        subjects_with_grades[subject].append({
            'student': student,
            'mark': mark,
            'date': date
        })
    
    return subjects_with_grades

def get_marks_for_subject(subject, group=None, student_name=None):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        logger.debug(f"Запрос оценок по предмету {subject} для студента {student_name}")
        
        if student_name:
            query = """
                SELECT date, mark
                FROM marks
                WHERE subject = ? AND student = ?
                ORDER BY date DESC
            """
            cursor.execute(query, (subject, student_name))
        elif group:
            query = """
                SELECT date, mark
                FROM marks
                WHERE subject = ? AND group_number = ?
                ORDER BY date DESC
            """
            cursor.execute(query, (subject, group))
        else:
            query = """
                SELECT date, mark
                FROM marks
                WHERE subject = ?
                ORDER BY date DESC
            """
            cursor.execute(query, (subject,))
        
        marks_info = cursor.fetchall()
        conn.close()

        if not marks_info:
            logger.debug("Оценки не найдены.")
            return None
        return [{"date": mark[0], "mark": mark[1]} for mark in marks_info]

    except sqlite3.Error as e:
        logger.error(f"Ошибка при выполнении запроса к базе данных: {e}")
        return None
