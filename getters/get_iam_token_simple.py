"""
Get IAM token from API key using direct HTTP request
"""
import requests
from config.settings import settings


def get_iam_token(api_key: str) -> str:
    """Get IAM token using Service Account API Key"""
    
    # Method 1: Try using API key in Authorization header
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    
    headers = {
        "Authorization": f"Api-Key {api_key}",
        "Content-Type": "application/json"
    }
    
    print("   Trying to get IAM token with API key...")
    
    try:
        response = requests.post(url, headers=headers, json={})
        
        if response.status_code == 200:
            result = response.json()
            return result.get("iamToken", "")
        else:
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"   Error: {e}")
        return None


def main():
    print("="*60)
    print("Get IAM Token from Service Account API Key")
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
        return
    
    print(f"\nAPI Key: {api_key[:8]}...")
    print("\nRequesting IAM token from Yandex Cloud...")
    
    iam_token = get_iam_token(api_key)
    
    if iam_token:
        print(f"\n✅ Success!")
        print(f"\nIAM Token: {iam_token[:30]}...")
        print(f"Token length: {len(iam_token)} characters")
        
        # Get folder ID
        print("\n⚠️  Folder ID required!")
        print("You can find it at: https://console.cloud.yandex.ru/")
        print("Look for 'Folder ID' in your cloud settings")
        print("\nEnter Folder ID (looks like: b1gxxxxxxxxxxxx):")
        folder_id = input("> ").strip()
        
        if folder_id:
            print(f"\nUpdating .env file...")
            
            # Update .env
            env_path = "c:\\Users\\romanov\\PycharmProjects\\b2b-contact-miner\\.env"
            
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
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
                print("\nNow test the connection:")
                print("python test_yandexgpt.py")
                
            except Exception as e:
                print(f"\n❌ Error updating .env: {e}")
                print(f"\nPlease manually update .env:")
                print(f"YANDEX_IAM_TOKEN={iam_token}")
                print(f"YANDEX_FOLDER_ID={folder_id}")
        else:
            print("\n⚠️  Please manually update .env file:")
            print(f"YANDEX_IAM_TOKEN={iam_token}")
            print("YANDEX_FOLDER_ID=your_folder_id_here")
    else:
        print(f"\n❌ Failed to get IAM token")
        print("\nPossible issues:")
        print("1. API key is invalid or expired")
        print("2. API key format is incorrect")
        print("3. Service account doesn't have proper permissions")
        print("\nNote: The key 'aje59uvsgfu9u518set8' looks short.")
        print("Service Account API keys usually start with 'AQVN...' and are longer.")
        print("\nPlease check your credentials at: https://console.cloud.yandex.ru/")
        print("\nAlternatively, you can use OAuth token from Yandex Passport.")


if __name__ == "__main__":
    main()
