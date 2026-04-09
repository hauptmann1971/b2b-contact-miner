"""
Test GigaChat API connection
Run this after setting GIGACHAT credentials in .env
"""
from gigachat import GigaChat
from gigachat.models import Messages
from config.settings import settings


def test_gigachat():
    """Test GigaChat API connection"""
    print("="*60)
    print("Testing GigaChat API Connection")
    print("="*60)
    
    if not settings.GIGACHAT_CLIENT_ID or settings.GIGACHAT_CLIENT_ID == "your_gigachat_client_id":
        print("\n❌ GIGACHAT_CLIENT_ID not set!")
        print("\nPlease:")
        print("1. Get credentials from: https://developers.sber.ru/gigachat")
        print("2. Update .env file with your credentials")
        print("3. Run this script again")
        return False
    
    try:
        print(f"\n1. Initializing GigaChat client...")
        print(f"   Client ID: {settings.GIGACHAT_CLIENT_ID[:8]}...")
        
        gc = GigaChat(
            credentials=settings.GIGACHAT_CLIENT_ID,
            client_secret=settings.GIGACHAT_CLIENT_SECRET,
            verify_ssl_certs=False,
            scope="GIGACHAT_API_PERS",
            model="GigaChat-Pro"
        )
        
        # Get access token
        print("   Getting access token...")
        gc.get_token()
        print("   ✅ Token received")
        print("   ✅ Client initialized")
        
        print("\n2. Sending test request...")
        response = gc.chat(
            messages=[{"role": "user", "content": "Привет! Напиши короткое приветствие на русском."}],
            temperature=0.7,
            max_tokens=50
        )
        print("   ✅ Request successful")
        
        print("\n3. Response:")
        print("-" * 60)
        print(response.choices[0].message.content)
        print("-" * 60)
        
        print("\n✅ GigaChat API is working correctly!")
        print(f"\nModel: GigaChat")
        print(f"Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check CLIENT_ID and CLIENT_SECRET in .env")
        print("2. Verify account is activated at developers.sber.ru")
        print("3. Check internet connection")
        print("4. Verify project status in Sber Developers portal")
        return False


if __name__ == "__main__":
    import sys
    success = test_gigachat()
    sys.exit(0 if success else 1)
