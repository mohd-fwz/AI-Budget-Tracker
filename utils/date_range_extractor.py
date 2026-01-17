"""
Date range extraction and filtering utilities
Analyzes transaction dates and provides filtering options
"""
from datetime import datetime, timedelta
from typing import List, Dict


def extract_date_range(transactions: List[Dict]) -> Dict:
    """
    Extract date range information from transactions

    Args:
        transactions: List of transaction dictionaries with 'date' key

    Returns:
        dict: {
            'min_date': datetime,
            'max_date': datetime,
            'total_days': int,
            'suggested_ranges': [
                {
                    'label': str,
                    'start_date': str (YYYY-MM-DD),
                    'end_date': str (YYYY-MM-DD),
                    'days': int
                },
                ...
            ]
        }

    The suggested_ranges include:
    - Last 1 Month
    - Last 3 Months
    - Last 6 Months
    - All Transactions
    """
    if not transactions:
        return {
            'min_date': None,
            'max_date': None,
            'total_days': 0,
            'suggested_ranges': []
        }

    # Find min and max dates
    dates = [t['date'] for t in transactions if t.get('date')]

    if not dates:
        return {
            'min_date': None,
            'max_date': None,
            'total_days': 0,
            'suggested_ranges': []
        }

    min_date = min(dates)
    max_date = max(dates)
    total_days = (max_date - min_date).days

    # Calculate suggested ranges based on the max date
    suggested_ranges = []

    # All transactions
    suggested_ranges.append({
        'label': 'All Transactions',
        'start_date': min_date.strftime('%Y-%m-%d'),
        'end_date': max_date.strftime('%Y-%m-%d'),
        'days': total_days
    })

    # Last 1 Month (from max_date)
    one_month_ago = max_date - timedelta(days=30)
    if one_month_ago >= min_date:
        # Count transactions in this range
        count = sum(1 for t in transactions if t['date'] >= one_month_ago)
        suggested_ranges.append({
            'label': f'Last 1 Month ({count} transactions)',
            'start_date': one_month_ago.strftime('%Y-%m-%d'),
            'end_date': max_date.strftime('%Y-%m-%d'),
            'days': 30
        })

    # Last 3 Months
    three_months_ago = max_date - timedelta(days=90)
    if three_months_ago >= min_date:
        count = sum(1 for t in transactions if t['date'] >= three_months_ago)
        suggested_ranges.append({
            'label': f'Last 3 Months ({count} transactions)',
            'start_date': three_months_ago.strftime('%Y-%m-%d'),
            'end_date': max_date.strftime('%Y-%m-%d'),
            'days': 90
        })

    # Last 6 Months
    six_months_ago = max_date - timedelta(days=180)
    if six_months_ago >= min_date:
        count = sum(1 for t in transactions if t['date'] >= six_months_ago)
        suggested_ranges.append({
            'label': f'Last 6 Months ({count} transactions)',
            'start_date': six_months_ago.strftime('%Y-%m-%d'),
            'end_date': max_date.strftime('%Y-%m-%d'),
            'days': 180
        })

    # Last 1 Year
    one_year_ago = max_date - timedelta(days=365)
    if one_year_ago >= min_date and total_days > 180:  # Only show if statement > 6 months
        count = sum(1 for t in transactions if t['date'] >= one_year_ago)
        suggested_ranges.append({
            'label': f'Last 1 Year ({count} transactions)',
            'start_date': one_year_ago.strftime('%Y-%m-%d'),
            'end_date': max_date.strftime('%Y-%m-%d'),
            'days': 365
        })

    return {
        'min_date': min_date.strftime('%Y-%m-%d'),
        'max_date': max_date.strftime('%Y-%m-%d'),
        'total_days': total_days,
        'suggested_ranges': suggested_ranges
    }


def filter_by_date_range(
    transactions: List[Dict],
    start_date: str,
    end_date: str
) -> List[Dict]:
    """
    Filter transactions by date range

    Args:
        transactions: List of transaction dictionaries
        start_date: Start date (YYYY-MM-DD format)
        end_date: End date (YYYY-MM-DD format)

    Returns:
        List[Dict]: Filtered transactions within the date range (inclusive)

    Example:
        filtered = filter_by_date_range(
            transactions,
            '2025-01-01',
            '2025-03-31'
        )
    """
    # Parse date strings
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError as e:
        raise ValueError(f"Invalid date format. Use YYYY-MM-DD: {str(e)}")

    # Ensure end >= start
    if end < start:
        raise ValueError("End date must be after or equal to start date")

    # Filter transactions
    filtered = [
        t for t in transactions
        if t.get('date') and start <= t['date'] <= end
    ]

    print(f"Filtered {len(filtered)} transactions from {start_date} to {end_date}")
    return filtered


def get_date_range_summary(transactions: List[Dict]) -> str:
    """
    Get a human-readable summary of transaction date range

    Args:
        transactions: List of transaction dictionaries

    Returns:
        str: Summary like "Jan 1, 2025 to Mar 31, 2025 (90 days, 45 transactions)"
    """
    if not transactions:
        return "No transactions"

    dates = [t['date'] for t in transactions if t.get('date')]

    if not dates:
        return "No valid dates"

    min_date = min(dates)
    max_date = max(dates)
    total_days = (max_date - min_date).days

    return (
        f"{min_date.strftime('%b %d, %Y')} to {max_date.strftime('%b %d, %Y')} "
        f"({total_days} days, {len(transactions)} transactions)"
    )
