import requests
import config

print(f"Token from config (raw): '{config.TELEGRAM_TOKEN}'")
print(f"Token repr: {repr(config.TELEGRAM_TOKEN)}")

clean_token = config.TELEGRAM_TOKEN.strip()
print(f"Cleaned Token: '{clean_token}'")

# 1. Test getMe (verifies token validity)
print("\n--- Testing 'getMe' ---")
url_me = f"https://api.telegram.org/bot{clean_token}/getMe"
try:
    resp = requests.get(url_me)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Connection Error: {e}")

# 2. Test sendMessage (verifies Chat ID + permissions)
print("\n--- Testing 'sendMessage' ---")
url_msg = f"https://api.telegram.org/bot{clean_token}/sendMessage"
data = {
    "chat_id": config.TELEGRAM_CHAT_ID,
    "text": "Antigravity Debug Test"
}
try:
    resp = requests.post(url_msg, json=data)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    
    if resp.status_code == 400 or resp.status_code == 404:
        print("\n!!! ERROR: Chat Not Found !!!")
        print("1. Make sure you have searched for your bot in Telegram and clicked 'START'.")
        print("2. Send a dummy message (e.g., 'hello') to your bot.")
        print("3. Then run this script again, or check the URL below to find your real Chat ID:")
        print(f"   https://api.telegram.org/bot{clean_token}/getUpdates")
except Exception as e:
    print(f"Connection Error: {e}")
