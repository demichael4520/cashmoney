import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import convert_currency, batch_convert, get_exchange_rates, get_historical_rate

print("Testing convert_currency: 100 USD to EUR...")
print(convert_currency(100.0, "USD", "EUR"))

print("\nTesting batch_convert: 1000 USD to [EUR, GBP, INR]...")
print(batch_convert(1000.0, "USD", ["EUR", "GBP", "INR"]))

print("\nTesting get_exchange_rates: base BTC...")
print(get_exchange_rates("BTC", ["USD", "EUR", "GBP"]))

print("\nTesting get_historical_rate: base USD to INR on 2025-01-15...")
print(get_historical_rate("USD", "INR", "2025-01-15"))
