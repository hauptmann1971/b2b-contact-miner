"""Exchange OAuth token for IAM token"""
import requests
import sys

def exchange_oauth_for_iam(oauth_token: str):
    """Exchange Yandex OAuth token for IAM token"""
    
    print("Exchanging OAuth token for IAM token...")
    
    response = requests.post(
        'https://iam.api.cloud.yandex.net/iam/v1/tokens',
        headers={'Content-Type': 'application/json'},
        json={'yandexPassportOauthToken': oauth_token}
    )
    
    if response.status_code == 200:
        data = response.json()
        iam_token = data['iamToken']
        expires_at = data.get('expiresAt', 'unknown')
        
        print("\n✅ Success!")
        print(f"\nNew IAM Token:")
        print(iam_token)
        print(f"\nExpires at: {expires_at}")
        print("\n⚠️  Copy this token and update your .env file:")
        print(f"YANDEX_IAM_TOKEN={iam_token}")
        
        return iam_token
    else:
        print(f"❌ Error: HTTP {response.status_code}")
        print(f"Response: {response.text}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        oauth_token = sys.argv[1]
        exchange_oauth_for_iam(oauth_token)
    else:
        print("Usage: python exchange_oauth_token.py <YOUR_OAUTH_TOKEN>")
        print("\nTo get OAuth token:")
        print("1. Go to: https://oauth.yandex.ru/authorize?response_type=token&client_id=1a6990aa636648e9b2ef855fa7bec2fb")
        print("2. Authorize")
        print("3. Copy the token from URL (#token=...)")
        print("4. Run: python exchange_oauth_token.py YOUR_TOKEN")
