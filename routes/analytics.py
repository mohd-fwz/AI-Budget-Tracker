"""
Analytics routes
Provides aggregated spending data for charts and graphs
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from models import db, Expense
from utils.auth_helpers import require_auth

# Create Blueprint for analytics routes
analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/analytics', methods=['GET'])
@require_auth
def get_analytics():
    """Get analytics data for authenticated user

    Query parameters:
        - start_date: Start date for analysis (ISO format) - defaults to 30 days ago
        - end_date: End date for analysis (ISO format) - defaults to today
        - period: Aggregation period ('daily', 'weekly', 'monthly') - defaults to 'monthly'

    Returns:
        200: Analytics data including:
            - spending_by_category: Total spending per category
            - monthly_trends: Spending over time
            - total_spending: Total amount spent in period
            - average_transaction: Average transaction amount
            - transaction_count: Number of transactions
            - top_expenses: Largest individual expenses
    """
    try:
        user_id = g.user_id
        # Get date range from query params or use defaults
        end_date = request.args.get('end_date')
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end = datetime.utcnow()

        start_date = request.args.get('start_date')
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            # Default to showing all transactions (1 year back to cover most cases)
            start = end - timedelta(days=365)

        # Base query for the date range
        base_query = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.date >= start,
            Expense.date <= end
        )

        # 1. Spending by Category (EXCLUDE Income category)
        category_spending = db.session.query(
            Expense.category,
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count')
        ).filter(
            Expense.user_id == user_id,
            Expense.date >= start,
            Expense.date <= end,
            Expense.category != 'Income'  # Exclude Income from spending
        ).group_by(Expense.category).all()

        spending_by_category = [
            {
                'category': cat,
                'total': float(total),
                'count': count,
                'percentage': 0  # Will calculate after getting total
            }
            for cat, total, count in category_spending
        ]

        # 2. Total Spending (EXCLUDE Income)
        total_result = db.session.query(
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count'),
            func.avg(Expense.amount).label('average')
        ).filter(
            Expense.user_id == user_id,
            Expense.date >= start,
            Expense.date <= end,
            Expense.category != 'Income'  # Exclude Income from spending
        ).first()

        total_spending = float(total_result.total) if total_result.total else 0
        transaction_count = total_result.count if total_result.count else 0
        average_transaction = float(total_result.average) if total_result.average else 0

        # 3. Calculate Income separately
        income_result = db.session.query(
            func.sum(Expense.amount).label('total'),
            func.count(Expense.id).label('count')
        ).filter(
            Expense.user_id == user_id,
            Expense.date >= start,
            Expense.date <= end,
            Expense.category == 'Income'
        ).first()

        total_income = float(income_result.total) if income_result.total else 0
        income_count = income_result.count if income_result.count else 0

        # Calculate percentages for categories
        for item in spending_by_category:
            if total_spending > 0:
                item['percentage'] = round((item['total'] / total_spending) * 100, 2)

        # 3. Time-based Trends
        period = request.args.get('period', 'monthly')
        trends = _get_spending_trends(user_id, start, end, period)

        # 4. Top Expenses (largest transactions, EXCLUDE Income)
        top_expenses_query = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.date >= start,
            Expense.date <= end,
            Expense.category != 'Income'
        ).order_by(Expense.amount.desc()).limit(10)

        top_expenses = [
            {
                'id': expense.id,
                'amount': float(expense.amount),
                'category': expense.category,
                'description': expense.description,
                'date': expense.date.isoformat()
            }
            for expense in top_expenses_query.all()
        ]

        # 5. Daily Average
        days_in_period = (end - start).days + 1
        daily_average = total_spending / days_in_period if days_in_period > 0 else 0

        # Return comprehensive analytics
        return jsonify({
            'period': {
                'start': start.isoformat(),
                'end': end.isoformat(),
                'days': days_in_period
            },
            'summary': {
                'total_spending': round(total_spending, 2),
                'total_income': round(total_income, 2),
                'net_balance': round(total_income - total_spending, 2),
                'transaction_count': transaction_count,
                'income_count': income_count,
                'average_transaction': round(average_transaction, 2),
                'daily_average': round(daily_average, 2)
            },
            'spending_by_category': spending_by_category,
            'trends': trends,
            'top_expenses': top_expenses
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Failed to generate analytics',
            'message': str(e)
        }), 500


def _get_spending_trends(user_id, start_date, end_date, period='monthly'):
    """
    Get spending trends over time

    Args:
        user_id: User ID
        start_date: Start date
        end_date: End date
        period: 'daily', 'weekly', or 'monthly'

    Returns:
        list: List of time periods with spending totals
    """
    try:
        if period == 'daily':
            # Group by date (EXCLUDE Income)
            results = db.session.query(
                func.date(Expense.date).label('period'),
                func.sum(Expense.amount).label('total')
            ).filter(
                Expense.user_id == user_id,
                Expense.date >= start_date,
                Expense.date <= end_date,
                Expense.category != 'Income'
            ).group_by(func.date(Expense.date)).order_by('period').all()

            return [
                {
                    'period': str(period),
                    'total': float(total)
                }
                for period, total in results
            ]

        elif period == 'weekly':
            # Group by week (EXCLUDE Income)
            results = db.session.query(
                extract('year', Expense.date).label('year'),
                extract('week', Expense.date).label('week'),
                func.sum(Expense.amount).label('total')
            ).filter(
                Expense.user_id == user_id,
                Expense.date >= start_date,
                Expense.date <= end_date,
                Expense.category != 'Income'
            ).group_by('year', 'week').order_by('year', 'week').all()

            return [
                {
                    'period': f"{int(year)}-W{int(week):02d}",
                    'total': float(total)
                }
                for year, week, total in results
            ]

        else:  # monthly (default)
            # Group by month (EXCLUDE Income)
            results = db.session.query(
                extract('year', Expense.date).label('year'),
                extract('month', Expense.date).label('month'),
                func.sum(Expense.amount).label('total')
            ).filter(
                Expense.user_id == user_id,
                Expense.date >= start_date,
                Expense.date <= end_date,
                Expense.category != 'Income'
            ).group_by('year', 'month').order_by('year', 'month').all()

            return [
                {
                    'period': f"{int(year)}-{int(month):02d}",
                    'total': float(total)
                }
                for year, month, total in results
            ]

    except Exception as e:
        print(f"Error generating trends: {str(e)}")
        return []


@analytics_bp.route('/api/insights/transactions', methods=['GET'])
@require_auth
def get_transaction_insights():
    """Get transaction insights like most frequent merchants, transactions per day, etc.

    Query parameters:
        - days_back: Number of days to analyze (default: 30)

    Returns:
        200: Transaction insights
    """
    try:
        user_id = g.user_id

        days_back = int(request.args.get('days_back', 30))
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # Most frequent merchants (by transaction count)
        merchant_counts = db.session.query(
            Expense.description,
            func.count(Expense.id).label('count'),
            func.sum(Expense.amount).label('total_spent'),
            Expense.category
        ).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date,
            Expense.description.isnot(None),
            Expense.category != 'Income'
        ).group_by(Expense.description, Expense.category).order_by(func.count(Expense.id).desc()).limit(10).all()

        # Transactions per day
        daily_transactions = db.session.query(
            func.date(Expense.date).label('date'),
            func.count(Expense.id).label('count'),
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date,
            Expense.category != 'Income'
        ).group_by(func.date(Expense.date)).all()

        total_transactions = sum(row.count for row in daily_transactions)
        total_days = len(daily_transactions)
        avg_transactions_per_day = total_transactions / max(total_days, 1)
        avg_amount_per_day = sum(float(row.total) for row in daily_transactions) / max(total_days, 1)

        # Most expensive single transaction
        top_transaction = db.session.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date,
            Expense.category != 'Income'
        ).order_by(Expense.amount.desc()).first()

        # Category with most transactions
        category_transaction_counts = db.session.query(
            Expense.category,
            func.count(Expense.id).label('count')
        ).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date <= end_date,
            Expense.category != 'Income'
        ).group_by(Expense.category).order_by(func.count(Expense.id).desc()).all()

        return jsonify({
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days_back
            },
            'most_frequent_merchants': [
                {
                    'merchant': row.description[:50] if row.description else 'Unknown',
                    'transaction_count': row.count,
                    'total_spent': float(row.total_spent),
                    'category': row.category
                }
                for row in merchant_counts
            ],
            'transaction_summary': {
                'total_transactions': total_transactions,
                'avg_transactions_per_day': round(avg_transactions_per_day, 1),
                'avg_amount_per_day': round(avg_amount_per_day, 2),
                'days_with_transactions': total_days
            },
            'top_transaction': {
                'amount': float(top_transaction.amount),
                'category': top_transaction.category,
                'description': top_transaction.description,
                'date': top_transaction.date.isoformat()
            } if top_transaction else None,
            'category_activity': [
                {
                    'category': row.category,
                    'transaction_count': row.count
                }
                for row in category_transaction_counts
            ]
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Failed to generate transaction insights',
            'message': str(e)
        }), 500
