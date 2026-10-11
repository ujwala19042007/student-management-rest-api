from flask import Flask, jsonify, request
import sqlite3

app = Flask(__name__)

DATABASE = "students.db"


# Database connection
def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create database table
def init_db():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            course TEXT
        )
    """)

    conn.commit()
    conn.close()


# Home API
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Student Management API",
        "available_methods": [
            "GET", "POST", "PUT", "DELETE"
        ]
    }), 200


# POST - Add student
@app.route("/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON is required"}), 400

    name = data.get("name")
    age = data.get("age")
    course = data.get("course")

    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Name is required"}), 400

    if age is not None:
        if type(age) is not int or not 1 <= age <= 120:
            return jsonify({"error": "Invalid age"}), 400

    if course is not None:
        if not isinstance(course, str) or not course.strip():
            return jsonify({"error": "Invalid course"}), 400

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO students (name, age, course) VALUES (?, ?, ?)",
        (name.strip(), age, course.strip() if course else None)
    )

    student_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Student added successfully",
        "id": student_id
    }), 201


# GET - View all students
@app.route("/students", methods=["GET"])
def get_students():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM students ORDER BY id"
    ).fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows]), 200


# GET - View one student
@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(dict(row)), 200


# PUT - Update student
@app.route("/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({"error": "Valid JSON is required"}), 400

    allowed = {"name", "age", "course"}

    if not set(data).issubset(allowed):
        return jsonify({"error": "Invalid field"}), 400

    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    if row is None:
        conn.close()
        return jsonify({"error": "Student not found"}), 404

    name = data.get("name", row["name"])
    age = data.get("age", row["age"])
    course = data.get("course", row["course"])

    if not isinstance(name, str) or not name.strip():
        conn.close()
        return jsonify({"error": "Invalid name"}), 400

    if age is not None:
        if type(age) is not int or not 1 <= age <= 120:
            conn.close()
            return jsonify({"error": "Invalid age"}), 400

    if course is not None:
        if not isinstance(course, str) or not course.strip():
            conn.close()
            return jsonify({"error": "Invalid course"}), 400

    conn.execute(
        """UPDATE students
           SET name = ?, age = ?, course = ?
           WHERE id = ?""",
        (
            name.strip(),
            age,
            course.strip() if course else None,
            student_id
        )
    )

    conn.commit()
    conn.close()

    return jsonify({"message": "Student updated successfully"}), 200


# DELETE - Remove student
@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn = get_connection()

    cursor = conn.execute(
        "DELETE FROM students WHERE id = ?",
        (student_id,)
    )

    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Student not found"}), 404

    return jsonify({"message": "Student deleted successfully"}), 200


# Handle missing routes
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404


# Handle unsupported methods
@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405


# Run application
init_db()
if __name__ == "__main__":
    app.run(debug=True)
