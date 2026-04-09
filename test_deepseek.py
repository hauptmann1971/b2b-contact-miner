"""
Test DeepSeek API connection
Run this after setting DEEPSEEK_API_KEY in .env
"""
from openai import OpenAI
from config.settings import settings


def test_deepseek():
    """Test DeepSeek API connection"""
    print("="*60)
    print("Testing DeepSeek API Connection")
    print("="*60)
    
    if not settings.DEEPSEEK_API_KEY or settings.DEEPSEEK_API_KEY == "your_deepseek_key_here":
        print("\n❌ DEEPSEEK_API_KEY not set!")
        print("\nPlease:")
        print("1. Get API key from: https://platform.deepseek.com")
        print("2. Update .env file with your key")
        print("3. Run this script again")
        return False
    
    try:
        print(f"\n1. Initializing client...")
        client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com/v1"
        )
        print("   ✅ Client initialized")
        
        print("\n2. Sending test request...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "user", "content": "Say hello in Russian and English"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        print("   ✅ Request successful")
        
        print("\n3. Response:")
        print("-" * 60)
        print(response.choices[0].message.content)
        print("-" * 60)
        
        print("\n✅ DeepSeek API is working correctly!")
        print(f"\nModel: deepseek-chat")
        print(f"Tokens used: {response.usage.total_tokens}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check your API key is correct")
        print("2. Verify internet connection")
        print("3. Try using VPN if DeepSeek is blocked in your region")
        print("4. Check DeepSeek status: https://status.deepseek.com")
        return False


if __name__ == "__main__":
    import sys
    success = test_deepseek()
    sys.exit(0 if success else 1)
