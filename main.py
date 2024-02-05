import aiohttp
import asyncio
import json
from datetime import datetime, timedelta
import sys

class PrivatBankAPI:
    API_URL = 'https://api.privatbank.ua/p24api/exchange_rates?json&date='

    async def get_exchange_rate(self, date):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.API_URL + date) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['exchangeRate']
                else:
                    response.raise_for_status()

class CurrencyExchange:
    def __init__(self, api):
        self.api = api

    async def get_exchange_rates(self, days):
        today = datetime.now()
        rates = []

        for day in range(days):
            current_date = today - timedelta(days=day)
            formatted_date = current_date.strftime('%d.%m.%Y')

            try:
                exchange_rate = await self.api.get_exchange_rate(formatted_date)
                rates.append({formatted_date: exchange_rate})
            except Exception as e:
                print(f"Error retrieving data for {formatted_date}: {e}")

        return rates

def filter_currency_rates(exchange_rates, selected_currencies):
    filtered_rates = []

    for rate in exchange_rates:
        filtered_rate = {}

        for date, currencies_list in rate.items():
            filtered_currencies = {}

            for currency in currencies_list:
                if currency['currency'].upper() in selected_currencies:
                    filtered_currencies[currency['currency']] = {
                        'sale': currency.get('saleRate', currency['saleRateNB']),
                        'purchase': currency.get('purchaseRate', currency['purchaseRateNB'])
                    }

            if filtered_currencies:
                filtered_rate[date] = filtered_currencies

        if filtered_rate:
            filtered_rates.append(filtered_rate)

    return filtered_rates

async def main():
    if len(sys.argv) < 2:
        print("Usage: python main2.py <number_of_days> [<currency1> <currency2> ...]")
        sys.exit(1)

    try:
        days = int(sys.argv[1])
        selected_currencies = [currency.upper() for currency in sys.argv[2:]] or ['EUR', 'USD']
    except ValueError:
        print("Invalid input. Please provide a valid number of days and currencies.")
        sys.exit(1)

    if days > 10:
        print("Number of days should not exceed 10.")
        sys.exit(1)

    api = PrivatBankAPI()
    exchange = CurrencyExchange(api)

    exchange_rates = await exchange.get_exchange_rates(days)
    filtered_rates = filter_currency_rates(exchange_rates, selected_currencies)
    
    print(json.dumps(filtered_rates, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())

