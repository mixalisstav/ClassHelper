import sqlite3 as sql

conn = sql.connect('classroom.db')
c = conn.cursor()
question="something"
frequency=5
student_name = input("Enter student name: ")
questions_dict = {}
questions_dict[question] = frequency
c.execute(f'''INSERT INTO students WHERE name={student_name} VALUES (questions)''', (questions_dict,))

c.close()
conn.close()
