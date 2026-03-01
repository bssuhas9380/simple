"""
Data Pipeline Processor — fetches data, transforms it, and outputs analysis.
Uses requests for HTTP, numpy for math, and pandas for dataframes.
"""
import requests
import numpy as np

def fetch_data(url: str) -> list[dict]:
    """Fetch JSON data from a URL (stubbed for demo)."""
    # Stubbed: return sample data instead of actual HTTP call
    return [
        {"name": "Alice", "score": 92, "grade": "A"},
        {"name": "Bob", "score": 78, "grade": "B"},
        {"name": "Charlie", "score": 85, "grade": "B+"},
        {"name": "Diana", "score": 95, "grade": "A+"},
        {"name": "Eve", "score": 67, "grade": "C"},
    ]

def analyze_scores(data: list[dict]) -> dict:
    """Compute statistical analysis on scores using numpy."""
    scores = np.array([d["score"] for d in data])
    return {
        "count": len(scores),
        "mean": float(np.mean(scores)),
        "median": float(np.median(scores)),
        "std_dev": float(np.std(scores)),
        "min": float(np.min(scores)),
        "max": float(np.max(scores)),
        "percentile_25": float(np.percentile(scores, 25)),
        "percentile_75": float(np.percentile(scores, 75)),
    }

def grade_distribution(data: list[dict]) -> dict:
    """Count grade distribution."""
    dist = {}
    for d in data:
        g = d["grade"]
        dist[g] = dist.get(g, 0) + 1
    return dict(sorted(dist.items()))

def main():
    print("Data Pipeline Processor")
    print("=" * 40)
    
    data = fetch_data("https://api.example.com/students")
    print(f"Fetched {len(data)} records")
    
    stats = analyze_scores(data)
    print("\nScore Analysis:")
    for key, value in stats.items():
        print(f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}")
    
    dist = grade_distribution(data)
    print("\nGrade Distribution:")
    for grade, count in dist.items():
        print(f"  {grade}: {'█' * count * 3} ({count})")

if __name__ == "__main__":
    main()
