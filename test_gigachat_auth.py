"""
Test GigaChat with direct API call to debug auth issue
"""
import requests
import base64
from config.settings import settings

print("Testing GigaChat Authentication...")
print(f"Client ID: {settings.GIGACHAT_CLIENT_ID}")
print(f"Client Secret length: {len(settings.GIGACHAT_CLIENT_SECRET)}")

# Try to get OAuth token
url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

# Create authorization header
auth_string = f"{settings.GIGACHAT_CLIENT_ID}:{settings.GIGACHAT_CLIENT_SECRET}"
auth_bytes = base64.b64encode(auth_string.encode()).decode()

headers = {
    'Authorization': f'Basic {auth_bytes}',
    'RqUID': 'test-request-id-12345',
    'Content-Type': 'application/x-www-form-urlencoded'
}

payload = {
    'scope': 'GIGACHAT_API_PERS'
}

print("\nAttempting to get OAuth token...")
try:
    response = requests.post(url, headers=headers, data=payload, verify=False)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        token_data = response.json()
        print(f"\n✅ Success! Token received:")
        print(f"Access token: {token_data.get('access_token', '')[:20]}...")
        print(f"Expires in: {token_data.get('expires_at', 'N/A')}")
    else:
        print(f"\n❌ Failed to get token")
        print("\nPossible issues:")
        print("1. Invalid CLIENT_ID or CLIENT_SECRET")
        print("2. Project not activated in Sber Developers")
        print("3. Credentials format incorrect")
        
except Exception as e:
    print(f"❌ Error: {e}")
