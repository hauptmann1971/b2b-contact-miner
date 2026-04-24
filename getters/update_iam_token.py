"""
Quick script to get new IAM token and update .env
"""
import requests
import os


def get_iam_token(oauth_token: str) -> str:
    """Exchange OAuth token for IAM token"""
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "yandexPassportOauthToken": oauth_token
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        return result.get("iamToken", "")
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")


if __name__ == "__main__":
    oauth_token = os.getenv("YANDEX_OAUTH_TOKEN") or input("Enter Yandex OAuth token: ").strip()
    if not oauth_token:
        raise ValueError("OAuth token is required. Set YANDEX_OAUTH_TOKEN or provide it interactively.")
    
    print("Getting new IAM token...")
    iam_token = get_iam_token(oauth_token)
    
    print(f"IAM Token: {iam_token[:30]}...")
    
    # Update .env
    env_path = "c:\\Users\\romanov\\PycharmProjects\\b2b-contact-miner\\.env"
    
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace old token with new one
    import re
    pattern = r'YANDEX_IAM_TOKEN=.*'
    replacement = f'YANDEX_IAM_TOKEN={iam_token}'
    content = re.sub(pattern, replacement, content)
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ .env updated with new IAM token!")
    print("\nNow testing connection...")
