"""
Test YandexGPT API connection
Run this after setting YANDEX credentials in .env
"""
import requests
from config.settings import settings


def test_yandexgpt():
    """Test YandexGPT API connection"""
    print("="*60)
    print("Testing YandexGPT API Connection")
    print("="*60)
    
    if not settings.YANDEX_IAM_TOKEN or settings.YANDEX_IAM_TOKEN == "your_yandex_iam_token":
        print("\n❌ YANDEX_IAM_TOKEN not set!")
        print("\nPlease:")
        print("1. Get credentials from: https://cloud.yandex.ru/services/yandexgpt")
        print("2. Update .env file with your credentials")
        print("3. Run this script again")
        return False
    
    try:
        print(f"\n1. Configuration:")
        print(f"   Folder ID: {settings.YANDEX_FOLDER_ID}")
        print(f"   IAM Token: {settings.YANDEX_IAM_TOKEN[:10]}...")
        
        url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.YANDEX_IAM_TOKEN}",
            "x-folder-id": settings.YANDEX_FOLDER_ID
        }
        
        payload = {
            "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt/latest",
            "completionOptions": {
                "stream": False,
                "temperature": 0.7,
                "maxTokens": "50"
            },
            "messages": [
                {"role": "user", "text": "Привет! Напиши короткое приветствие на русском."}
            ]
        }
        
        print("\n2. Sending test request...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        text = result["result"]["alternatives"][0]["message"]["text"]
        
        print("   ✅ Request successful")
        
        print("\n3. Response:")
        print("-" * 60)
        print(text)
        print("-" * 60)
        
        print("\n✅ YandexGPT API is working correctly!")
        print(f"\nModel: YandexGPT")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check IAM_TOKEN and FOLDER_ID in .env")
        print("2. Verify service account has ai.languageModels.user role")
        print("3. Check if IAM token expired (lives 12 hours)")
        print("4. Verify billing account is active")
        return False


if __name__ == "__main__":
    import sys
    success = test_yandexgpt()
    sys.exit(0 if success else 1)
