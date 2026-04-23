"""Test YandexGPT token with actual API call"""
import requests
from config.settings import settings

def test_yandexgpt_token():
    """Test IAM token by making a simple request to YandexGPT"""
    
    print("=" * 80)
    print("YANDEXGPT TOKEN TEST")
    print("=" * 80)
    
    if not settings.YANDEX_IAM_TOKEN:
        print("\n❌ No IAM token in .env")
        return False
    
    if not settings.YANDEX_FOLDER_ID:
        print("\n❌ No folder ID in .env")
        return False
    
    print(f"\nToken (first 30 chars): {settings.YANDEX_IAM_TOKEN[:30]}...")
    print(f"Folder ID: {settings.YANDEX_FOLDER_ID}")
    
    # Test with YandexGPT API
    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    headers = {
        'Authorization': f'Bearer {settings.YANDEX_IAM_TOKEN}',
        'Content-Type': 'application/json',
        'x-folder-id': settings.YANDEX_FOLDER_ID
    }
    
    data = {
        "modelUri": f"gpt://{settings.YANDEX_FOLDER_ID}/yandexgpt/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.5,
            "maxTokens": "50"
        },
        "messages": [
            {
                "role": "user",
                "text": "Привет! Напиши коротко: OK"
            }
        ]
    }
    
    print("\nTesting YandexGPT API...")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('result', {}).get('alternatives', [{}])[0].get('message', {}).get('text', '')
            
            print(f"\n✅ Token is VALID!")
            print(f"   YandexGPT response: {text}")
            print(f"\n🎉 You can now run the pipeline!")
            return True
        else:
            print(f"\n❌ Token invalid (HTTP {response.status_code})")
            print(f"   Error: {response.text[:300]}")
            
            if response.status_code == 401:
                print("\n⚠️  Token expired or invalid")
                print("   Get new token from: https://cloud.yandex.ru/console")
            elif response.status_code == 403:
                print("\n⚠️  Access denied")
                print("   Check that folder ID is correct and you have permissions")
            
            return False
            
    except Exception as e:
        print(f"\n❌ Error testing token: {e}")
        return False

if __name__ == "__main__":
    test_yandexgpt_token()
