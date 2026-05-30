"""
Task 4 — Quiz Grading
Grades student answers against the answer key.
"""

from dataclasses import dataclass, field
from typing import Optional
from task3_bubble_reader import StudentAnswers
from task1_qr_decoder import AnswerKey


@dataclass
class GradeReport:
    student_name: str = "Unknown"
    reg_no: str = "Unknown"
    quiz_set: str = "A"
    correct: int = 0
    incorrect: int = 0
    unattempted: int = 0
    invalid: int = 0
    total_marks: float = 0.0
    max_marks: float = 0.0
    percentage: float = 0.0
    grade: str = "F"
    breakdown: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "student_name": self.student_name,
            "reg_no": self.reg_no,
            "quiz_set": self.quiz_set,
            "correct": self.correct,
            "incorrect": self.incorrect,
            "unattempted": self.unattempted,
            "invalid": self.invalid,
            "total_marks": self.total_marks,
            "max_marks": self.max_marks,
            "percentage": round(self.percentage, 1),
            "grade": self.grade,
            "breakdown": self.breakdown,
        }


def _letter_grade(pct: float) -> str:
    if pct >= 90: return "A+"
    if pct >= 80: return "A"
    if pct >= 70: return "B"
    if pct >= 60: return "C"
    if pct >= 50: return "D"
    return "F"


def grade_quiz(
    student_answers: StudentAnswers,
    answer_key: AnswerKey,
    student_name: str = "Unknown",
    reg_no: str = "Unknown",
) -> GradeReport:

    report = GradeReport(
        student_name=student_name,
        reg_no=reg_no,
        quiz_set=answer_key.quiz_set,
    )

    all_questions = []
    for q, correct in answer_key.part1.items():
        student_ans = student_answers.part1.get(q)
        all_questions.append(("Part1_" + q, correct, student_ans))

    for q, correct in answer_key.part2.items():
        student_ans = student_answers.part2.get(q)
        all_questions.append(("Part2_" + q, correct, student_ans))

    report.max_marks = float(len(all_questions))
    marks = 0.0

    for label, correct, student_ans in all_questions:
        if student_ans is None:
            report.unattempted += 1
            report.breakdown[label] = "unattempted"
        elif student_ans == "INVALID":
            report.invalid += 1
            report.breakdown[label] = "invalid"
        elif student_ans == correct:
            report.correct += 1
            marks += 1.0
            report.breakdown[label] = "correct"
        else:
            report.incorrect += 1
            marks -= answer_key.negative_marking
            report.breakdown[label] = "incorrect"

    report.total_marks = max(0.0, marks)
    report.percentage = (report.total_marks / report.max_marks * 100) if report.max_marks > 0 else 0.0
    report.grade = _letter_grade(report.percentage)

    return report


def print_report(report: GradeReport):
    print(f"\n{'='*45}")
    print(f"  Student: {report.student_name}")
    print(f"  Reg No:  {report.reg_no}")
    print(f"  Set:     {report.quiz_set}")
    print(f"{'='*45}")
    print(f"  Score:   {report.total_marks}/{report.max_marks}")
    print(f"  Percent: {report.percentage:.1f}%")
    print(f"  Grade:   {report.grade}")
    print(f"  Correct: {report.correct}  Wrong: {report.incorrect}  Skipped: {report.unattempted}")
    print(f"{'='*45}\n")


if __name__ == "__main__":
    print("Run app.py to use the full system.")