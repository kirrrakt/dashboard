"""Генерація навчального CSV з успішністю студентів (students.csv)."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

GROUPS = ["КБ-31", "КБ-32", "ІТ-21", "ІТ-22"]
SUBJECTS = ["Алгоритмізація", "Математика", "Фізика", "Англійська мова", "Історія", "Бази даних"]
SEMESTERS = [1, 2, 3, 4]
# Предмети з однієї «групи» залежать від спільної здібності студента -> виникають кореляції
TECH = {"Алгоритмізація", "Математика", "Фізика", "Бази даних"}

rows = []
sid = 1
for g in GROUPS:
    for _ in range(25):
        tech_skill = rng.normal(75, 10)
        hum_skill = rng.normal(75, 10)
        name = f"Студент {sid:03d}"
        for sem in SEMESTERS:
            for subj in SUBJECTS:
                base = tech_skill if subj in TECH else hum_skill
                grade = base + rng.normal(0, 6) + (sem - 2.5) * 0.8
                rows.append((sid, name, g, sem, subj, int(np.clip(round(grade), 35, 100))))
        sid += 1

df = pd.DataFrame(rows, columns=["student_id", "student", "group", "semester", "subject", "grade"])
df.to_csv("students.csv", index=False, encoding="utf-8")
print(f"Збережено students.csv: {len(df)} рядків")
