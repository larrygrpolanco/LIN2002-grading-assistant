#!/usr/bin/env python3
"""
Module 2 & 3 Focused Analysis Tool

This script analyzes teacher grading patterns specifically for:
- Module 2 (Perfect Secret): 5 iterations
- Module 3 (Another Round): 3 iterations
- Final comparison analysis between modules

Total: 8 iterations × 5 essays = 40 samples
Output: Master CSV with all results + comparison
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
OUTPUT_DIR = "data/module2_module3_results"
MASTER_CSV_PATH = "data/module2_module3_analysis_master.csv"

# Module-specific configuration
TARGET_MODULES = [2, 3]
MODULE_ITERATIONS = {2: 5, 3: 3}  # Module 2: 5 iterations, Module 3: 3 iterations

# Grade thresholds
HIGH_GRADE_THRESHOLD = 85

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
                            module = int(row["Module"])
                            # Only include Module 2 and 3
                            if module in TARGET_MODULES:
                                essays.append(
                                    {
                                        "id": len(essays),
                                        "module": module,
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
                        if module_num in TARGET_MODULES:
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
    essays: List[Dict],
    used_common: Set[int],
    used_rare: Set[int],
    iteration: int,
    module_num: int,
) -> Tuple[Dict[str, Dict], Set[int], Set[int]]:
    """
    Select one essay from each grade stratum for this iteration within a specific module.
    """

    # Filter essays to current module only
    module_essays = [e for e in essays if e["module"] == module_num]
    common, rare = categorize_essays(module_essays)

    grades = [e["grade"] for e in module_essays]
    min_grade = min(grades)
    max_grade = max(grades)
    median_grade = statistics.median(grades)
    q1 = statistics.quantiles(grades, n=4)[0]
    q3 = statistics.quantiles(grades, n=4)[2]

    def find_best_candidate(
        target_grade: float, stratum_name: str
    ) -> Tuple[Dict, bool]:
        """Find best candidate for stratum."""
        tolerance = 3.0

        is_rare_stratum = (
            stratum_name in ["minimum"] or target_grade < HIGH_GRADE_THRESHOLD
        )

        if is_rare_stratum:
            pool = rare if rare else module_essays
            candidates = [
                e for e in pool if abs(e["grade"] - target_grade) <= tolerance
            ]
            if not candidates:
                candidates = module_essays
            selected = min(candidates, key=lambda x: abs(x["grade"] - target_grade))
            return selected, selected["id"] in used_rare
        else:
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

        if essay["grade"] >= HIGH_GRADE_THRESHOLD:
            new_used_common.add(essay["id"])
        else:
            new_used_rare.add(essay["id"])

    return samples, new_used_common, new_used_rare


def build_analysis_prompt(
    essays_data: List[Dict],
    rubric: str,
    instructions: str,
    iteration: int,
    module_num: int,
    modules: Dict,
) -> str:
    """Build the prompt for Gemini to analyze grading and feedback patterns."""

    module_info = modules.get(module_num, {})

    prompt = f"""You are an expert educational analyst tasked with reverse-engineering a teacher's grading and feedback style.

## ITERATION {iteration} - MODULE {module_num} FOCUSED ANALYSIS
This is iteration {iteration} analyzing essays from Module {module_num}: {module_info.get("movie", "Unknown")}
All {len(essays_data)} samples below are from the same module and respond to the same essay question about the same film.

## FILM INFORMATION
{module_info.get("details", "No details available")}

## ASSIGNMENT INSTRUCTIONS
{instructions}

## GRADING RUBRIC
{rubric}

IMPORTANT: The teacher appears to give grades intuitively first, then uses the rubric to justify the grade afterward (grades don't perfectly align with rubric criteria).

## ESSAY QUESTION FOR MODULE {module_num}
{module_info.get("question", "Unknown")}

## ESSAYS TO ANALYZE FOR MODULE {module_num} - ITERATION {iteration}

"""

    for i, data in enumerate(essays_data, 1):
        prompt += f"""--- SAMPLE {i}: GRADE {data["grade"]}/100 ({data["stratum"].upper()}) ---
ESSAY:
{data["essay"][:1500]}...

TEACHER FEEDBACK:
{data["feedback"]}

"""

    prompt += """## YOUR TASK

Based on these Module-specific samples spanning the full grade range, provide the following analysis:

### 1. GRADING STYLE DECONSTRUCTION (max 300 words)
Analyze HOW this teacher grades for Module-specific essays. Consider:
- What patterns do you see in what earns high vs low grades?
- What aspects of the essay does the teacher prioritize?
- How strictly does the teacher follow the rubric vs. intuitive judgment?
- What are the teacher's "pet peeves" or consistently commented issues?
- What earns praise and what earns criticism?
- Are there module-specific grading patterns (e.g., particular expectations for this film/question)?

### 2. SYSTEM PROMPT FOR GRADING EMULATION
Provide a concise system prompt (2-3 paragraphs) that would instruct an AI to grade exactly like this teacher for Module-specific essays. Include:
- How to evaluate content quality for this specific module
- What weight to give different aspects
- The teacher's apparent priorities and preferences
- Module-specific grading nuances

### 3. FEEDBACK STYLE DECONSTRUCTION (max 300 words)
Analyze the teacher's feedback patterns for Module-specific essays:
- What is the tone? (encouraging, critical, balanced, etc.)
- What types of comments are consistently made?
- How does feedback vary by grade level?
- What suggestions are typically offered?
- What is the balance between praise and critique?
- Are there module-specific feedback patterns?

### 4. SYSTEM PROMPT FOR FEEDBACK EMULATION
Provide a concise system prompt (2-3 paragraphs) that would instruct an AI to write feedback exactly like this teacher for Module-specific essays. Include:
- Tone and voice characteristics
- Structure of feedback
- Types of comments to include or avoid
- How to balance encouragement with constructive criticism
- Module-specific feedback nuances

Format your response clearly with headers for each section numbered 1-4."""

    return prompt


def build_comparison_prompt(all_results: List[Dict], modules: Dict) -> str:
    """Build a prompt to compare patterns between Module 2 and Module 3."""

    prompt = f"""You are an expert educational analyst tasked with comparing grading patterns between two different modules.

## CONTEXT
You have analyzed teacher grading and feedback patterns for Module 2 (Perfect Secret) and Module 3 (Another Round) separately. Now you need to compare them to identify:
1. Consistent patterns across modules (teacher's general style)
2. Module-specific variations (how expectations differ by film/question)
3. Universal principles that apply to all modules

## MODULE INFORMATION

### Module 2: Perfect Secret
{modules.get(2, {}).get("details", "")[:500]}...

### Module 3: Another Round  
{modules.get(3, {}).get("details", "")[:500]}...

## SUMMARY OF PREVIOUS ANALYSES

"""

    # Summarize findings from Module 2
    module2_results = [r for r in all_results if r.get("module") == 2]
    module3_results = [r for r in all_results if r.get("module") == 3]

    prompt += "### Module 2 Key Findings ({} iterations analyzed):\n".format(
        len(module2_results) // 4
    )
    for result in module2_results[:4]:  # Show first iteration of each type
        prompt += (
            f"\n{result['analysis_type'].upper()}:\n{result['content'][:300]}...\n"
        )

    prompt += "\n\n### Module 3 Key Findings ({} iterations analyzed):\n".format(
        len(module3_results) // 4
    )
    for result in module3_results[:4]:  # Show first iteration of each type
        prompt += (
            f"\n{result['analysis_type'].upper()}:\n{result['content'][:300]}...\n"
        )

    prompt += """

## YOUR TASK

Provide a comprehensive comparison analysis:

### 1. CONSISTENT PATTERNS (Teacher's Core Style)
What grading and feedback patterns remain consistent across both modules? This represents the teacher's fundamental approach regardless of the specific film or question.

### 2. MODULE-SPECIFIC VARIATIONS
How do grading expectations and feedback styles differ between Module 2 and Module 3? Consider:
- Do different films/questions have different "ideal" responses?
- Are there topic-specific feedback patterns?
- Does the teacher weight criteria differently for different types of content?

### 3. UNIVERSAL GRADING SYSTEM PROMPT
Synthesize a master system prompt that captures the teacher's consistent style while accounting for module variations. This should be adaptable to any module.

### 4. UNIVERSAL FEEDBACK SYSTEM PROMPT  
Synthesize a master feedback prompt that captures the teacher's consistent voice while being adaptable to different modules.

### 5. RECOMMENDATIONS FOR GRADING ASSISTANT
Based on these patterns, what are the key principles for building a grading assistant that emulates this teacher? What should be prioritized?

Format clearly with numbered headers."""

    return prompt


def call_gemini_api(prompt: str, api_key: str) -> str:
    """Call the Gemini API with the analysis prompt."""
    try:
        from google import genai

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

    if current_section and current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def save_iteration_results(
    results: Dict, samples: Dict, iteration: int, module_num: int, output_dir: str
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

    iteration_file = os.path.join(
        output_dir, f"module{module_num}_iteration_{iteration:02d}.csv"
    )
    with open(iteration_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "module",
                "iteration",
                "analysis_type",
                "content",
                "samples_used",
                "timestamp",
            ]
        )

        for analysis_type, content in results.items():
            writer.writerow(
                [module_num, iteration, analysis_type, content, sample_info, timestamp]
            )

    return iteration_file


def update_master_csv(all_results: List[Dict], master_path: str):
    """Update the master CSV with all iterations."""

    with open(master_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "module",
                "iteration",
                "analysis_type",
                "content",
                "samples_grades",
                "samples_ids",
                "timestamp",
            ]
        )

        for result in all_results:
            writer.writerow(
                [
                    result.get("module", "comparison"),
                    result.get("iteration", "N/A"),
                    result["analysis_type"],
                    result["content"],
                    result.get("samples_grades", ""),
                    result.get("samples_ids", ""),
                    result["timestamp"],
                ]
            )

    print(f"\n✓ Master CSV updated: {master_path}")


def main():
    """Main execution function with module-specific iterations."""

    print("=" * 70)
    print("MODULE 2 & 3 FOCUSED ANALYZER")
    print("=" * 70)

    # Check for API key
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: API key not found.")
        print("Set either GOOGLE_API_KEY or GEMINI_API_KEY environment variable.")
        return

    # Load data
    print("\n📚 Loading data files...")
    essays, modules, rubric, instructions = load_grading_data()
    print(f"✓ Loaded {len(essays)} essays from Modules 2 & 3")
    print(f"✓ Loaded {len(modules)} modules")

    # Count essays per module
    module_counts = {}
    for essay in essays:
        mod = essay["module"]
        module_counts[mod] = module_counts.get(mod, 0) + 1

    for mod in sorted(module_counts.keys()):
        mod_essays = [e for e in essays if e["module"] == mod]
        common, rare = categorize_essays(mod_essays)
        print(
            f"  Module {mod} ({modules.get(mod, {}).get('movie', 'Unknown')}): {module_counts[mod]} essays ({len(common)} common, {len(rare)} rare)"
        )

    # Initialize tracking
    used_common_ids: Set[int] = set()
    used_rare_ids: Set[int] = set()
    all_results = []

    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Process each module
    total_iterations = sum(MODULE_ITERATIONS.values())
    current_iteration = 0

    for module_num in TARGET_MODULES:
        num_iterations = MODULE_ITERATIONS[module_num]
        module_essays = [e for e in essays if e["module"] == module_num]

        print(
            f"\n🎬 MODULE {module_num}: {modules.get(module_num, {}).get('movie', 'Unknown')}"
        )
        print("-" * 70)

        for iteration in range(1, num_iterations + 1):
            current_iteration += 1
            print(
                f"\n📊 ITERATION {iteration}/{num_iterations} (Global: {current_iteration}/{total_iterations})"
            )

            # Get stratified samples for this module and iteration
            samples, used_common_ids, used_rare_ids = get_stratified_samples_iteration(
                essays, used_common_ids, used_rare_ids, iteration, module_num
            )

            print(
                f"  Selected samples: "
                + ", ".join(
                    [f"{k}:{v['grade']:.0f}(id:{v['id']})" for k, v in samples.items()]
                )
            )

            # Prepare essay data
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
            prompt = build_analysis_prompt(
                essays_data, rubric, instructions, iteration, module_num, modules
            )

            # Call Gemini API
            response = call_gemini_api(prompt, api_key)

            if response:
                # Save raw response
                response_file = os.path.join(
                    OUTPUT_DIR,
                    f"module{module_num}_iteration_{iteration:02d}_response.txt",
                )
                with open(response_file, "w", encoding="utf-8") as f:
                    f.write(response)

                # Parse response
                results = parse_analysis_response(response)

                # Print summary
                print(f"  ✓ Analysis complete")
                for key, content in results.items():
                    if content:
                        word_count = len(content.split())
                        print(f"    {key}: {word_count} words")

                # Prepare result records
                timestamp = datetime.now().isoformat()
                sample_grades = json.dumps({k: v["grade"] for k, v in samples.items()})
                sample_ids = json.dumps({k: v["id"] for k, v in samples.items()})

                for analysis_type, content in results.items():
                    all_results.append(
                        {
                            "module": module_num,
                            "iteration": iteration,
                            "analysis_type": analysis_type,
                            "content": content,
                            "samples_grades": sample_grades,
                            "samples_ids": sample_ids,
                            "timestamp": timestamp,
                        }
                    )

                # Save iteration file
                save_iteration_results(
                    results, samples, iteration, module_num, OUTPUT_DIR
                )
            else:
                print(f"  ✗ Iteration failed - skipping")

            if current_iteration < total_iterations:
                time.sleep(0.5)

    # FINAL COMPARISON ANALYSIS
    print("\n" + "=" * 70)
    print("🔍 FINAL COMPARISON ANALYSIS")
    print("=" * 70)

    print("\n  Building comparison prompt...")
    comparison_prompt = build_comparison_prompt(all_results, modules)

    # Save comparison prompt
    comparison_prompt_file = os.path.join(OUTPUT_DIR, "comparison_prompt.txt")
    with open(comparison_prompt_file, "w", encoding="utf-8") as f:
        f.write(comparison_prompt)
    print(f"  ✓ Comparison prompt saved")

    # Call Gemini for comparison
    print("  Calling Gemini API for comparison analysis...")
    comparison_response = call_gemini_api(comparison_prompt, api_key)

    if comparison_response:
        # Save raw comparison response
        comparison_file = os.path.join(OUTPUT_DIR, "comparison_response.txt")
        with open(comparison_file, "w", encoding="utf-8") as f:
            f.write(comparison_response)
        print(f"  ✓ Comparison response saved")

        # Add comparison to results
        timestamp = datetime.now().isoformat()
        all_results.append(
            {
                "module": "comparison",
                "iteration": "final",
                "analysis_type": "module_comparison",
                "content": comparison_response,
                "samples_grades": "N/A",
                "samples_ids": "N/A",
                "timestamp": timestamp,
            }
        )

    # Final aggregation
    print("\n" + "=" * 70)
    print("📊 FINALIZING RESULTS")
    print("=" * 70)

    # Update master CSV
    update_master_csv(all_results, MASTER_CSV_PATH)

    # Print statistics
    print(f"\n📈 ANALYSIS STATISTICS:")
    print(f"  Total iterations: {total_iterations}")
    module2_count = sum(1 for r in all_results if r.get("module") == 2)
    module3_count = sum(1 for r in all_results if r.get("module") == 3)
    comparison_count = sum(1 for r in all_results if r.get("module") == "comparison")
    print(f"  Module 2 records: {module2_count}")
    print(f"  Module 3 records: {module3_count}")
    print(f"  Comparison records: {comparison_count}")
    print(f"  Total records: {len(all_results)}")

    print(f"\n📁 OUTPUT FILES:")
    print(f"  - Master CSV: {MASTER_CSV_PATH}")
    print(f"  - Iteration files: {OUTPUT_DIR}/module*_iteration_*.csv")
    print(f"  - Responses: {OUTPUT_DIR}/module*_iteration_*_response.txt")
    print(f"  - Comparison: {OUTPUT_DIR}/comparison_response.txt")

    print("\n" + "=" * 70)
    print("✅ ALL ANALYSES COMPLETE!")
    print("=" * 70)

    print("\n🎯 NEXT STEPS:")
    print("  1. Review Module 2 and Module 3 patterns in the master CSV")
    print("  2. Read the comparison_response.txt for cross-module insights")
    print("  3. Identify consistent teacher style vs module-specific variations")
    print("  4. Use findings to build the grading assistant")


if __name__ == "__main__":
    main()
