import json
import random
import string
from typing import List, Dict, Any

QUESTIONS_FILE = "test_questions.json"
NUM_QUESTIONS = 50  # Number of test questions to create

# Sample question templates
QUESTION_TEMPLATES = [
    "What is the time complexity of {algorithm}?",
    "Explain how {concept} works in {language}.",
    "What are the main differences between {tech1} and {tech2}?",
    "How would you implement {feature} in {language}?",
    "What are the best practices for {topic} in {context}?"
]

# Sample fillers for templates
ALGORITHMS = ["quicksort", "mergesort", "binary search", "Dijkstra's algorithm", "BFS", "DFS"]
CONCEPTS = ["inheritance", "polymorphism", "recursion", "closures", "async/await", "promises"]
LANGUAGES = ["Python", "JavaScript", "Java", "C++", "Go", "Rust"]
TECHNOLOGIES = ["REST", "GraphQL", "WebSocket", "gRPC", "RPC", "SOAP"]
TOPICS = ["error handling", "logging", "testing", "deployment", "security", "performance"]
CONTEXTS = ["web applications", "microservices", "mobile apps", "desktop apps", "cloud services"]
FEATURES = ["authentication", "authorization", "caching", "rate limiting", "logging", "monitoring"]

def generate_random_string(length: int) -> str:
    """Generate a random string of specified length"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_question() -> Dict[str, Any]:
    """Generate a random question with sample answer"""
    template = random.choice(QUESTION_TEMPLATES)
    
    # Fill in the template with random values
    question_text = template.format(
        algorithm=random.choice(ALGORITHMS),
        concept=random.choice(CONCEPTS),
        language=random.choice(LANGUAGES),
        tech1=random.choice(TECHNOLOGIES),
        tech2=random.choice(TECHNOLOGIES),
        topic=random.choice(TOPICS),
        context=random.choice(CONTEXTS),
        feature=random.choice(FEATURES)
    )
    
    # Generate a sample answer
    answer_length = random.randint(100, 500)
    sample_answer = f"This is a sample answer for the question: {question_text}. " + \
                   f"Here is some additional text to make the answer longer. " * (answer_length // 50)
    
    return {
        "id": f"q_{generate_random_string(8)}",
        "text": question_text,
        "sample_answer": sample_answer,
        "category": random.choice(["algorithms", "system design", "language-specific", "general"]),
        "difficulty": random.choice(["easy", "medium", "hard"])
    }

def main():
    print(f"Generating {NUM_QUESTIONS} test questions...")
    
    questions = []
    
    for i in range(NUM_QUESTIONS):
        question = generate_question()
        questions.append(question)
        print(f"Generated question {i+1}/{NUM_QUESTIONS}: {question['text'][:50]}...")
    
    # Save questions to file
    with open(QUESTIONS_FILE, 'w') as f:
        json.dump(questions, f, indent=2)
    
    print(f"\nSuccessfully generated {NUM_QUESTIONS} test questions")
    print(f"Test questions saved to {QUESTIONS_FILE}")

if __name__ == "__main__":
    main() 