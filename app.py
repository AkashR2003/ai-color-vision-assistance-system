from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
from PIL import Image
import numpy as np
from object_detection import detect_object
import os
from ml_model import predict_confusion
from save_results import save_result
import base64
from color_ai import predict_color
import csv

app = Flask(__name__)
app.secret_key = "secret123"
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024


# ---------------- DATABASE ----------------
def create_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    conn.commit()
    conn.close()


create_db()


# ---------------- HISTORY ----------------
def get_user_results(username):
    results = []

    if not os.path.exists("results.csv"):
        return results

    with open("results.csv", newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["User"] == username:
                results.append(row)

    return results


# ---------------- COLOR BLIND SIMULATION ----------------
def simulate_color_blindness(color_name, vision_type):
    if vision_type == "Protanopia":
        mapping = {
            "red": "brown",
            "green": "brown",
            "dark green": "dark brown",
            "light green": "yellowish",
            "yellow": "light brown"
        }

    elif vision_type == "Deuteranopia":
        mapping = {
            "green": "brown",
            "red": "dark yellow",
            "dark green": "dark brown",
            "light green": "yellow"
        }

    elif vision_type == "Tritanopia":
        mapping = {
            "blue": "green",
            "yellow": "pink",
            "dark blue": "dark green"
        }

    else:
        return color_name

    return mapping.get(color_name.lower(), color_name)


# ---------------- SHADE FUNCTION ----------------
def get_shade_name(r, g, b):
    avg = (r + g + b) / 3
    base = predict_color(r, g, b)

    if avg < 80:
        shade = "dark"
    elif avg > 180:
        shade = "light"
    else:
        shade = ""

    if shade:
        return f"{shade} {base}"
    return base


# ---------------- COLOR ----------------
def get_dominant_color(image_path):
    img = Image.open(image_path)
    img = img.resize((150, 150))

    data = np.array(img)
    data = data.reshape((-1, 3))
    data = data[np.sum(data, axis=1) < 700]

    from collections import Counter
    most_common = Counter([tuple(p) for p in data]).most_common(1)[0][0]

    return most_common


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return "Invalid login"

    return render_template("index.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    data = get_user_results(session["user"])

    test_folder = os.path.join("static", "test_images")
    test_images = []

    if os.path.exists(test_folder):
        test_images = [
            "test_images/" + img
            for img in os.listdir(test_folder)
            if img.lower().endswith((".jpg", ".jpeg", ".png"))
        ]

    return render_template(
        "dashboard.html",
        user=session["user"],
        result=session.get("result"),
        image=session.get("image"),
        history=data,
        test_images=test_images
    )


# ---------------- SET TYPE ----------------
@app.route("/set_type", methods=["POST"])
def set_type():
    session["vision_type"] = request.form["type"]
    return redirect("/dashboard")

# ---------------- COLOR BLIND TEST ----------------
@app.route("/test", methods=["GET", "POST"])
def test():

    if "user" not in session:
        return redirect("/")

    test_images = [
        {"file": "test_images/8.jpg", "answer": "8"},
        {"file": "test_images/45.jpg", "answer": "45"},
        {"file": "test_images/74.jpg", "answer": "74"},
        {"file": "test_images/Ishihara-color-blind-test-12.jpg", "answer": "12"},
        {"file": "test_images/Ishihara-color-blind-test-26.jpg", "answer": "26"},
        {"file": "test_images/Ishihara-color-blind-test-96.jpg", "answer": "96"}
    ]

    if request.method == "POST":

        score = 0

        for i, img in enumerate(test_images):
            user_answer = request.form.get(f"answer{i}", "").strip()

            if user_answer == img["answer"]:
                score += 1

        if score >= 5:
            vision_type = "Normal"

        elif score >= 3:
            vision_type = "Deuteranopia"

        elif score >= 1:
            vision_type = "Protanopia"

        else:
            vision_type = "Tritanopia"

        session["vision_type"] = vision_type
        session["test_score"] = score

        return redirect("/dashboard")

    return render_template("test.html", test_images=test_images)

# ---------------- IMAGE UPLOAD ----------------
@app.route("/upload", methods=["POST"])
def upload():
    if "user" not in session:
        return redirect("/")

    file = request.files["image"]

    filepath = os.path.join("static", file.filename)
    file.save(filepath)

    r, g, b = get_dominant_color(filepath)
    color_name = get_shade_name(r, g, b)

    objects = detect_object(filepath)
    object_name = objects[0] if objects else "Unknown object"

    vision = session.get("vision_type", "Normal")
    seen_color = simulate_color_blindness(color_name, vision)

    result = f"Detected {object_name} with {color_name} color."

    if vision != "Normal":
        result += f"\nYou may see it as {seen_color}."
        result += "\nThis color may not be clearly visible for you."

    session["result"] = result
    session["image"] = "/" + filepath

    save_result(color_name, result, session["user"], vision)

    return redirect("/dashboard")


# ---------------- CAMERA UPLOAD ----------------
@app.route("/camera_upload", methods=["POST"])
def camera_upload():
    if "user" not in session:
        return jsonify({"result": "Not logged in"})

    try:
        data = request.get_json()

        if not data or "image" not in data:
            return jsonify({"result": "No image received"})

        image_data = data["image"]
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        filepath = "static/capture.png"

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        r, g, b = get_dominant_color(filepath)
        color_name = get_shade_name(r, g, b)

        objects = detect_object(filepath)
        object_name = objects[0] if objects else "Unknown object"

        vision = session.get("vision_type", "Normal")
        seen_color = simulate_color_blindness(color_name, vision)

        result = f"Detected {object_name} with {color_name} color."

        if vision != "Normal":
            result += f"\nYou may see it as {seen_color}."
            result += "\nThis color may not be clearly visible for you."

        save_result(color_name, result, session["user"], vision)

        return jsonify({"result": result})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"result": "Error processing image"})


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)