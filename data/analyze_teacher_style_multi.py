#!/usr/bin/env python3
"""
Teacher Grading & Feedback Style Analysis Tool - Multi-Iteration Version

This script reverse-engineers a teacher's grading and feedback patterns
using 15 iterations of stratified sampling with smart overlap handling.

Total essays analyzed: 15 iterations × 5 essays = up to 75 samples
from 195 total essays, with intelligent overlap management for rare low grades.
"""

import csv
import os
import json
import statistics
import time
from typing import List, Dict, Tuple, Set
import random
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("\"'")

# Set random seed for reproducibility
random.seed(42)

# Configuration
DATASET_PATH = "data/movie_grading_dataset.csv"
MODULE_DETAILS_PATH = "data/module_details.csv"
RUBRIC_PATH = "data/rubric.txt"
INSTRUCTIONS_PATH = "data/instructions.txt"
OUTPUT_DIR = "data/analysis_results"
MASTER_CSV_PATH = "data/teacher_analysis_master.csv"

# Number of iterations
NUM_ITERATIONS = 15

# Grade thresholds
HIGH_GRADE_THRESHOLD = 85  # Essays below this are considered "rare"

# Gemini API Configuration
GEMINI_MODEL = "gemini-3-pro-preview"


def load_grading_data() -> Tuple[List[Dict], Dict[int, Dict], str, str]:
    """Load all necessary data files."""

    # Load essays with grades - try utf-8 first, fallback to latin-1
    essays = []
    encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

    for encoding in encodings:
        try:
            with open(DATASET_PATH, "r", encoding=encoding) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        if row["Grade out of 100"] and row["Grade out of 100"].strip():
                            grade = float(row["Grade out of 100"])
                            essays.append(
                                {
                                    "id": len(essays),  # Unique ID for tracking
                                    "module": int(row["Module"]),
                                    "essay": row["Student Essay"],
                                    "grade": grade,
                                    "feedback": row["Teacher Feedback"],
                                }
                            )
                    except (ValueError, KeyError):
                        continue
            print(f"  ✓ Loaded essays with encoding: {encoding}")
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
                        modules[module_num] = {
                            "movie": row["Movie"],
                            "question": row["Essay Question"],
                            "details": row["Movie-details"],
                        }
                    except (ValueError, KeyError):
                        continue
            print(f"  ✓ Loaded modules with encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue

    # Load rubric and instructions
    rubric = ""
    for encoding in encodings:
        try:
            with open(RUBRIC_PATH, "r", encoding=encoding) as f:
                rubric = f.read()
            break
        except UnicodeDecodeError:
            continue

    instructions = ""
    for encoding in encodings:
        try:
            with open(INSTRUCTIONS_PATH, "r", encoding=encoding) as f:
                instructions = f.read()
            break
        except UnicodeDecodeError:
            continue

    return essays, modules, rubric, instructions


def categorize_essays(essays: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """Categorize essays into common (>=85) and rare (<85) groups."""
    common = [e for e in essays if e["grade"] >= HIGH_GRADE_THRESHOLD]
    rare = [e for e in essays if e["grade"] < HIGH_GRADE_THRESHOLD]
    return common, rare


def get_stratified_samples_iteration(
    essays: List[Dict], used_common: Set[int], used_rare: Set[int], iteration: int
) -> Tuple[Dict[str, Dict], Set[int], Set[int]]:
    """
    Select one essay from each grade stratum for this iteration.
    Prioritizes unused essays for common grades, allows overlap for rare grades.

    Returns:
        samples: Dict of stratum -> essay
        updated_used_common: Set of used common essay IDs
        updated_used_rare: Set of used rare essay IDs
    """

    common, rare = categorize_essays(essays)

    grades = [e["grade"] for e in essays]
    min_grade = min(grades)
    max_grade = max(grades)
    median_grade = statistics.median(grades)
    q1 = statistics.quantiles(grades, n=4)[0]
    q3 = statistics.quantiles(grades, n=4)[2]

    def find_best_candidate(
        target_grade: float, stratum_name: str
    ) -> Tuple[Dict, bool]:
        """
        Find best candidate for stratum.
        For rare grades: use any available (overlap OK)
        For common grades: prefer unused, allow overlap if necessary
        Returns (essay, is_reused)
        """
        tolerance = 3.0

        # Determine if this is a rare stratum
        is_rare_stratum = (
            stratum_name in ["minimum"] or target_grade < HIGH_GRADE_THRESHOLD
        )

        if is_rare_stratum:
            # For rare grades, use from rare pool or any essay
            pool = rare if rare else essays
            candidates = [
                e for e in pool if abs(e["grade"] - target_grade) <= tolerance
            ]
            if not candidates:
                candidates = essays
            selected = min(candidates, key=lambda x: abs(x["grade"] - target_grade))
            return selected, selected["id"] in used_rare
        else:
            # For common grades, prefer unused
            available_common = [e for e in common if e["id"] not in used_common]

            if available_common:
                candidates = [
                    e
                    for e in available_common
                    if abs(e["grade"] - target_grade) <= tolerance
                ]
                if not candidates:
                    candidates = available_common
                selected = min(candidates, key=lambda x: abs(x["grade"] - target_grade))
                return selected, False
            else:
                # All common used, allow overlap
                candidates = [
                    e for e in common if abs(e["grade"] - target_grade) <= tolerance
                ]
                if not candidates:
                    candidates = common
                selected = min(candidates, key=lambda x: abs(x["grade"] - target_grade))
                return selected, True

    samples = {}
    new_used_common = used_common.copy()
    new_used_rare = used_rare.copy()

    # Sample each stratum
    strata = [
        ("maximum", max_grade),
        ("q3_75th", q3),
        ("median", median_grade),
        ("q1_25th", q1),
        ("minimum", min_grade),
    ]

    for stratum_name, target in strata:
        essay, is_reused = find_best_candidate(target, stratum_name)
        samples[stratum_name] = essay

        # Track usage
        if essay["grade"] >= HIGH_GRADE_THRESHOLD:
            new_used_common.add(essay["id"])
        else:
            new_used_rare.add(essay["id"])

    return samples, new_used_common, new_used_rare


def build_analysis_prompt(
    essays_data: List[Dict], rubric: str, instructions: str, iteration: int
) -> str:
    """Build the prompt for Gemini to analyze grading and feedback patterns."""

    prompt = f"""You are an expert educational analyst tasked with reverse-engineering a teacher's grading and feedback style.

## ITERATION {iteration} of 15
This is iteration {iteration} of a multi-iteration analysis. Each iteration samples different essays across the grade spectrum to build a comprehensive understanding.

## CONTEXT
You are analyzing {len(essays_data)} student essays across the full grade spectrum (from minimum to maximum grades) from the same teacher.

## ASSIGNMENT INSTRUCTIONS
{instructions}

## GRADING RUBRIC
{rubric}

IMPORTANT: The teacher appears to give grades intuitively first, then uses the rubric to justify the grade afterward (grades don't perfectly align with rubric criteria).

## ESSAYS TO ANALYZE FOR ITERATION {iteration}

"""

    for i, data in enumerate(essays_data, 1):
        prompt += f"""--- SAMPLE {i}: GRADE {data["grade"]}/100 ({data["stratum"].upper()}) ---
MODULE: {data["module"]} - {data["movie"]}
ESSAY QUESTION:
{data["question"]}

STUDENT ESSAY:
{data["essay"][:1500]}...

TEACHER FEEDBACK:
{data["feedback"]}

"""

    prompt += """## YOUR TASK

Based on these samples spanning the full grade range, provide the following analysis:

### 1. GRADING STYLE DECONSTRUCTION (max 300 words)
Analyze HOW this teacher grades. Consider:
- What patterns do you see in what earns high vs low grades?
- What aspects of the essay does the teacher prioritize?
- How strictly does the teacher follow the rubric vs. intuitive judgment?
- What are the teacher's "pet peeves" or consistently commented issues?
- What earns praise and what earns criticism?

### 2. SYSTEM PROMPT FOR GRADING EMULATION
Provide a concise system prompt (2-3 paragraphs) that would instruct an AI to grade exactly like this teacher. Include specific guidance on:
- How to evaluate content quality
- What weight to give different aspects
- The teacher's apparent priorities and preferences

### 3. FEEDBACK STYLE DECONSTRUCTION (max 300 words)
Analyze the teacher's feedback patterns:
- What is the tone? (encouraging, critical, balanced, etc.)
- What types of comments are consistently made?
- How does feedback vary by grade level?
- What suggestions are typically offered?
- What is the balance between praise and critique?

### 4. SYSTEM PROMPT FOR FEEDBACK EMULATION
Provide a concise system prompt (2-3 paragraphs) that would instruct an AI to write feedback exactly like this teacher. Include:
- Tone and voice characteristics
- Structure of feedback (what comes first, what follows)
- Types of comments to always include or avoid
- How to balance encouragement with constructive criticism

Format your response clearly with headers for each section numbered 1-4."""

    return prompt


def call_gemini_api(prompt: str, api_key: str) -> str:
    """Call the Gemini API with the analysis prompt."""
    try:
        from google import genai

        # Set API key in environment for the new client
        os.environ["GOOGLE_API_KEY"] = api_key

        client = genai.Client()

        print("  Calling Gemini API...")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config={
                "temperature": 0.3,
                "max_output_tokens": 4000,
            },
        )

        return response.text

    except Exception as e:
        print(f"  Error calling Gemini API: {e}")
        return None


def parse_analysis_response(response_text: str) -> Dict[str, str]:
    """Parse the Gemini response into structured sections."""

    sections = {
        "grading_deconstruction": "",
        "grading_system_prompt": "",
        "feedback_deconstruction": "",
        "feedback_system_prompt": "",
    }

    lines = response_text.split("\n")
    current_section = None
    current_content = []

    for line in lines:
        line_upper = line.upper().strip()

        # Check for section headers
        if (
            any(
                x in line_upper
                for x in ["1.", "GRADING STYLE", "GRADING DECONSTRUCTION"]
            )
            and "GRADING" in line_upper
        ):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "grading_deconstruction"
            current_content = []
        elif (
            any(
                x in line_upper
                for x in ["2.", "SYSTEM PROMPT FOR GRADING", "GRADING EMULATION"]
            )
            and "GRADING" in line_upper
        ):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "grading_system_prompt"
            current_content = []
        elif (
            any(
                x in line_upper
                for x in ["3.", "FEEDBACK STYLE", "FEEDBACK DECONSTRUCTION"]
            )
            and "FEEDBACK" in line_upper
        ):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "feedback_deconstruction"
            current_content = []
        elif (
            any(
                x in line_upper
                for x in ["4.", "SYSTEM PROMPT FOR FEEDBACK", "FEEDBACK EMULATION"]
            )
            and "FEEDBACK" in line_upper
        ):
            if current_section and current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = "feedback_system_prompt"
            current_content = []
        elif current_section and not line.startswith("#") and line.strip():
            current_content.append(line)

    # Save the last section
    if current_section and current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def save_iteration_results(
    results: Dict, samples: Dict, iteration: int, output_dir: str
):
    """Save results from a single iteration."""

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().isoformat()
    sample_info = json.dumps(
        {
            k: {"grade": v["grade"], "id": v["id"], "module": v["module"]}
            for k, v in samples.items()
        }
    )

    # Save individual iteration file
    iteration_file = os.path.join(output_dir, f"iteration_{iteration:02d}.csv")
    with open(iteration_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["iteration", "analysis_type", "content", "samples_used", "timestamp"]
        )

        for analysis_type, content in results.items():
            writer.writerow([iteration, analysis_type, content, sample_info, timestamp])

    return iteration_file


def update_master_csv(all_results: List[Dict], master_path: str):
    """Update the master CSV with all iterations."""

    with open(master_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "iteration",
                "analysis_type",
                "content",
                "samples_grades",
                "samples_ids",
                "samples_modules",
                "timestamp",
            ]
        )

        for result in all_results:
            writer.writerow(
                [
                    result["iteration"],
                    result["analysis_type"],
                    result["content"],
                    result["samples_grades"],
                    result["samples_ids"],
                    result["samples_modules"],
                    result["timestamp"],
                ]
            )

    print(f"\n✓ Master CSV updated: {master_path}")


def print_iteration_summary(iteration: int, samples: Dict, results: Dict):
    """Print a summary of the iteration results."""

    print(f"\n  Iteration {iteration} Summary:")
    print(
        f"  Samples: "
        + ", ".join([f"{k}:{v['grade']:.0f}" for k, v in samples.items()])
    )

    for key, content in results.items():
        if content:
            word_count = len(content.split())
            preview = content[:120].replace("\n", " ").strip()
            print(f"    {key}: {word_count} words - {preview}...")


def main():
    """Main execution function with 15 iterations."""

    print("=" * 70)
    print("TEACHER GRADING & FEEDBACK STYLE ANALYZER - 15 ITERATIONS")
    print("=" * 70)

    # Check for API key (supports both GOOGLE_API_KEY and GEMINI_API_KEY)
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: API key not found.")
        print("Set either GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
        print("Or add it to .env file in the project root.")
        return

    # Load data
    print("\n📚 Loading data files...")
    essays, modules, rubric, instructions = load_grading_data()
    common, rare = categorize_essays(essays)
    print(f"✓ Loaded {len(essays)} essays ({len(common)} common, {len(rare)} rare)")
    print(f"✓ Loaded {len(modules)} modules")

    # Initialize tracking
    used_common_ids: Set[int] = set()
    used_rare_ids: Set[int] = set()
    all_results = []

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n🚀 Starting {NUM_ITERATIONS} iterations...")
    print("=" * 70)

    for iteration in range(1, NUM_ITERATIONS + 1):
        print(f"\n📊 ITERATION {iteration}/{NUM_ITERATIONS}")
        print("-" * 70)

        # Get stratified samples for this iteration
        samples, used_common_ids, used_rare_ids = get_stratified_samples_iteration(
            essays, used_common_ids, used_rare_ids, iteration
        )

        print(
            f"  Selected samples: "
            + ", ".join(
                [f"{k}:{v['grade']:.0f}(id:{v['id']})" for k, v in samples.items()]
            )
        )

        # Prepare essay data with module questions
        essays_data = []
        for stratum, essay in samples.items():
            module_info = modules.get(essay["module"], {})
            essays_data.append(
                {
                    "stratum": stratum,
                    "grade": essay["grade"],
                    "module": essay["module"],
                    "movie": module_info.get("movie", "Unknown"),
                    "question": module_info.get("question", "Unknown"),
                    "essay": essay["essay"],
                    "feedback": essay["feedback"],
                    "id": essay["id"],
                }
            )

        # Build analysis prompt
        prompt = build_analysis_prompt(essays_data, rubric, instructions, iteration)

        # Call Gemini API
        response = call_gemini_api(prompt, api_key)

        if response:
            # Save raw response
            response_file = os.path.join(
                OUTPUT_DIR, f"iteration_{iteration:02d}_response.txt"
            )
            with open(response_file, "w", encoding="utf-8") as f:
                f.write(response)

            # Parse response
            results = parse_analysis_response(response)

            # Print summary
            print_iteration_summary(iteration, samples, results)

            # Prepare result records
            timestamp = datetime.now().isoformat()
            sample_grades = json.dumps({k: v["grade"] for k, v in samples.items()})
            sample_ids = json.dumps({k: v["id"] for k, v in samples.items()})
            sample_modules = json.dumps({k: v["module"] for k, v in samples.items()})

            for analysis_type, content in results.items():
                all_results.append(
                    {
                        "iteration": iteration,
                        "analysis_type": analysis_type,
                        "content": content,
                        "samples_grades": sample_grades,
                        "samples_ids": sample_ids,
                        "samples_modules": sample_modules,
                        "timestamp": timestamp,
                    }
                )

            # Save iteration file
            save_iteration_results(results, samples, iteration, OUTPUT_DIR)

            print(f"  ✓ Iteration {iteration} complete")
        else:
            print(f"  ✗ Iteration {iteration} failed - skipping")

        # Small delay between iterations (even on paid tier, good practice)
        if iteration < NUM_ITERATIONS:
            time.sleep(0.5)

    # Final aggregation
    print("\n" + "=" * 70)
    print("📊 FINALIZING RESULTS")
    print("=" * 70)

    # Update master CSV
    update_master_csv(all_results, MASTER_CSV_PATH)

    # Print statistics
    print(f"\n📈 ANALYSIS STATISTICS:")
    print(f"  Total iterations completed: {NUM_ITERATIONS}")
    print(f"  Total essays sampled: {len(used_common_ids) + len(used_rare_ids)} unique")
    print(f"    - Common grades (≥85): {len(used_common_ids)} unique essays")
    print(f"    - Rare grades (<85): {len(used_rare_ids)} unique essays")
    print(f"  Total analysis records: {len(all_results)}")

    print(f"\n📁 OUTPUT FILES:")
    print(f"  - Master CSV: {MASTER_CSV_PATH}")
    print(f"  - Iteration files: {OUTPUT_DIR}/iteration_*.csv")
    print(f"  - Raw responses: {OUTPUT_DIR}/iteration_*_response.txt")

    print("\n" + "=" * 70)
    print("✅ ALL ITERATIONS COMPLETE!")
    print("=" * 70)

    print("\n🎯 NEXT STEPS:")
    print("  1. Review the master CSV for patterns across iterations")
    print("  2. Look for consistent themes in grading_deconstruction")
    print("  3. Compare grading_system_prompt across iterations")
    print("  4. Identify consensus feedback patterns")


if __name__ == "__main__":
    main()
