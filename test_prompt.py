import os
import csv
import random
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Configuration
MODEL_NAME = "gemini-1.5-flash" 
# You can switch to pro for better reasoning if needed

def load_rubric():
    with open('data/rubric.txt', 'r') as f:
        return f.read()

def load_random_essay():
    essays = []
    with open('data/movie_grading_dataset.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Grade out of 100']:
                essays.append(row)
    return random.choice(essays)

def create_system_prompt(rubric_text):
    return f"""You are an expert Teaching Assistant for a Linguistics and Film course.
Your goal is to grade student essays with a rigorous but empathetic style.
You are known for catching small details like typos and timestamps, but also appreciating deep insights.

RUBRIC:
{rubric_text}

INSTRUCTIONS:
1. Read the essay carefully.
2. Assign a grade out of 100.
3. Write feedback. Start with "Hi [Student Name],". 
4. Be specific. Mention 1 thing they did well and 1 thing to improve.
5. Watch out for:
   - Missing timestamps (Major deduction)
   - Typos (Point them out gently)
   - Word count (Too short = deduction)
   - Tone: Encouraging but firm on standards.

OUTPUT FORMAT:
Grade: [Score]
Feedback: [Your feedback here]
"""

def test_prompt():
    print("--- Loading Data ---")
    rubric = load_rubric()
    essay_data = load_random_essay()
    
    student_essay = essay_data['Student Essay']
    actual_grade = essay_data['Grade out of 100']
    actual_feedback = essay_data['Teacher Feedback']
    
    print("\n--- Student Essay ---")
    print(student_essay[:500] + "...") 
    
    print("\n--- Generating Grade with Gemini ---")
    model = genai.GenerativeModel(MODEL_NAME, system_instruction=create_system_prompt(rubric))
    
    response = model.generate_content(f"Grade this essay:\n\n{student_essay}")
    
    print("\n" + "="*30)
    print("       COMPARISON       ")
    print("="*30)
    print(f"\n[ACTUAL TEACHER] Grade: {actual_grade}")
    print(f"Feedback: {actual_feedback}")
    
    print("\n" + "-"*30)
    print(f"[GEMINI] Generated Output:")
    print(response.text)
    print("="*30)

if __name__ == "__main__":
    test_prompt()
