import requests
import threading
import time
import random
import json
from datetime import datetime
import statistics
import queue
import argparse
from typing import List, Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{BASE_URL}/api/auth/login"
SUBMIT_QUESTION_ENDPOINT = f"{BASE_URL}/api/questions/submit"
USERS_FILE = "test_users.json"

# Global variables for statistics
successful_submissions = 0
failed_submissions = 0
response_times = []
lock = threading.Lock()
results_queue = queue.Queue()

def load_test_users() -> List[Dict[str, str]]:
    """Load test users from JSON file"""
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {USERS_FILE} not found. Please run create_test_users.py first.")
        exit(1)

def login_user(user: Dict[str, str]) -> str:
    """Login a user and return the token"""
    try:
        response = requests.post(
            LOGIN_ENDPOINT,
            json={
                "email": user["email"],
                "password": user["password"]
            },
            timeout=10
        )
        if response.status_code == 200:
            return response.json().get("token")
        return None
    except Exception:
        return None

def generate_question() -> Dict[str, Any]:
    """Generate a random question"""
    # Sample question templates
    templates = [
        "What is the time complexity of {algorithm}?",
        "Explain how {concept} works in {language}.",
        "What are the main differences between {tech1} and {tech2}?",
        "How would you implement {feature} in {language}?",
        "What are the best practices for {topic} in {context}?"
    ]
    
    # Sample fillers
    algorithms = ["quicksort", "mergesort", "binary search", "Dijkstra's algorithm", "BFS", "DFS"]
    concepts = ["inheritance", "polymorphism", "recursion", "closures", "async/await", "promises"]
    languages = ["Python", "JavaScript", "Java", "C++", "Go", "Rust"]
    technologies = ["REST", "GraphQL", "WebSocket", "gRPC", "RPC", "SOAP"]
    topics = ["error handling", "logging", "testing", "deployment", "security", "performance"]
    contexts = ["web applications", "microservices", "mobile apps", "desktop apps", "cloud services"]
    
    template = random.choice(templates)
    question_text = template.format(
        algorithm=random.choice(algorithms),
        concept=random.choice(concepts),
        language=random.choice(languages),
        tech1=random.choice(technologies),
        tech2=random.choice(technologies),
        topic=random.choice(topics),
        context=random.choice(contexts)
    )
    
    return {
        "text": question_text,
        "category": random.choice(["algorithms", "system design", "language-specific", "general"]),
        "difficulty": random.choice(["easy", "medium", "hard"]),
        "tags": random.sample(["programming", "algorithms", "data-structures", "system-design", "testing"], k=random.randint(1, 3))
    }

def submit_question(token: str, question: Dict[str, Any]) -> Dict[str, Any]:
    """Submit a question"""
    start_time = time.time()
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            SUBMIT_QUESTION_ENDPOINT,
            json=question,
            headers=headers,
            timeout=10
        )
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        return {
            "success": response.status_code == 201,
            "response_time": response_time,
            "status_code": response.status_code
        }
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "response_time": (end_time - start_time) * 1000,
            "error": str(e)
        }

def worker(users: List[Dict[str, str]], num_requests: int):
    """Worker thread function to perform question submission attempts"""
    for _ in range(num_requests):
        # Select random user
        user = random.choice(users)
        
        # Login to get token
        token = login_user(user)
        if not token:
            continue
        
        # Generate and submit question
        question = generate_question()
        result = submit_question(token, question)
        results_queue.put(result)

def run_load_test(num_threads: int, requests_per_thread: int, users: List[Dict[str, str]]):
    """Run the load test with specified number of threads"""
    global successful_submissions, failed_submissions, response_times
    
    print(f"\nStarting load test with {num_threads} threads, {requests_per_thread} requests per thread")
    print(f"Total requests: {num_threads * requests_per_thread}")
    print(f"Test users available: {len(users)}")
    
    threads = []
    start_time = time.time()
    
    # Create and start threads
    for _ in range(num_threads):
        thread = threading.Thread(
            target=worker,
            args=(users, requests_per_thread)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Process results
    while not results_queue.empty():
        result = results_queue.get()
        with lock:
            if result["success"]:
                successful_submissions += 1
            else:
                failed_submissions += 1
            response_times.append(result["response_time"])
    
    # Calculate statistics
    total_requests = successful_submissions + failed_submissions
    requests_per_second = total_requests / total_time
    avg_response_time = statistics.mean(response_times) if response_times else 0
    p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else 0
    
    # Print results
    print("\nLoad Test Results:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Total requests: {total_requests}")
    print(f"Successful submissions: {successful_submissions}")
    print(f"Failed submissions: {failed_submissions}")
    print(f"Average response time: {avg_response_time:.2f} ms")
    print(f"95th percentile response time: {p95_response_time:.2f} ms")
    print(f"Requests per second: {requests_per_second:.2f}")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"question_submission_load_test_results_{timestamp}.json"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_time": total_time,
        "total_requests": total_requests,
        "successful_submissions": successful_submissions,
        "failed_submissions": failed_submissions,
        "average_response_time": avg_response_time,
        "p95_response_time": p95_response_time,
        "response_times": response_times,
        "requests_per_second": requests_per_second
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to {results_file}")

def main():
    parser = argparse.ArgumentParser(description='Run question submission load test')
    parser.add_argument('--threads', type=int, default=50,
                      help='Number of concurrent threads (default: 50)')
    parser.add_argument('--requests', type=int, default=10,
                      help='Number of requests per thread (default: 10)')
    
    args = parser.parse_args()
    
    users = load_test_users()
    run_load_test(args.threads, args.requests, users)

if __name__ == "__main__":
    main() 