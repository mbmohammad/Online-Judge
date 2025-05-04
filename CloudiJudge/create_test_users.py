import json
import random
import string
from typing import List, Dict

USERS_FILE = "test_users.json"
NUM_USERS = 100  # Number of test users to create

def generate_random_string(length: int) -> str:
    """Generate a random string of specified length"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def create_test_user() -> Dict[str, str]:
    """Create a single test user with random credentials"""
    username = f"test_user_{generate_random_string(8)}"
    email = f"{username}@example.com"
    password = generate_random_string(12)
    
    return {
        "email": email,
        "password": password
    }

def main():
    print(f"Generating {NUM_USERS} test users...")
    
    test_users = []
    
    for i in range(NUM_USERS):
        user = create_test_user()
        test_users.append(user)
        print(f"Generated user {i+1}/{NUM_USERS}: {user['email']}")
    
    # Save test users to file
    with open(USERS_FILE, 'w') as f:
        json.dump(test_users, f, indent=2)
    
    print(f"\nSuccessfully generated {NUM_USERS} test users")
    print(f"Test users saved to {USERS_FILE}")

if __name__ == "__main__":
    main() 