"""
Simple DeepSeek test with minimal parameters
"""
from openai import OpenAI
from config.settings import settings

print("Testing DeepSeek API...")
print(f"API Key: {settings.DEEPSEEK_API_KEY[:10]}...")

client = OpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

try:
    # Check balance/account status
    print("\nTrying simple completion...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Hi"}],
        max_tokens=5
    )
    print("✅ Success!")
    print(f"Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nPossible solutions:")
    print("1. Check your DeepSeek account balance at https://platform.deepseek.com")
    print("2. You may need to add credits (even small amount)")
    print("3. Verify account is activated")
    print("4. Contact DeepSeek support if issue persists")
