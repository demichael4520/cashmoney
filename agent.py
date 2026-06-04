import urllib.request
import json
import datetime
from typing import List, Dict, Optional
from google.adk.agents import LlmAgent

# 1. Helper validation/mapping
CRYPTO_MAP = {
    "BTC": "bitcoin", "ETH": "ethereum", "USDT": "tether", "SOL": "solana",
    "USDC": "usd-coin", "XRP": "ripple", "ADA": "cardano", "AVAX": "avalanche-2",
    "DOGE": "dogecoin", "DOT": "polkadot", "MATIC": "polygon", "LINK": "chainlink",
    "TRX": "tron", "LTC": "litecoin", "BCH": "bitcoin-cash", "UNI": "uniswap",
    "SHIB": "shiba-inu", "XLM": "stellar", "XMR": "monero", "ETC": "ethereum-classic",
    "ICP": "internet-computer", "FIL": "filecoin", "LDO": "lido-finance",
    "HBAR": "hedera-hashgraph", "APT": "aptos", "NEAR": "near", "VET": "vechain",
    "QNT": "quant", "GRT": "the-graph", "AAVE": "aave", "ALGO": "algorand"
}

def is_crypto(currency: str) -> bool:
    return currency.upper() in CRYPTO_MAP

# 2. Core API clients
def fetch_json(url: str) -> dict:
    print(f"[CashMoney Tool] Fetching URL: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))

def get_fiat_rates(base: str) -> dict:
    # ExchangeRate-API (Zero-auth)
    url = f"https://open.er-api.com/v6/latest/{base.upper()}"
    data = fetch_json(url)
    if data.get("result") == "success":
        return {
            "base": data["base_code"],
            "rates": data["rates"],
            "source": "exchangerate-api"
        }
    raise Exception("Failed to fetch fiat rates")

def get_crypto_rates(base: str) -> dict:
    # Coinbase (Zero-auth)
    url = f"https://api.coinbase.com/v2/exchange-rates?currency={base.upper()}"
    data = fetch_json(url)
    raw_rates = data.get("data", {}).get("rates", {})
    rates = {}
    for k, v in raw_rates.items():
        try:
            rates[k] = float(v)
        except ValueError:
            pass
    return {
        "base": data["data"]["currency"],
        "rates": rates,
        "source": "coinbase"
    }

def get_current_rate(from_curr: str, to_curr: str) -> dict:
    from_curr = from_curr.upper()
    to_curr = to_curr.upper()
    
    if not is_crypto(from_curr) and not is_crypto(to_curr):
        res = get_fiat_rates(from_curr)
        return {"rate": res["rates"][to_curr], "source": res["source"]}
        
    if is_crypto(from_curr) and not is_crypto(to_curr):
        res = get_crypto_rates(from_curr)
        return {"rate": res["rates"][to_curr], "source": res["source"]}
        
    if not is_crypto(from_curr) and is_crypto(to_curr):
        res = get_crypto_rates(to_curr)
        return {"rate": 1.0 / res["rates"][from_curr], "source": res["source"]}
        
    # Crypto -> Crypto via USD cross-rate
    rate_from_usd = get_crypto_rates(from_curr)["rates"]["USD"]
    rate_to_usd = get_crypto_rates(to_curr)["rates"]["USD"]
    return {
        "rate": rate_from_usd / rate_to_usd,
        "source": "coinbase+coinbase"
    }

# 3. Tool Functions
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount from one currency to another (supports fiat and crypto).

    Args:
        amount: Amount to convert (positive number).
        from_currency: 3-letter source currency code (e.g. USD, EUR, BTC).
        to_currency: 3-letter target currency code (e.g. USD, EUR, BTC).
    """
    try:
        from_curr = from_currency.upper()
        to_curr = to_currency.upper()
        res = get_current_rate(from_curr, to_curr)
        rate = res["rate"]
        converted = round(amount * rate, 6)
        result_dict = {
            "amount": amount,
            "from": from_curr,
            "to": to_curr,
            "result": converted,
            "rate": rate,
            "inverseRate": round(1.0 / rate, 6) if rate else 0,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "source": res["source"],
            "cached": False
        }
        return json.dumps(result_dict)
    except Exception as e:
        return json.dumps({"error": f"Failed to convert currency: {str(e)}"})

def batch_convert(amount: float, from_currency: str, to_currencies: List[str]) -> str:
    """Convert an amount from one currency to multiple target currencies in a single call.

    Args:
        amount: Amount to convert (positive number).
        from_currency: 3-letter source currency code (e.g. USD, BTC).
        to_currencies: List of target currency codes (e.g. ['EUR', 'GBP', 'INR']).
    """
    try:
        from_curr = from_currency.upper()
        conversions = []
        for to_curr in to_currencies:
            to_curr = to_curr.upper()
            if to_curr == from_curr:
                continue
            try:
                res = get_current_rate(from_curr, to_curr)
                conversions.append({
                    "to": to_curr,
                    "result": round(amount * res["rate"], 6),
                    "rate": res["rate"],
                    "inverseRate": round(1.0 / res["rate"], 6) if res["rate"] else 0,
                    "source": res["source"]
                })
            except Exception:
                pass
        result_dict = {
            "amount": amount,
            "from": from_curr,
            "conversions": conversions,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
        return json.dumps(result_dict)
    except Exception as e:
        return json.dumps({"error": f"Failed to batch convert: {str(e)}"})

def get_exchange_rates(base_currency: str, target_currencies: Optional[List[str]] = None) -> str:
    """Get current exchange rates for a base currency against a list of target currencies.

    Args:
        base_currency: 3-letter base currency code (e.g. USD, EUR, BTC).
        target_currencies: Optional list of target currency codes.
    """
    try:
        base = base_currency.upper()
        targets = [t.upper() for t in target_currencies] if target_currencies else [
            'USD', 'EUR', 'GBP', 'JPY', 'INR', 'AED', 'CAD', 'AUD', 'CHF', 'CNY',
            'SGD', 'HKD', 'KRW', 'BRL', 'MXN', 'ZAR', 'TRY', 'THB', 'SAR', 'BTC'
        ]
        if base in targets:
            targets.remove(base)
            
        rates = {}
        source = ""
        
        if not is_crypto(base):
            res = get_fiat_rates(base)
            source = res["source"]
            for t in targets:
                if not is_crypto(t) and t in res["rates"]:
                    rates[t] = res["rates"][t]
                elif is_crypto(t):
                    try:
                        c_res = get_crypto_rates(t)
                        rates[t] = round(1.0 / c_res["rates"][base], 8)
                        if c_res["source"] not in source:
                            source += f"+{c_res['source']}"
                    except Exception:
                        pass
        else:
            res = get_crypto_rates(base)
            source = res["source"]
            for t in targets:
                if t in res["rates"]:
                    rates[t] = res["rates"][t]
                    
        result_dict = {
            "base": base,
            "rates": rates,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "source": source,
            "cached": False
        }
        return json.dumps(result_dict)
    except Exception as e:
        return json.dumps({"error": f"Failed to retrieve rates: {str(e)}"})

def get_historical_rate(base_currency: str, target_currency: str, date_str: str) -> str:
    """Get historical exchange rate for a specific date using Frankfurter ECB API.

    Args:
        base_currency: 3-letter base currency code (e.g. USD, EUR).
        target_currency: 3-letter target currency code (e.g. USD, EUR).
        date_str: Date in YYYY-MM-DD format.
    """
    try:
        base = base_currency.upper()
        target = target_currency.upper()
        
        url = f"https://api.frankfurter.app/{date_str}?from={base}&to={target}"
        data = fetch_json(url)
        rate = data.get("rates", {}).get(target)
        if rate is None:
            raise Exception(f"No rate available for {base}->{target} on {date_str}")
            
        result_dict = {
            "base": base,
            "target": target,
            "date": date_str,
            "rate": rate,
            "source": "frankfurter",
            "cached": False
        }
        return json.dumps(result_dict)
    except Exception as e:
        return json.dumps({"error": f"Failed to retrieve historical rate: {str(e)}"})

import os
from google.adk.tools import McpToolset
from google.adk.tools.mcp_tool import StreamableHTTPConnectionParams

# Check if we should use a remote MCP server (e.g. deployed on Cloud Run)
mcp_url = os.environ.get("MCP_SERVER_URL")

if mcp_url:
    print(f"[CashMoney] Connecting to remote MCP server: {mcp_url}")
    if "/sse" in mcp_url:
        from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
        connection_params = SseConnectionParams(url=mcp_url)
    else:
        connection_params = StreamableHTTPConnectionParams(url=mcp_url)
    tools = [McpToolset(connection_params=connection_params)]
else:
    print("[CashMoney] Using local Python functions as tools")
    tools = [convert_currency, batch_convert, get_exchange_rates, get_historical_rate]

# Define specialized cash-money LLM Agent
cash_money_agent = LlmAgent(
    name='cash_money',
    model='gemini-2.5-flash',
    instruction='You are a premier cash-money currency assistant. Help the user with conversions, forex exchange rates, batch conversions, and historical data lookup using your high-performance tools.',
    description='Vertex AI Reasoning Engine deployment for real-time currency and crypto rates conversion.',
    tools=tools,
)

from google.adk.apps.app import App

app = App(
    name="cash_money_app",
    root_agent=cash_money_agent
)

root_agent = cash_money_agent
