import sqlite3

connection = sqlite3.connect('database.db')  
cursor = connection.cursor()


cursor.execute("""
    SELECT student, subject, date, mark 
    FROM marks;
""")
marks = cursor.fetchall()


if marks:
    print("ФИО студента | Дисциплина | Дата | Оценка")
    print("-" * 50)
    for mark in marks:
        student, subject, date, mark_value = mark
        print(f"{student} | {subject} | {date} | {mark_value}")
else:
    print("Нет данных в таблице marks")


connection.close()
