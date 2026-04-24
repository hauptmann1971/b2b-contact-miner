"""
Get IAM token from Yandex Passport OAuth token
"""
import requests
import os


def get_iam_token_from_oauth(oauth_token: str) -> str:
    """Exchange OAuth token for IAM token"""
    url = "https://iam.api.cloud.yandex.net/iam/v1/tokens"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "yandexPassportOauthToken": oauth_token
    }
    
    print("Exchanging OAuth token for IAM token...")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            iam_token = result.get("iamToken", "")
            
            if iam_token:
                print(f"✅ Success!")
                print(f"IAM Token: {iam_token[:30]}...")
                return iam_token
            else:
                print("❌ No IAM token in response")
                return None
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


if __name__ == "__main__":
    oauth_token = os.getenv("YANDEX_OAUTH_TOKEN") or input("Enter Yandex OAuth token: ").strip()
    if not oauth_token:
        raise ValueError("OAuth token is required. Set YANDEX_OAUTH_TOKEN or provide it interactively.")
    
    print("="*60)
    print("Get IAM Token from Yandex OAuth Token")
    print("="*60)
    print(f"\nOAuth Token: {oauth_token[:15]}...")
    
    iam_token = get_iam_token_from_oauth(oauth_token)
    
    if iam_token:
        print("\n⚠️  Now I need your Folder ID!")
        print("You can find it at: https://console.cloud.yandex.ru/")
        print("Look for 'Folder ID' (looks like: b1gxxxxxxxxxxxx)")
        print("\nEnter Folder ID:")
        folder_id = input("> ").strip()
        
        if folder_id:
            # Update .env file
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
                print(f"\nIAM Token: {iam_token[:30]}...")
                print(f"Folder ID: {folder_id}")
                print("\nNow test the connection:")
                print("python test_yandexgpt.py")
                
            except Exception as e:
                print(f"\n❌ Error updating .env: {e}")
                print(f"\nPlease manually update .env:")
                print(f"YANDEX_IAM_TOKEN={iam_token}")
                print(f"YANDEX_FOLDER_ID={folder_id}")
        else:
            print("\n⚠️  Please provide Folder ID to continue")
    else:
        print("\n❌ Failed to get IAM token")
        print("\nPossible issues:")
        print("1. OAuth token is invalid or expired")
        print("2. OAuth token format is incorrect")
        print("3. Account doesn't have access to Yandex Cloud")
