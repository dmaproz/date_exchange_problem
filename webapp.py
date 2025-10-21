from datetime import datetime

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Import our existing services
from app import ExchangeRateService, FinanceCalculator

# Initialize services
exchange_service = ExchangeRateService()
calculator = FinanceCalculator()


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/rates')
def api_rates():
    """API endpoint for the web app to fetch rate data"""
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        from_currency = request.args.get('from', 'USD')
        to_currency = request.args.get('to', 'EUR')

        if not start_date or not end_date:
            return jsonify({'error': 'Start and end dates are required'}), 400

        # Validate date format
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Get exchange rates
        rates_data = exchange_service.get_rates(start_date, end_date, from_currency, to_currency)

        # Process data for visualization
        result = calculator.process_rates_data(rates_data, to_currency, 'day')

        if 'error' in result:
            return jsonify(result), 500

        # Format data for Chart.js
        breakdown = result.get('breakdown', [])
        chart_data = {
            'labels': [day['date'] for day in breakdown],
            'rates': [day['rate'] for day in breakdown],
            'changes': [day['pct_change'] if day['pct_change'] != 'N/A' else 0 for day in breakdown],
            'totals': result['totals'],
            'metadata': {
                'start_date': start_date,
                'end_date': end_date,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'timestamp': datetime.now().isoformat()
            }
        }

        return jsonify(chart_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Exchange Rate Visualization App',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)