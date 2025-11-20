import sqlite3 as sql

conn = sql.connect('classroom.db')
c = conn.cursor()
question="something"
frequency=5
student_name = input("Enter student name: ")
questions_dict = {}
questions_dict[question] = frequency

c.execute(
    "INSERT INTO students (name, questions) VALUES (?, ?)",
    (student_name, str(questions_dict))
)
conn.commit()
c.close()
conn.close()


import json
if __name__ == "__main__":
    conn = sql.connect('classroom.db')
    c = conn.cursor()
    c.execute("SELECT questions FROM students WHERE name=?", (student_name,))
    rows = c.fetchall()
    print(rows)    
    c.close()
    conn.close()
    questions_data = rows[0][0]
    questions_dict = json.loads(questions_data.replace("'", '"'))
    print(questions_dict)