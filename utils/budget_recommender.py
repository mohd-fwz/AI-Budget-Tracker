"""
AI-Powered Budget Recommendation System
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict
from sqlalchemy import func, extract


def analyze_spending_patterns(db_session, user_id: str, category: str, months_back: int = 6) -> Dict:
    from models import Expense
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months_back)
    
    monthly_data = db_session.query(
        extract('year', Expense.date).label('year'),
        extract('month', Expense.date).label('month'),
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        Expense.category == category,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).group_by('year', 'month').order_by('year', 'month').all()
    
    if not monthly_data:
        return {'avg_monthly': 0, 'trend': 'no_data', 'data_points': 0}
    
    amounts = [float(row.total) for row in monthly_data]
    avg = sum(amounts) / len(amounts)
    
    mid = len(amounts) // 2
    if len(amounts) >= 4:
        first = sum(amounts[:mid]) / mid if mid > 0 else 0
        second = sum(amounts[mid:]) / (len(amounts) - mid)
        trend = 'increasing' if second > first * 1.15 else 'decreasing' if second < first * 0.85 else 'stable'
    else:
        trend = 'stable'
    
    return {'avg_monthly': round(avg, 2), 'trend': trend, 'data_points': len(amounts)}


def generate_simple_recommendations(db_session, user_id: str, target_month: str, months_back: int = 6) -> Dict:
    from models import EXPENSE_CATEGORIES

    recs = []
    total = 0

    for cat in EXPENSE_CATEGORIES:
        if cat == 'Income':
            continue

        analysis = analyze_spending_patterns(db_session, user_id, cat, months_back)

        if analysis['data_points'] > 0:
            mult = 1.10 if analysis['trend'] == 'increasing' else 0.95 if analysis['trend'] == 'decreasing' else 1.0
            suggested = analysis['avg_monthly'] * mult

            recs.append({
                'category': cat,
                'suggested_amount': round(suggested, 2),
                'historical_average': analysis['avg_monthly'],
                'reasoning': f"Rs.{analysis['avg_monthly']:.0f} average, {analysis['trend']} trend",
                'trend': analysis['trend']
            })
            total += suggested

    return {
        'success': True,
        'target_month': target_month,
        'recommendations': recs,
        'total_suggested_budget': round(total, 2),
        'analysis_period': months_back,
        'generated_at': datetime.now().isoformat()
    }
