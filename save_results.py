import csv
import os
from datetime import datetime

def save_result(color, result, user, vision_type):
    file_exists = os.path.isfile("results.csv")

    with open("results.csv", "a", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Time", "User", "Color", "Result", "Vision Type"])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user,
            color,
            result,
            vision_type
        ])