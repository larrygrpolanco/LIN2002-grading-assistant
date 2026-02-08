#!/usr/bin/env python3
"""
Create Golden Examples CSV for LLM Training

Creates a curated dataset of 10 examples (5 from Module 2, 5 from Module 3)
with more high-grade examples as requested.
"""

import csv
import json
import random
from pathlib import Path

# Configuration
DATASET_PATH = "data/movie_grading_dataset.csv"
MODULE_DETAILS_PATH = "data/module_details.csv"
OUTPUT_PATH = "data/training_examples.csv"

# Grade threshold
HIGH_GRADE_THRESHOLD = 85

# Set seed for reproducibility
random.seed(42)


def load_data():
    """Load essays and module details."""

    # Load essays
    essays = []
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            with open(DATASET_PATH, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    try:
                        if row["Grade out of 100"] and row["Grade out of 100"].strip():
                            grade = float(row["Grade out of 100"])
                            module = int(row["Module"])
                            if module in [2, 3]:
                                essays.append(
                                    {
                                        "id": i,
                                        "module": module,
                                        "essay": row["Student Essay"],
                                        "grade": grade,
                                        "feedback": row["Teacher Feedback"],
                                    }
                                )
                    except (ValueError, KeyError):
                        continue
            break
        except UnicodeDecodeError:
            continue

    # Load module details
    modules = {}
    for encoding in encodings:
        try:
            with open(MODULE_DETAILS_PATH, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        module_num = int(row["Module"])
                        if module_num in [2, 3]:
                            modules[module_num] = {
                                "movie": row["Movie"],
                                "question": row["Essay Question"],
                                "details": row["Movie-details"],
                            }
                    except (ValueError, KeyError):
                        continue
            break
        except UnicodeDecodeError:
            continue

    return essays, modules


def select_examples(essays, module_num, num_examples=5):
    """
    Select examples for a module with more high-grade examples.
    Distribution: 3 high-grade, 2 low-grade (or similar based on availability)
    """
    module_essays = [e for e in essays if e["module"] == module_num]

    # Separate by grade
    high_grades = [e for e in module_essays if e["grade"] >= HIGH_GRADE_THRESHOLD]
    low_grades = [e for e in module_essays if e["grade"] < HIGH_GRADE_THRESHOLD]

    print(
        f"Module {module_num}: {len(high_grades)} high-grade, {len(low_grades)} low-grade essays"
    )

    selected = []

    # Select 3 high-grade examples with diversity
    if len(high_grades) >= 3:
        # Sort by grade and pick from different parts of high-grade range
        high_grades_sorted = sorted(high_grades, key=lambda x: x["grade"], reverse=True)
        # Pick: 1 near max, 1 middle-high, 1 lower-high
        selected.append(high_grades_sorted[0])  # Near max
        selected.append(high_grades_sorted[len(high_grades_sorted) // 2])  # Middle
        selected.append(high_grades_sorted[-1])  # Lowest high-grade
    else:
        selected.extend(high_grades)

    # Select 2 low-grade examples with diversity
    if len(low_grades) >= 2:
        low_grades_sorted = sorted(low_grades, key=lambda x: x["grade"])
        # Pick: 1 near threshold, 1 near minimum
        selected.append(
            low_grades_sorted[-1]
        )  # Highest low-grade (just below threshold)
        selected.append(low_grades_sorted[0])  # Near minimum
    else:
        selected.extend(low_grades)

    return selected[:num_examples]


def categorize_grade(grade):
    """Categorize grade as High or Low."""
    return "High" if grade >= HIGH_GRADE_THRESHOLD else "Low"


def determine_stratum(grade, module_essays):
    """Determine which statistical stratum this grade falls into."""
    grades = [e["grade"] for e in module_essays]
    min_g = min(grades)
    max_g = max(grades)

    # Simple categorization based on position in range
    if grade >= max_g - 3:
        return "maximum"
    elif grade >= 90:
        return "q3_75th"
    elif grade >= HIGH_GRADE_THRESHOLD:
        return "median_high"
    elif grade >= 70:
        return "q1_25th"
    else:
        return "minimum"


def create_training_csv():
    """Create the training examples CSV."""

    print("=" * 70)
    print("CREATING GOLDEN EXAMPLES CSV")
    print("=" * 70)

    # Load data
    print("\n📚 Loading data...")
    essays, modules = load_data()
    print(f"✓ Loaded {len(essays)} essays from Modules 2 & 3")

    # Select examples for each module
    print("\n🎯 Selecting examples...")

    module2_examples = select_examples(essays, 2, 5)
    module3_examples = select_examples(essays, 3, 5)

    all_examples = []

    # Process Module 2 examples
    module2_info = modules.get(2, {})
    for i, ex in enumerate(module2_examples, 1):
        module_essays = [e for e in essays if e["module"] == 2]
        all_examples.append(
            {
                "example_id": f"M2_{i:03d}",
                "module": 2,
                "movie": module2_info.get("movie", ""),
                "essay_question": module2_info.get("question", ""),
                "movie_details": module2_info.get("details", ""),
                "student_essay": ex["essay"],
                "grade": ex["grade"],
                "teacher_feedback": ex["feedback"],
                "grade_category": categorize_grade(ex["grade"]),
                "stratum": determine_stratum(ex["grade"], module_essays),
            }
        )

    # Process Module 3 examples
    module3_info = modules.get(3, {})
    for i, ex in enumerate(module3_examples, 1):
        module_essays = [e for e in essays if e["module"] == 3]
        all_examples.append(
            {
                "example_id": f"M3_{i:03d}",
                "module": 3,
                "movie": module3_info.get("movie", ""),
                "essay_question": module3_info.get("question", ""),
                "movie_details": module3_info.get("details", ""),
                "student_essay": ex["essay"],
                "grade": ex["grade"],
                "teacher_feedback": ex["feedback"],
                "grade_category": categorize_grade(ex["grade"]),
                "stratum": determine_stratum(ex["grade"], module_essays),
            }
        )

    # Write CSV
    print(f"\n💾 Writing {OUTPUT_PATH}...")

    fieldnames = [
        "example_id",
        "module",
        "movie",
        "essay_question",
        "movie_details",
        "student_essay",
        "grade",
        "teacher_feedback",
        "grade_category",
        "stratum",
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_examples)

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    high_count = sum(1 for ex in all_examples if ex["grade_category"] == "High")
    low_count = sum(1 for ex in all_examples if ex["grade_category"] == "Low")

    print(f"\nTotal examples: {len(all_examples)}")
    print(f"  Module 2: {len(module2_examples)} examples")
    print(f"  Module 3: {len(module3_examples)} examples")
    print(f"\nGrade distribution:")
    print(f"  High grades (≥85): {high_count}")
    print(f"  Low grades (<85): {low_count}")

    print(f"\n📊 Examples by ID:")
    for ex in all_examples:
        print(
            f"  {ex['example_id']}: Grade {ex['grade']:.0f} ({ex['grade_category']}) - {ex['stratum']}"
        )

    print(f"\n✅ CSV created successfully: {OUTPUT_PATH}")
    print("\n📝 CSV Columns:")
    for col in fieldnames:
        print(f"  - {col}")


if __name__ == "__main__":
    create_training_csv()
