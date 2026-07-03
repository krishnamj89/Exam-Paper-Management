from flask import Flask, request, jsonify, send_from_directory
import pandas as pd
import csv
import os
from datetime import datetime
from pdf_builder import build_paper_pdf

app = Flask(__name__)

BANK = "questions.csv"
PAPERS_DIR = "papers"
os.makedirs(PAPERS_DIR, exist_ok=True)

FIELDS = ["id", "topic", "difficulty", "marks", "question", "answer"]


class Question:
    def __init__(self, id, topic, difficulty, marks, question, answer):
        self.id = id
        self.topic = topic.strip().title()
        self.difficulty = difficulty.strip().capitalize()
        self.marks = int(marks)
        self.question = question.strip()
        self.answer = answer.strip()

    def to_dict(self):
        return {"id": self.id, "topic": self.topic, "difficulty": self.difficulty,
                "marks": self.marks, "question": self.question, "answer": self.answer}


def load_questions():
    if not os.path.exists(BANK):
        return []
    try:
        with open(BANK, newline="", encoding="utf-8") as f:
            return [Question(**row) for row in csv.DictReader(f)]
    except Exception:
        return []


def save_questions(questions):
    with open(BANK, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for q in questions:
            w.writerow(q.to_dict())


def next_id(questions):
    if not questions:
        return "Q001"
    return f"Q{int(questions[-1].id[1:]) + 1:03d}"


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/questions", methods=["GET"])
def get_questions():
    questions = load_questions()
    topic = request.args.get("topic", "").strip().lower()
    difficulty = request.args.get("difficulty", "").strip().lower()
    if topic:
        questions = [q for q in questions if q.topic.lower() == topic]
    if difficulty:
        questions = [q for q in questions if q.difficulty.lower() == difficulty]
    return jsonify([q.to_dict() for q in questions])


@app.route("/questions", methods=["POST"])
def add_question():
    data = request.json
    questions = load_questions()
    q = Question(next_id(questions), data["topic"], data["difficulty"],
                 data["marks"], data["question"], data["answer"])
    questions.append(q)
    save_questions(questions)
    return jsonify(q.to_dict()), 201


@app.route("/topics", methods=["GET"])
def get_topics():
    questions = load_questions()
    df = pd.DataFrame([q.to_dict() for q in questions]) if questions else pd.DataFrame()
    topics = sorted(df["topic"].unique().tolist()) if not df.empty else []
    return jsonify(topics)


@app.route("/paper", methods=["POST"])
def save_paper():
    data = request.json
    ids = data.get("ids", [])
    exam = data.get("exam_name", "Exam")
    subject = data.get("subject", "")
    teacher = data.get("teacher", "")

    questions = load_questions()
    selected = [q for q in questions if q.id in ids]

    if not selected:
        return jsonify({"error": "No questions selected"}), 400

    df = pd.DataFrame([q.to_dict() for q in selected])
    total = df["marks"].sum()

    filename = f"{exam.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    path = os.path.join(PAPERS_DIR, filename)

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Exam", exam])
        w.writerow(["Subject", subject])
        w.writerow(["Teacher", teacher])
        w.writerow(["Total Marks", total])
        w.writerow([])
        w.writerow(["#", "ID", "Topic", "Difficulty", "Marks", "Question", "Answer"])
        for i, q in enumerate(selected, 1):
            w.writerow([i, q.id, q.topic, q.difficulty, q.marks, q.question, q.answer])

    return jsonify({"message": f"Paper saved as {filename}", "total_marks": int(total)})


@app.route("/paper/pdf", methods=["POST"])
def save_paper_pdf():
    data = request.json
    meta = data.get("meta", {})
    sections = data.get("sections", [])

    if not sections:
        return jsonify({"error": "No sections provided"}), 400

    exam_name = meta.get("exam_title", "Exam")
    filename = f"{exam_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    path = os.path.join(PAPERS_DIR, filename)

    build_paper_pdf(path, meta, sections)

    return jsonify({"message": f"PDF saved as {filename}", "filename": filename})


@app.route("/papers/<path:filename>")
def download_paper(filename):
    return send_from_directory(PAPERS_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5050)
