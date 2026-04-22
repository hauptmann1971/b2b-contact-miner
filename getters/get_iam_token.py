"""
Simple script to get IAM token from API key using yandexcloud SDK
"""
from yandex.iam import create_iam_token_for_api_key
from config.settings import settings


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
    print("\nGetting IAM token...")
    
    try:
        iam_token = create_iam_token_for_api_key(api_key)
        
        print(f"\n✅ Success!")
        print(f"\nIAM Token: {iam_token[:30]}...")
        print(f"Token length: {len(iam_token)} characters")
        
        # Get folder ID
        folder_id = input("\nEnter your Folder ID (or press Enter to skip): ").strip()
        
        if folder_id:
            print(f"\nFolder ID: {folder_id}")
            
            # Update .env
            env_path = "c:\\Users\\romanov\\PycharmProjects\\b2b-contact-miner\\.env"
            
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
            
            print(f"\n✅ .env file updated!")
            print("\nNow test the connection:")
            print("python test_yandexgpt.py")
        else:
            print("\n⚠️  Please manually update .env file:")
            print(f"YANDEX_IAM_TOKEN={iam_token}")
            print("YANDEX_FOLDER_ID=your_folder_id_here")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: Make sure the API key is valid and active.")
        print("You can check at: https://console.cloud.yandex.ru/")


if __name__ == "__main__":
    main()
