"""
Get IAM token from API key and update .env file
"""
import requests
import json
from config.settings import settings


def get_iam_token_from_api_key(api_key: str) -> str:
    """Exchange Service Account API Key for IAM token"""
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # For Service Account API Key
    payload = {
        "yandexPassportOauthToken": api_key
    }
    
    try:
        print("   Trying OAuth token method...")
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            iam_token = result.get("iamToken")
            if iam_token:
                return iam_token
        
        # If OAuth method failed, try API Key method
        print("   OAuth method failed, trying API Key method...")
        url_key = "https://iam.api.cloud.yandex.net/iam/v1/apiKeys"
        
        headers_key = {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json"
        }
        
        # First get the service account ID
        response_sa = requests.get(
            "https://iam.api.cloud.yandex.net/iam/v1/serviceAccounts",
            headers=headers_key
        )
        
        if response_sa.status_code != 200:
            raise Exception(f"Failed to authenticate with API key: {response_sa.text}")
        
        # Create IAM token using the API key directly
        url_token = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
        payload_token = {
            "yandexPassportOauthToken": api_key  # This won't work for API keys
        }
        
        # Actually, for API keys we need to use a different approach
        # Let's use the yandexcloud SDK
        from yandex.iam import create_iam_token_for_api_key
        
        iam_token = create_iam_token_for_api_key(api_key)
        return iam_token
        
    except ImportError:
        print("   yandexcloud SDK not available, trying direct API...")
        # Fallback: try to use API key directly in requests
        raise Exception("Please use OAuth token instead of API key, or install yandexcloud SDK properly")
        
    except Exception as e:
        print(f"❌ Error getting IAM token: {e}")
        raise


def get_folder_id():
    """Get folder ID from user input or existing config"""
    if settings.YANDEX_FOLDER_ID and settings.YANDEX_FOLDER_ID != "your_yandex_folder_id":
        return settings.YANDEX_FOLDER_ID
    
    print("\n⚠️  Folder ID required!")
    print("You can find it in Yandex Cloud Console:")
    print("1. Go to https://console.cloud.yandex.ru/")
    print("2. Select your cloud")
    print("3. Copy Folder ID (looks like: b1gxxxxxxxxxxxx)")
    print("\nEnter Folder ID:")
    folder_id = input("> ").strip()
    
    if not folder_id:
        raise Exception("Folder ID is required")
    
    return folder_id


def update_env_file(iam_token: str, folder_id: str):
    """Update .env file with new credentials"""
    env_path = "c:\\Users\\romanov\\PycharmProjects\\b2b-contact-miner\\.env"
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace placeholders
        content = content.replace(
            "YANDEX_IAM_TOKEN=your_yandex_iam_token",
            f"YANDEX_IAM_TOKEN={iam_token}"
        )
        content = content.replace(
            "YANDEX_FOLDER_ID=your_yandex_folder_id",
            f"YANDEX_FOLDER_ID={folder_id}"
        )
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ .env file updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating .env: {e}")
        raise


if __name__ == "__main__":
    print("="*60)
    print("YandexGPT Setup - Get IAM Token from API Key")
    print("="*60)
    
    # Get API key from environment variable (SECURITY: never hard-code secrets)
    import os
    api_key = os.getenv('YANDEX_API_KEY')
    
    if not api_key:
        print("\n❌ Error: YANDEX_API_KEY environment variable not set!")
        print("\nSet it with:")
        print("  export YANDEX_API_KEY=your_api_key_here  # Linux/Mac")
        print("  set YANDEX_API_KEY=your_api_key_here     # Windows CMD")
        print("  $env:YANDEX_API_KEY='your_api_key_here'  # PowerShell")
        exit(1)
    
    print(f"\n1. Using API Key: {api_key[:8]}...")
    
    try:
        print("\n2. Exchanging API key for IAM token...")
        iam_token = get_iam_token_from_api_key(api_key)
        print(f"   ✅ IAM Token received: {iam_token[:20]}...")
        
        print("\n3. Getting Folder ID...")
        folder_id = get_folder_id()
        print(f"   ✅ Folder ID: {folder_id}")
        
        print("\n4. Updating .env file...")
        update_env_file(iam_token, folder_id)
        
        print("\n" + "="*60)
        print("✅ Setup Complete!")
        print("="*60)
        print("\nNow you can test the connection:")
        print("python test_yandexgpt.py")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\nNote: The API key format might be incorrect.")
        print("For YandexGPT, you need:")
        print("1. Service Account API Key (starts with 'AQVN...')")
        print("   OR")
        print("2. OAuth Token from Yandex Passport")
        print("\nPlease check your credentials at: https://console.cloud.yandex.ru/")
