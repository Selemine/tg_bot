import sqlite3
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

def get_student_marks():



    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(marks)")
    print(cursor.fetchall())
    conn.close()
    print("12312312412")
    # Проверка существования базы данных
    if not os.path.exists("database.db"):
        print("База данных не существует.")
        return

    # Попытка подключения к базе данных
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        logger.debug("Запрос оценок студентов")

        # Выполнение запроса для получения всех оценок студентов с дисциплинами и датами
        cursor.execute("""
            SELECT student, subject, date, mark
            FROM marks
            ORDER BY student, date DESC
        """)
        marks = cursor.fetchall()

        if not marks:
            logger.debug("Оценки не найдены.")
            print("Оценки не найдены.")
            return

        result = []
        for mark in marks:
            student, subject, date, mark_value = mark
            result.append(f"ФИО: {student} | Дисциплина: {subject} | Дата: {date} | Оценка: {mark_value}")

        # Выводим результаты в терминал
        for line in result:
            print(line)

    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении оценок студентов: {e}")
        print("Произошла ошибка при выполнении запроса.")
    
    finally:
        conn.close()

def main():
    get_student_marks()

if __name__ == "__main__":
    main()
