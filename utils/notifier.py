import requests

class TelegramNotifier:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_message(self, message):
        if not self.token or not self.chat_id:
            print("Telegram not configured. Skipping notification.")
            return

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(self.base_url, json=payload)
            if response.status_code != 200:
                print(f"Failed to send Telegram message: {response.text}")
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
