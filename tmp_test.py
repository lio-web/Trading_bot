import MetaTrader5 as mt5
import time
import os
from dotenv import load_dotenv

load_dotenv()

print("Initializing...")
res = mt5.initialize(timeout=60000)
print(f"initialize returned {res}")

if res:
    print("Waiting up to 15 seconds for terminal to connect itself...")
    found = False
    for i in range(15):
        acc = mt5.account_info()
        if acc and str(acc.login) == str(os.getenv("MT5_LOGIN")):
            print(f"[{i}s] Got it! Logged in automatically as {acc.login} to {acc.server}")
            found = True
            break
        print(f"[{i}s] Polling... currently: {acc.login if acc else 'None'}")
        time.sleep(1)
        
    if not found:
        print("Never found it... attempting explicit login.")
        lres = mt5.login(int(os.getenv("MT5_LOGIN")), os.getenv("MT5_PASSWORD"), os.getenv("MT5_SERVER"))
        print(f"Login returned {lres}, last_error={mt5.last_error()}")
    
mt5.shutdown()
