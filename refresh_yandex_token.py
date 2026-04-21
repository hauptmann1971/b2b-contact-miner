"""Refresh Yandex IAM Token"""
import requests
import json
from config.settings import settings

def refresh_iam_token():
    """Get new IAM token using OAuth token or service account"""
    
    print("=" * 80)
    print("YANDEX IAM TOKEN REFRESH")
    print("=" * 80)
    
    if not settings.YANDEX_IAM_TOKEN:
        print("\n❌ No current IAM token found in .env")
        print("\nTo get a new token:")
        print("1. Go to https://cloud.yandex.ru/console")
        print("2. Click on your profile avatar → 'Security'")
        print("3. Create OAuth token or use service account")
        print("4. Run one of these commands:")
        print("\n   Option A - Using yc CLI:")
        print("   yc iam create-token")
        print("\n   Option B - Using curl with OAuth token:")
        print("   curl -X POST 'https://iam.api.cloud.yandex.net/iam/v1/tokens' \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"yandexPassportOauthToken\": \"YOUR_OAUTH_TOKEN\"}'")
        return
    
    print(f"\nCurrent token (first 50 chars): {settings.YANDEX_IAM_TOKEN[:50]}...")
    print(f"Folder ID: {settings.YANDEX_FOLDER_ID}")
    
    # Test if token is still valid
    print("\nTesting current token...")
    try:
        response = requests.post(
            'https://iam.api.cloud.yandex.net/iam/v1/tokens',
            headers={'Content-Type': 'application/json'},
            json={'yandexIamToken': settings.YANDEX_IAM_TOKEN}
        )
        
        if response.status_code == 200:
            print("✅ Token is still valid!")
            data = response.json()
            expires_at = data.get('expiresAt', 'unknown')
            print(f"   Expires at: {expires_at}")
        else:
            print(f"❌ Token expired or invalid (HTTP {response.status_code})")
            print(f"   Response: {response.text[:200]}")
            print("\n🔄 Need to get a new token!")
            print("\nQuick way to get new token:")
            print("1. Install yc CLI: https://cloud.yandex.ru/docs/cli/quickstart")
            print("2. Login: yc init")
            print("3. Get token: yc iam create-token")
            print("4. Copy the token and update .env file")
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    refresh_iam_token()
