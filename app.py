import json
import os
from datetime import datetime, timedelta
from typing import Dict

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)


class ExchangeRateService:
    def __init__(self):
        self.base_url = "https://api.exchangerate.host"
        self.fallback_file = "data/sample_api.json"
        self.api_key = os.getenv("EXCHANGE_RATE_API_KEY")

    def get_rates(self, start_date: str, end_date: str, from_currency: str = "USD", to_currency: str = "EUR") -> Dict:
        """
        Get exchange rates for a date range. Try API first, fallback to local file.
        """
        try:
            # Try timeframe endpoint for date ranges (if available)
            if start_date != end_date:
                return self._get_timeframe_rates(start_date, end_date, from_currency, to_currency)
            else:
                # Single date - use historical endpoint
                return self._get_historical_rate(start_date, from_currency, to_currency)

        except Exception as e:
            print(f"API request failed: {e}")
            return self._load_fallback_data(start_date, end_date)

    def _get_timeframe_rates(self, start_date: str, end_date: str, from_currency: str, to_currency: str) -> Dict:
        """Get rates for a time frame using timeframe endpoint (fallback to day-by-day)"""
        try:
            # Try timeframe endpoint first (requires paid plan)
            url = f"{self.base_url}/timeframe"
            params = {
                'access_key': self.api_key,
                'start_date': start_date,
                'end_date': end_date,
                'source': from_currency,
                'currencies': to_currency
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('success', False) and 'quotes' in data:
                    # Convert timeframe format to our expected format
                    rates = {}
                    for date_str, quote_data in data['quotes'].items():
                        currency_pair = f"{from_currency}{to_currency}"
                        if currency_pair in quote_data:
                            rates[date_str] = {to_currency: quote_data[currency_pair]}

                    return {
                        'success': True,
                        'historical': True,
                        'base': from_currency,
                        'rates': rates
                    }

            # Fallback to day-by-day requests
            return self._get_rates_day_by_day(start_date, end_date, from_currency, to_currency)

        except Exception as e:
            print(f"Timeframe API request failed: {e}")
            return self._get_rates_day_by_day(start_date, end_date, from_currency, to_currency)

    def _get_historical_rate(self, date: str, from_currency: str, to_currency: str) -> Dict:
        """Get historical rate for a single date"""
        try:
            url = f"{self.base_url}/historical"
            params = {
                'access_key': self.api_key,
                'date': date,
                'source': from_currency,
                'currencies': to_currency
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get('success', False) and 'quotes' in data:
                    # Convert single date format to our expected format
                    currency_pair = f"{from_currency}{to_currency}"
                    if currency_pair in data['quotes']:
                        rates = {date: {to_currency: data['quotes'][currency_pair]}}
                        return {
                            'success': True,
                            'historical': True,
                            'base': from_currency,
                            'rates': rates
                        }

            raise Exception("No historical data available")

        except Exception as e:
            print(f"Historical API request failed: {e}")
            return self._load_fallback_data(date, date)

    def _get_rates_day_by_day(self, start_date: str, end_date: str, from_currency: str, to_currency: str) -> Dict:
        """Get rates day by day using historical endpoint"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            rates = {}
            current = start

            while current <= end:
                date_str = current.strftime('%Y-%m-%d')

                # Use historical endpoint for each date
                url = f"{self.base_url}/historical"
                params = {
                    'access_key': self.api_key,
                    'date': date_str,
                    'source': from_currency,
                    'currencies': to_currency
                }

                response = requests.get(url, params=params, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    if data.get('success', False) and 'quotes' in data:
                        currency_pair = f"{from_currency}{to_currency}"
                        if currency_pair in data['quotes']:
                            rates[date_str] = {to_currency: data['quotes'][currency_pair]}

                current += timedelta(days=1)

            if rates:
                return {
                    'success': True,
                    'historical': True,
                    'base': from_currency,
                    'rates': rates
                }
            else:
                raise Exception("No rates retrieved")

        except Exception as e:
            print(f"Day-by-day API request failed: {e}")
            return self._load_fallback_data(start_date, end_date)

    def _load_fallback_data(self, start_date: str, end_date: str) -> Dict:
        """Load fallback data from local file"""
        try:
            with open(self.fallback_file, 'r') as f:
                data = json.load(f)

            # Filter data to requested date range
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            filtered_rates = {}
            for date_str, rate_data in data['rates'].items():
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if start <= date_obj <= end:
                    filtered_rates[date_str] = rate_data

            return {
                'success': True,
                'historical': True,
                'base': data.get('base', 'USD'),
                'rates': filtered_rates
            }
        except Exception as e:
            print(f"Fallback data loading failed: {e}")
            return {'success': False, 'error': str(e)}


class FinanceCalculator:
    @staticmethod
    def calculate_percentage_change(old_value: float, new_value: float) -> float:
        """Calculate percentage change with division by zero handling"""
        if old_value == 0:
            return 0.0 if new_value == 0 else float('inf')
        return ((new_value - old_value) / old_value) * 100

    @staticmethod
    def process_rates_data(rates_data: Dict, to_currency: str = 'EUR', breakdown: str = 'day') -> Dict:
        """Process rates data and calculate statistics"""
        if not rates_data.get('success', False):
            return {'error': 'Failed to retrieve rates data'}

        rates = rates_data.get('rates', {})
        if not rates:
            return {'error': 'No rates data available'}

        # Sort dates
        sorted_dates = sorted(rates.keys())

        # Extract rate values for the target currency
        daily_data = []
        rate_values = []

        for i, date in enumerate(sorted_dates):
            # Get the rate for the target currency
            rate = rates[date].get(to_currency, 0)
            rate_values.append(rate)

            # Calculate percentage change from previous day
            pct_change = 0.0
            if i > 0:
                prev_rate = rate_values[i - 1]
                pct_change = FinanceCalculator.calculate_percentage_change(prev_rate, rate)

            daily_data.append({
                'date': date,
                'rate': round(rate, 5),
                'pct_change': round(pct_change, 2) if pct_change != float('inf') else 'N/A'
            })

        # Calculate totals
        start_rate = rate_values[0] if rate_values else 0
        end_rate = rate_values[-1] if rate_values else 0
        total_pct_change = FinanceCalculator.calculate_percentage_change(start_rate, end_rate)
        mean_rate = sum(rate_values) / len(rate_values) if rate_values else 0

        result = {
            'totals': {
                'start_rate': round(start_rate, 5),
                'end_rate': round(end_rate, 5),
                'total_pct_change': round(total_pct_change, 2) if total_pct_change != float('inf') else 'N/A',
                'mean_rate': round(mean_rate, 5)
            }
        }

        if breakdown == 'day':
            result['breakdown'] = daily_data

        return result


# Initialize services
exchange_service = ExchangeRateService()
calculator = FinanceCalculator()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Exchange Rate API',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/finance', methods=['GET'])
def finance():
    """
    Finance endpoint for exchange rate data
    Query parameters:
    - start: Start date (YYYY-MM-DD)
    - end: End date (YYYY-MM-DD)
    - breakdown: 'day' or 'none' (default: 'day')
    - from_currency: Source currency (default: 'USD')
    - to_currency: Target currency (default: 'EUR')
    """
    try:
        # Get query parameters
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        breakdown = request.args.get('breakdown', 'day')
        from_currency = request.args.get('from', 'USD')
        to_currency = request.args.get('to', 'EUR')

        # Validate required parameters
        if not start_date or not end_date:
            return jsonify({
                'error': 'Both start and end dates are required',
                'example': '/finance?start=2025-07-01&end=2025-07-03'
            }), 400

        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'error': 'Invalid date format. Use YYYY-MM-DD',
                'example': '/finance?start=2025-07-01&end=2025-07-03'
            }), 400

        # Get exchange rates
        rates_data = exchange_service.get_rates(start_date, end_date, from_currency, to_currency)

        # Process and calculate statistics
        result = calculator.process_rates_data(rates_data, to_currency, breakdown)

        if 'error' in result:
            return jsonify(result), 500

        # Add metadata
        result['metadata'] = {
            'start_date': start_date,
            'end_date': end_date,
            'from_currency': from_currency,
            'to_currency': to_currency,
            'breakdown': breakdown,
            'timestamp': datetime.now().isoformat()
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)