"""
AI-powered savings recommendations
Analyzes spending patterns and provides personalized advice using Groq API
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from sqlalchemy import func
import requests
from models import db, Expense
from config import Config
from utils.auth_helpers import require_auth

# Create Blueprint for recommendations routes
recommendations_bp = Blueprint('recommendations', __name__)


@recommendations_bp.route('/api/recommendations', methods=['GET'])
@require_auth
def get_recommendations():
    """Get AI-powered savings recommendations for authenticated user

    Query parameters:
        - days: Number of days to analyze (default: 30)

    Returns:
        200: Recommendations and insights
        503: AI service unavailable

    The AI analyzes:
        - Spending patterns by category
        - High-spending categories
        - Unusual expenses
        - Month-over-month trends
    """
    user_id = g.user_id

    if not Config.GROQ_API_KEY:
        return jsonify({
            'error': 'AI service not configured',
            'message': 'GROQ_API_KEY is not set'
        }), 503

    try:
        # Get analysis period
        days = request.args.get('days', type=int, default=30)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Gather spending data for AI analysis
        spending_data = _gather_spending_data(user_id, start_date, end_date)

        if not spending_data['total_spending']:
            return jsonify({
                'message': 'No spending data available for analysis',
                'recommendations': [
                    'Start tracking your expenses to get personalized recommendations!',
                    'Upload your bank statements for automatic expense categorization.',
                    'Set a monthly budget to monitor your spending habits.'
                ]
            }), 200

        # Generate AI recommendations
        recommendations = _generate_ai_recommendations(spending_data, days)

        return jsonify({
            'period': {
                'days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'spending_summary': {
                'total': spending_data['total_spending'],
                'daily_average': spending_data['daily_average'],
                'top_category': spending_data['top_category']
            },
            'recommendations': recommendations,
            'insights': _generate_insights(spending_data)
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Failed to generate recommendations',
            'message': str(e)
        }), 500


def _gather_spending_data(user_id, start_date, end_date):
    """
    Gather spending data for AI analysis

    Returns a comprehensive summary of user's spending patterns
    """
    # Total spending
    total_result = db.session.query(
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count'),
        func.avg(Expense.amount).label('average')
    ).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).first()

    total_spending = float(total_result.total) if total_result.total else 0
    transaction_count = total_result.count or 0
    average_transaction = float(total_result.average) if total_result.average else 0

    # Spending by category
    category_spending = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).group_by(Expense.category).order_by(func.sum(Expense.amount).desc()).all()

    categories = {
        cat: {
            'total': float(total),
            'count': count,
            'percentage': (float(total) / total_spending * 100) if total_spending > 0 else 0
        }
        for cat, total, count in category_spending
    }

    # Top category
    top_category = category_spending[0][0] if category_spending else None

    # Calculate daily average
    days = (end_date - start_date).days + 1
    daily_average = total_spending / days if days > 0 else 0

    return {
        'total_spending': round(total_spending, 2),
        'transaction_count': transaction_count,
        'average_transaction': round(average_transaction, 2),
        'daily_average': round(daily_average, 2),
        'categories': categories,
        'top_category': top_category,
        'days': days
    }


def _generate_ai_recommendations(spending_data, days):
    """
    Generate AI-powered recommendations using Groq API

    Args:
        spending_data: Dictionary with spending analysis
        days: Number of days analyzed

    Returns:
        list: List of recommendation strings
    """
    try:
        # Build prompt for AI
        prompt = f"""You are a financial advisor analyzing a user's spending habits. Based on the data below, provide 5-7 specific, actionable savings recommendations.

Spending Analysis ({days} days):
- Total spent: ${spending_data['total_spending']}
- Daily average: ${spending_data['daily_average']}
- Number of transactions: {spending_data['transaction_count']}
- Average transaction: ${spending_data['average_transaction']}

Spending by Category:
"""

        for category, data in spending_data['categories'].items():
            prompt += f"- {category}: ${data['total']} ({data['percentage']:.1f}%) - {data['count']} transactions\n"

        prompt += """
Provide recommendations as a numbered list. Focus on:
1. Identifying overspending categories
2. Practical ways to reduce spending in top categories
3. Budget allocation suggestions
4. Spending pattern observations
5. Specific money-saving tips

Keep each recommendation concise (1-2 sentences) and actionable."""

        # Call Groq API
        headers = {
            'Authorization': f'Bearer {Config.GROQ_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': Config.GROQ_MODEL,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a helpful financial advisor providing personalized savings recommendations.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.7,
            'max_tokens': 500
        }

        response = requests.post(
            Config.GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()

            # Parse the numbered list into array
            recommendations = []
            for line in content.split('\n'):
                line = line.strip()
                # Remove numbering (1., 2., etc.)
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove leading number and punctuation
                    cleaned = line.lstrip('0123456789.-) ').strip()
                    if cleaned:
                        recommendations.append(cleaned)

            return recommendations if recommendations else [content]

        else:
            # Fallback recommendations if API fails
            return _generate_fallback_recommendations(spending_data)

    except Exception as e:
        print(f"AI recommendation error: {str(e)}")
        return _generate_fallback_recommendations(spending_data)


def _generate_fallback_recommendations(spending_data):
    """
    Generate basic recommendations without AI (fallback)
    """
    recommendations = []

    # General recommendations based on data
    if spending_data['top_category']:
        top_cat = spending_data['top_category']
        top_amount = spending_data['categories'][top_cat]['total']
        top_pct = spending_data['categories'][top_cat]['percentage']

        recommendations.append(
            f"{top_cat} is your highest expense at ${top_amount} ({top_pct:.0f}% of spending). "
            f"Consider reviewing this category for potential savings."
        )

    # Category-specific tips
    for category, data in spending_data['categories'].items():
        if data['percentage'] > 20:  # If category is more than 20% of spending
            if category == 'Groceries':
                recommendations.append(
                    "Try meal planning and using grocery lists to reduce impulse purchases."
                )
            elif category == 'Entertainment':
                recommendations.append(
                    "Look for free entertainment alternatives or share streaming subscriptions."
                )
            elif category == 'Shopping':
                recommendations.append(
                    "Implement a 24-hour rule before making non-essential purchases."
                )
            elif category == 'Transport':
                recommendations.append(
                    "Consider carpooling, public transit, or optimizing routes to save on transportation costs."
                )

    # Daily average tip
    recommendations.append(
        f"Your daily spending average is ${spending_data['daily_average']:.2f}. "
        f"Setting a daily budget can help control expenses."
    )

    # Generic savings tips
    recommendations.append(
        "Review recurring subscriptions and cancel unused services."
    )
    recommendations.append(
        "Set up automatic transfers to savings on payday to build an emergency fund."
    )

    return recommendations[:7]  # Return max 7 recommendations


def _generate_insights(spending_data):
    """
    Generate quick insights about spending patterns
    """
    insights = []

    # Transaction frequency
    avg_per_day = spending_data['transaction_count'] / spending_data['days']
    insights.append(f"You make an average of {avg_per_day:.1f} transactions per day")

    # Spending concentration
    if spending_data['categories']:
        top_3_pct = sum(
            data['percentage']
            for data in sorted(
                spending_data['categories'].values(),
                key=lambda x: x['percentage'],
                reverse=True
            )[:3]
        )
        insights.append(f"Your top 3 categories account for {top_3_pct:.0f}% of total spending")

    # Average transaction size
    insights.append(f"Average transaction size: ${spending_data['average_transaction']:.2f}")

    return insights
