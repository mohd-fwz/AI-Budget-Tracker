"""
Income Analysis Utility
Tracks actual income from uploaded bank statements for realistic budgeting
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import func, extract


def get_income_for_month(db_session, user_id: str, year: int, month: int) -> Dict:
    """
    Get total income received in a specific month from actual transactions

    Args:
        db_session: Database session
        user_id: User ID
        year: Year (e.g., 2026)
        month: Month (1-12)

    Returns:
        Dict with income data:
        {
            'total_income': float,
            'transaction_count': int,
            'sources': List[str],  # List of income descriptions
            'has_data': bool
        }
    """
    from models import Expense

    # Query income transactions for the month
    results = db_session.query(
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).filter(
        Expense.user_id == user_id,
        Expense.category == 'Income',
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month
    ).first()

    total_income = float(results.total or 0)
    count = int(results.count or 0)

    # Get income sources (descriptions)
    if count > 0:
        sources = db_session.query(Expense.description).filter(
            Expense.user_id == user_id,
            Expense.category == 'Income',
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month
        ).distinct().limit(5).all()

        source_list = [s[0] for s in sources if s[0]]
    else:
        source_list = []

    return {
        'total_income': round(total_income, 2),
        'transaction_count': count,
        'sources': source_list,
        'has_data': count > 0
    }


def get_average_income_last_n_months(db_session, user_id: str, months: int = 3) -> Dict:
    """
    Calculate average monthly income over last N months from actual transactions

    Args:
        db_session: Database session
        user_id: User ID
        months: Number of months to average (default 3)

    Returns:
        Dict with:
        {
            'average_income': float,
            'months_analyzed': int,
            'total_income': float,
            'income_by_month': List[Dict],
            'is_stable': bool,  # True if income varies < 20%
            'trend': str  # 'increasing', 'decreasing', 'stable'
        }
    """
    from models import Expense

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months)

    # Get income grouped by month
    results = db_session.query(
        extract('year', Expense.date).label('year'),
        extract('month', Expense.date).label('month'),
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        Expense.category == 'Income',
        Expense.date >= start_date,
        Expense.date <= end_date
    ).group_by('year', 'month').order_by('year', 'month').all()

    if not results:
        return {
            'average_income': 0,
            'months_analyzed': 0,
            'total_income': 0,
            'income_by_month': [],
            'is_stable': False,
            'trend': 'no_data'
        }

    # Parse results
    income_by_month = []
    total = 0

    for row in results:
        amount = float(row.total or 0)
        income_by_month.append({
            'year': int(row.year),
            'month': int(row.month),
            'amount': round(amount, 2)
        })
        total += amount

    months_analyzed = len(results)
    average = total / months_analyzed if months_analyzed > 0 else 0

    # Calculate stability (coefficient of variation)
    if months_analyzed >= 2:
        amounts = [m['amount'] for m in income_by_month]
        variance = sum((x - average) ** 2 for x in amounts) / months_analyzed
        std_dev = variance ** 0.5
        cv = (std_dev / average * 100) if average > 0 else 0
        is_stable = cv < 20  # Stable if variation < 20%
    else:
        is_stable = False

    # Calculate trend
    if months_analyzed >= 3:
        mid = months_analyzed // 2
        first_half_avg = sum(m['amount'] for m in income_by_month[:mid]) / mid
        second_half_avg = sum(m['amount'] for m in income_by_month[mid:]) / (months_analyzed - mid)

        if second_half_avg > first_half_avg * 1.15:
            trend = 'increasing'
        elif second_half_avg < first_half_avg * 0.85:
            trend = 'decreasing'
        else:
            trend = 'stable'
    else:
        trend = 'stable'

    return {
        'average_income': round(average, 2),
        'months_analyzed': months_analyzed,
        'total_income': round(total, 2),
        'income_by_month': income_by_month,
        'is_stable': is_stable,
        'trend': trend
    }


def predict_next_month_income(db_session, user_id: str, target_year: int, target_month: int) -> Dict:
    """
    Predict income for upcoming month using intelligent analysis

    Strategy:
    1. If income already entered for target month, use that
    2. Else, use 3-month rolling average
    3. If no data, fall back to profile monthly_income
    4. Apply trend adjustment if income is increasing/decreasing

    Args:
        db_session: Database session
        user_id: User ID
        target_year: Target year
        target_month: Target month (1-12)

    Returns:
        Dict with:
        {
            'predicted_income': float,
            'confidence': str,  # 'high', 'medium', 'low'
            'method': str,  # How prediction was made
            'reasoning': str  # Human-readable explanation
        }
    """
    from models import UserProfile

    # Check if income already entered for target month
    current_month_income = get_income_for_month(db_session, user_id, target_year, target_month)

    if current_month_income['has_data']:
        return {
            'predicted_income': current_month_income['total_income'],
            'confidence': 'high',
            'method': 'actual_income',
            'reasoning': f"Based on ₹{current_month_income['total_income']:,.0f} already received this month from {current_month_income['transaction_count']} transaction(s)",
            'data': current_month_income
        }

    # Get 3-month average
    historical = get_average_income_last_n_months(db_session, user_id, months=3)

    if historical['months_analyzed'] >= 2:
        # Have enough historical data
        base_prediction = historical['average_income']

        # Apply trend adjustment
        if historical['trend'] == 'increasing':
            predicted = base_prediction * 1.10  # Expect 10% increase
            reasoning = f"Based on ₹{base_prediction:,.0f} average over last {historical['months_analyzed']} months. Income is increasing, so budgeting ₹{predicted:,.0f} (+10%)"
        elif historical['trend'] == 'decreasing':
            predicted = base_prediction * 0.90  # Conservative estimate
            reasoning = f"Based on ₹{base_prediction:,.0f} average over last {historical['months_analyzed']} months. Income is decreasing, so budgeting conservatively at ₹{predicted:,.0f} (-10%)"
        else:
            predicted = base_prediction
            reasoning = f"Based on ₹{base_prediction:,.0f} average from last {historical['months_analyzed']} months. Income is stable"

        confidence = 'high' if historical['is_stable'] else 'medium'

        return {
            'predicted_income': round(predicted, 2),
            'confidence': confidence,
            'method': 'historical_average',
            'reasoning': reasoning,
            'data': historical
        }

    elif historical['months_analyzed'] == 1:
        # Only 1 month of data
        predicted = historical['average_income']
        return {
            'predicted_income': round(predicted, 2),
            'confidence': 'low',
            'method': 'single_month',
            'reasoning': f"Based on ₹{predicted:,.0f} from last month. Upload more statements for better predictions",
            'data': historical
        }

    else:
        # No transaction data, fall back to profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()

        if profile and profile.monthly_income:
            predicted = float(profile.monthly_income)
            return {
                'predicted_income': round(predicted, 2),
                'confidence': 'low',
                'method': 'profile_estimate',
                'reasoning': f"Based on your profile estimate of ₹{predicted:,.0f}/month. Upload bank statements for accurate tracking",
                'data': None
            }
        else:
            return {
                'predicted_income': 0,
                'confidence': 'none',
                'method': 'no_data',
                'reasoning': "No income data available. Please upload bank statements or set expected income in profile",
                'data': None
            }


def get_income_summary(db_session, user_id: str) -> Dict:
    """
    Get comprehensive income summary for dashboard display

    Returns:
        Dict with current month, last 3 months, and predictions
    """
    now = datetime.now()

    # Current month
    current = get_income_for_month(db_session, user_id, now.year, now.month)

    # Last 3 months average
    historical = get_average_income_last_n_months(db_session, user_id, months=3)

    # Next month prediction
    next_month = now.month + 1
    next_year = now.year
    if next_month > 12:
        next_month = 1
        next_year += 1

    prediction = predict_next_month_income(db_session, user_id, next_year, next_month)

    return {
        'current_month': current,
        'historical_average': historical,
        'next_month_prediction': prediction,
        'generated_at': now.isoformat()
    }
