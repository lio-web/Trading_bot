import MetaTrader5 as mt5

print("Searching for FILLING constants in mt5 module...")
for prop in dir(mt5):
    if "FILLING" in prop:
        print(f"{prop}: {getattr(mt5, prop)}")
