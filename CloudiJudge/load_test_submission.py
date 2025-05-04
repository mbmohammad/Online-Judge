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
SUBMIT_ANSWER_ENDPOINT = f"{BASE_URL}/api/answers/submit"
GET_ANSWER_ENDPOINT = f"{BASE_URL}/api/answers"  # This will need the answer ID
USERS_FILE = "test_users.json"
QUESTIONS_FILE = "test_questions.json"

# Global variables for statistics
successful_submissions = 0
failed_submissions = 0
successful_retrievals = 0
failed_retrievals = 0
submission_times = []
retrieval_times = []
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

def load_test_questions() -> List[Dict[str, Any]]:
    """Load test questions from JSON file"""
    try:
        with open(QUESTIONS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {QUESTIONS_FILE} not found. Please create test questions first.")
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

def submit_answer(token: str, question: Dict[str, Any]) -> Dict[str, Any]:
    """Submit an answer for a question"""
    start_time = time.time()
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            SUBMIT_ANSWER_ENDPOINT,
            json={
                "question_id": question["id"],
                "answer": question["sample_answer"]
            },
            headers=headers,
            timeout=10
        )
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        result = {
            "type": "submission",
            "success": response.status_code == 201,
            "response_time": response_time,
            "status_code": response.status_code
        }
        
        if response.status_code == 201:
            result["answer_id"] = response.json().get("id")
        
        return result
    except Exception as e:
        end_time = time.time()
        return {
            "type": "submission",
            "success": False,
            "response_time": (end_time - start_time) * 1000,
            "error": str(e)
        }

def get_answer(token: str, answer_id: str) -> Dict[str, Any]:
    """Retrieve an answer by ID"""
    start_time = time.time()
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{GET_ANSWER_ENDPOINT}/{answer_id}",
            headers=headers,
            timeout=10
        )
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        return {
            "type": "retrieval",
            "success": response.status_code == 200,
            "response_time": response_time,
            "status_code": response.status_code
        }
    except Exception as e:
        end_time = time.time()
        return {
            "type": "retrieval",
            "success": False,
            "response_time": (end_time - start_time) * 1000,
            "error": str(e)
        }

def worker(users: List[Dict[str, str]], questions: List[Dict[str, Any]], num_requests: int):
    """Worker thread function to perform submission and retrieval attempts"""
    for _ in range(num_requests):
        # Select random user and question
        user = random.choice(users)
        question = random.choice(questions)
        
        # Login to get token
        token = login_user(user)
        if not token:
            continue
        
        # Submit answer
        submission_result = submit_answer(token, question)
        results_queue.put(submission_result)
        
        # If submission was successful, try to retrieve the answer
        if submission_result.get("success") and "answer_id" in submission_result:
            retrieval_result = get_answer(token, submission_result["answer_id"])
            results_queue.put(retrieval_result)

def run_load_test(num_threads: int, requests_per_thread: int, users: List[Dict[str, str]], questions: List[Dict[str, Any]]):
    """Run the load test with specified number of threads"""
    global successful_submissions, failed_submissions, successful_retrievals, failed_retrievals
    global submission_times, retrieval_times
    
    print(f"\nStarting load test with {num_threads} threads, {requests_per_thread} requests per thread")
    print(f"Total requests: {num_threads * requests_per_thread}")
    print(f"Test users available: {len(users)}")
    print(f"Test questions available: {len(questions)}")
    
    threads = []
    start_time = time.time()
    
    # Create and start threads
    for _ in range(num_threads):
        thread = threading.Thread(
            target=worker,
            args=(users, questions, requests_per_thread)
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
            if result["type"] == "submission":
                if result["success"]:
                    successful_submissions += 1
                else:
                    failed_submissions += 1
                submission_times.append(result["response_time"])
            else:  # retrieval
                if result["success"]:
                    successful_retrievals += 1
                else:
                    failed_retrievals += 1
                retrieval_times.append(result["response_time"])
    
    # Calculate statistics
    total_submissions = successful_submissions + failed_submissions
    total_retrievals = successful_retrievals + failed_retrievals
    total_requests = total_submissions + total_retrievals
    
    requests_per_second = total_requests / total_time
    avg_submission_time = statistics.mean(submission_times) if submission_times else 0
    avg_retrieval_time = statistics.mean(retrieval_times) if retrieval_times else 0
    
    p95_submission_time = statistics.quantiles(submission_times, n=20)[18] if len(submission_times) >= 20 else 0
    p95_retrieval_time = statistics.quantiles(retrieval_times, n=20)[18] if len(retrieval_times) >= 20 else 0
    
    # Print results
    print("\nLoad Test Results:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Total requests: {total_requests}")
    print("\nSubmissions:")
    print(f"  Successful: {successful_submissions}")
    print(f"  Failed: {failed_submissions}")
    print(f"  Average response time: {avg_submission_time:.2f} ms")
    print(f"  95th percentile response time: {p95_submission_time:.2f} ms")
    print("\nRetrievals:")
    print(f"  Successful: {successful_retrievals}")
    print(f"  Failed: {failed_retrievals}")
    print(f"  Average response time: {avg_retrieval_time:.2f} ms")
    print(f"  95th percentile response time: {p95_retrieval_time:.2f} ms")
    print(f"\nOverall requests per second: {requests_per_second:.2f}")
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"submission_load_test_results_{timestamp}.json"
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_time": total_time,
        "total_requests": total_requests,
        "submissions": {
            "successful": successful_submissions,
            "failed": failed_submissions,
            "average_response_time": avg_submission_time,
            "p95_response_time": p95_submission_time,
            "response_times": submission_times
        },
        "retrievals": {
            "successful": successful_retrievals,
            "failed": failed_retrievals,
            "average_response_time": avg_retrieval_time,
            "p95_response_time": p95_retrieval_time,
            "response_times": retrieval_times
        },
        "requests_per_second": requests_per_second
    }
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to {results_file}")

def main():
    parser = argparse.ArgumentParser(description='Run submission load test')
    parser.add_argument('--threads', type=int, default=50,
                      help='Number of concurrent threads (default: 50)')
    parser.add_argument('--requests', type=int, default=10,
                      help='Number of requests per thread (default: 10)')
    
    args = parser.parse_args()
    
    users = load_test_users()
    questions = load_test_questions()
    run_load_test(args.threads, args.requests, users, questions)

if __name__ == "__main__":
    main() 