import csv
import random
import statistics

def analyze_data():
    dataset_path = 'data/movie_grading_dataset.csv'
    
    grades = []
    essays = []
    
    print(f"Loading data from {dataset_path}...")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Clean up grade - sometimes it might be empty or have text
                if row['Grade out of 100'] and row['Grade out of 100'].strip():
                    grade = float(row['Grade out of 100'])
                    grades.append(grade)
                    essays.append(row)
            except ValueError:
                continue

    print(f"\nTotal Essays: {len(essays)}")
    print(f"Average Grade: {statistics.mean(grades):.2f}")
    print(f"Min Grade: {min(grades)}")
    print(f"Max Grade: {max(grades)}")
    
    # Categorize essays
    high_score = [e for e in essays if float(e['Grade out of 100']) >= 95]
    mid_score = [e for e in essays if 85 <= float(e['Grade out of 100']) < 95]
    low_score = [e for e in essays if float(e['Grade out of 100']) < 85]
    
    print("\n--- Selected Golden Examples ---")
    
    def print_example(category, essay_list):
        if not essay_list:
            print(f"\nNo examples found for {category}")
            return
            
        example = random.choice(essay_list)
        print(f"\n[{category}] Grade: {example['Grade out of 100']}")
        print(f"Feedback Preview: {example['Teacher Feedback'][:150]}...")
        # In a real scenario we might save these to a file, but printing is good for now.

    print_example("HIGH SCORE (>= 95)", high_score)
    print_example("MID SCORE (85-94)", mid_score)
    print_example("LOW SCORE (< 85)", low_score)
    
    # Special check: Length vs Grade
    # Let's see if short essays really get penalized
    short_essays = [e for e in essays if len(e['Student Essay'].split()) < 250]
    if short_essays:
        avg_short_grade = statistics.mean([float(e['Grade out of 100']) for e in short_essays])
        print(f"\nAverage Grade for Short Essays (<250 words): {avg_short_grade:.2f} (Count: {len(short_essays)})")

if __name__ == "__main__":
    analyze_data()
