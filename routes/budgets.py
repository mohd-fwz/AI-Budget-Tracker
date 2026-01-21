"""
Budget routes - Manages user budgets and AI-powered recommendations
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from models import db, Budget, UserProfile, Expense
from sqlalchemy import func, extract
from utils.budget_recommender import generate_simple_recommendations
from utils.smart_budget_calculator import (
    calculate_groceries_budget,
    calculate_transport_budget,
    calculate_entertainment_budget,
    calculate_bills_budget,
    calculate_generic_budget
)
from utils.auth_helpers import require_auth
import json

budgets_bp = Blueprint('budgets', __name__)


@budgets_bp.route('/api/budgets/generate', methods=['POST'])
@require_auth
def generate_budget_recommendations():
    """
    Generate AI-powered budget recommendations using:
    1. ACTUAL income from uploaded bank statements (not profile estimate)
    2. User preferences (groceries consumption, transport mode)
    3. Market prices in user's city
    4. Historical spending patterns
    """
    try:
        user_id = g.user_id
        data = request.get_json() or {}

        # Target month for budget
        target_month = data.get('target_month')
        if not target_month:
            next_month = datetime.now().month + 1
            year = datetime.now().year
            if next_month > 12:
                next_month = 1
                year += 1
            target_month = f"{year}-{next_month:02d}"

        # Parse target month
        target_year, target_month_num = map(int, target_month.split('-'))

        # Get user profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return jsonify({
                'error': 'Profile not found',
                'message': 'Please complete your profile first'
            }), 404

        # ===== NEW: Predict actual income for target month =====
        from utils.income_analyzer import predict_next_month_income, get_average_income_last_n_months

        income_prediction = predict_next_month_income(
            db.session,
            user_id,
            target_year,
            target_month_num
        )

        predicted_income = income_prediction['predicted_income']
        income_confidence = income_prediction['confidence']
        income_reasoning = income_prediction['reasoning']

        # Get historical income trend for context
        income_history = get_average_income_last_n_months(db.session, user_id, months=3)

        # Get historical spending by category (last 6 months)
        historical = get_historical_spending_by_category(user_id, months_back=6)

        # ===== NEW: Get LAST MONTH's actual spending for overspending analysis =====
        last_month_spending = get_last_month_spending_by_category(user_id)

        # Parse category preferences
        preferences = json.loads(profile.category_preferences or '{}')

        # Get city for market prices
        city = profile.city or 'Bangalore'

        # Define all expense categories
        EXPENSE_CATEGORIES = [
            'Groceries', 'Transport', 'Entertainment',
            'Shopping', 'Bills', 'Healthcare', 'Education', 'Other'
        ]

        # ===== NEW: Recommended spending limits based on income =====
        # Standard budget allocation percentages (based on 50/30/20 rule adapted for India)
        monthly_income = float(profile.monthly_income) if profile.monthly_income else predicted_income
        savings_goal = float(profile.savings_goal or 0)
        available_budget = monthly_income - savings_goal

        RECOMMENDED_PERCENTAGES = {
            'Groceries': 15,      # 15% of available budget
            'Transport': 10,     # 10%
            'Entertainment': 10, # 10%
            'Shopping': 10,      # 10%
            'Bills': 25,         # 25% (includes rent, utilities)
            'Healthcare': 5,     # 5%
            'Education': 5,      # 5%
            'Other': 10          # 10%
        }

        # Generate recommendations for each category
        recommendations = []
        overspending_alerts = []

        for category in EXPENSE_CATEGORIES:
            category_prefs = preferences.get(category, {})
            historical_avg = historical.get(category, 0)

            if category == 'Groceries' and category_prefs:
                # Use smart calculator with user preferences
                rec = calculate_groceries_budget(
                    preferences=category_prefs,
                    city=city,
                    historical_avg=historical_avg,
                    use_ai=True
                )
            elif category == 'Transport' and category_prefs:
                # Use smart calculator with user preferences
                rec = calculate_transport_budget(
                    preferences=category_prefs,
                    city=city,
                    historical_avg=historical_avg,
                    use_ai=True
                )
            elif category == 'Entertainment' and category_prefs:
                # Use entertainment calculator with AI cost estimation
                rec = calculate_entertainment_budget(
                    preferences=category_prefs,
                    city=city,
                    historical_avg=historical_avg,
                    use_ai=True
                )
            elif category == 'Bills' and category_prefs:
                # Use bills calculator
                rec = calculate_bills_budget(
                    preferences=category_prefs,
                    city=city,
                    historical_avg=historical_avg
                )
            else:
                # Fallback to generic calculator for other categories
                rec = calculate_generic_budget(
                    category=category,
                    historical_avg=historical_avg
                )

            rec['category'] = category
            rec['is_ai_suggested'] = True

            # ===== NEW: Add overspending analysis for each category =====
            recommended_limit = (available_budget * RECOMMENDED_PERCENTAGES.get(category, 10)) / 100
            actual_last_month = last_month_spending.get(category, 0)

            rec['recommended_limit'] = round(recommended_limit, 2)
            rec['actual_last_month'] = round(actual_last_month, 2)

            # Check for overspending
            if actual_last_month > 0:
                if actual_last_month > recommended_limit:
                    overspend_amount = actual_last_month - recommended_limit
                    overspend_percent = ((actual_last_month - recommended_limit) / recommended_limit * 100) if recommended_limit > 0 else 100
                    rec['overspending'] = {
                        'is_overspent': True,
                        'amount': round(overspend_amount, 2),
                        'percent': round(overspend_percent, 1),
                        'message': f"⚠️ You spent ₹{actual_last_month:,.0f} last month, which is ₹{overspend_amount:,.0f} ({overspend_percent:.0f}%) over the recommended limit of ₹{recommended_limit:,.0f}"
                    }
                    overspending_alerts.append({
                        'category': category,
                        'actual': actual_last_month,
                        'recommended': recommended_limit,
                        'overspend_amount': overspend_amount,
                        'overspend_percent': overspend_percent
                    })
                else:
                    rec['overspending'] = {
                        'is_overspent': False,
                        'message': f"✓ You spent ₹{actual_last_month:,.0f} last month, within the recommended limit of ₹{recommended_limit:,.0f}"
                    }
            else:
                rec['overspending'] = {
                    'is_overspent': False,
                    'message': f"No spending recorded last month. Recommended limit: ₹{recommended_limit:,.0f}"
                }

            recommendations.append(rec)

        # Calculate totals
        total_budget = sum(r['suggested_amount'] for r in recommendations)
        total_last_month_spending = sum(last_month_spending.values())

        # ===== NEW: Income-aware budget adjustment =====
        # If predicted income is less than suggested budget, adjust recommendations proportionally
        budget_adjustment_factor = 1.0
        budget_warning = None
        ai_budget_reasoning = []

        if predicted_income > 0:
            # Reserve for savings goal
            savings_goal_amount = float(profile.savings_goal or 0)
            available_for_expenses = predicted_income - savings_goal_amount

            if available_for_expenses < total_budget:
                # Need to reduce budget
                budget_adjustment_factor = available_for_expenses / total_budget if total_budget > 0 else 0
                budget_warning = f"Budget reduced by {(1-budget_adjustment_factor)*100:.1f}% to fit expected income of ₹{predicted_income:,.0f}"

                # Adjust all recommendations proportionally
                for rec in recommendations:
                    original = rec['suggested_amount']
                    rec['suggested_amount'] = round(original * budget_adjustment_factor, 2)
                    rec['adjustment_applied'] = True
                    rec['original_amount'] = original

                total_budget = sum(r['suggested_amount'] for r in recommendations)

                ai_budget_reasoning.append({
                    'type': 'income_constraint',
                    'message': f"Your expected income is ₹{predicted_income:,.0f}. After savings goal of ₹{savings_goal_amount:,.0f}, you have ₹{available_for_expenses:,.0f} available. Budget adjusted to fit."
                })
            else:
                ai_budget_reasoning.append({
                    'type': 'income_sufficient',
                    'message': f"Budget of ₹{total_budget:,.0f} fits within expected income of ₹{predicted_income:,.0f}"
                })

        # Calculate savings potential using ACTUAL predicted income
        savings_potential = None
        savings_rate = None
        if predicted_income > 0:
            savings_potential = predicted_income - total_budget
            savings_rate = (savings_potential / predicted_income) * 100

            if savings_potential < 0:
                ai_budget_reasoning.append({
                    'type': 'overspending_warning',
                    'message': f"⚠️ Budget exceeds income by ₹{abs(savings_potential):,.0f}. Consider reducing expenses."
                })
            elif savings_potential > 0:
                ai_budget_reasoning.append({
                    'type': 'savings_possible',
                    'message': f"You can save ₹{savings_potential:,.0f} ({savings_rate:.1f}%) this month!"
                })

        # Check if meets savings goal
        meets_savings_goal = False
        if profile.savings_goal and savings_potential:
            meets_savings_goal = savings_potential >= float(profile.savings_goal)
            if not meets_savings_goal:
                shortfall = float(profile.savings_goal) - savings_potential
                ai_budget_reasoning.append({
                    'type': 'savings_goal_shortfall',
                    'message': f"You're ₹{shortfall:,.0f} short of your ₹{profile.savings_goal:,.0f} savings goal. Try reducing expenses."
                })

        # Add income analysis reasoning
        ai_budget_reasoning.insert(0, {
            'type': 'income_analysis',
            'message': income_reasoning,
            'confidence': income_confidence
        })

        return jsonify({
            'success': True,
            'target_month': target_month,
            'recommendations': recommendations,
            'total_suggested_budget': round(total_budget, 2),

            # NEW: Actual income prediction (not profile estimate)
            'predicted_income': round(predicted_income, 2),
            'income_confidence': income_confidence,
            'income_method': income_prediction['method'],
            'income_history': income_history,

            # Keep profile income for reference
            'profile_income': float(profile.monthly_income) if profile.monthly_income else None,

            # Savings calculations
            'savings_potential': round(savings_potential, 2) if savings_potential else None,
            'savings_rate': round(savings_rate, 2) if savings_rate else None,
            'savings_goal': float(profile.savings_goal) if profile.savings_goal else None,
            'meets_savings_goal': meets_savings_goal,

            # NEW: AI reasoning and explanations
            'ai_reasoning': ai_budget_reasoning,
            'budget_warning': budget_warning,
            'budget_adjusted': budget_adjustment_factor < 1.0,

            # ===== NEW: Overspending Analysis =====
            'overspending_analysis': {
                'last_month_total': round(total_last_month_spending, 2),
                'available_budget': round(available_budget, 2),
                'is_over_budget': total_last_month_spending > available_budget,
                'overspend_total': round(total_last_month_spending - available_budget, 2) if total_last_month_spending > available_budget else 0,
                'alerts': overspending_alerts,
                'categories_overspent': len(overspending_alerts)
            },

            # Other metadata
            'location': {'city': city, 'state': profile.state} if profile.state else None,
            'analysis_period': 6,
            'generated_at': datetime.now().isoformat()
        }), 200

    except Exception as e:
        print(f"Budget generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to generate recommendations',
            'message': str(e)
        }), 500


def get_historical_spending_by_category(user_id: str, months_back: int = 6) -> dict:
    """
    Get average monthly spending by category over last N months

    Args:
        user_id: User ID
        months_back: Number of months to analyze

    Returns:
        Dict mapping category to average monthly spending
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months_back)

    # Get all expenses in the period grouped by category and month
    results = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('monthly_total'),
        extract('year', Expense.date).label('year'),
        extract('month', Expense.date).label('month')
    ).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date,
        Expense.category != 'Income'
    ).group_by(
        Expense.category,
        extract('year', Expense.date),
        extract('month', Expense.date)
    ).all()

    # Calculate average for each category
    category_totals = {}
    category_months = {}

    for row in results:
        category = row.category
        amount = float(row.monthly_total or 0)

        if category not in category_totals:
            category_totals[category] = 0
            category_months[category] = 0

        category_totals[category] += amount
        category_months[category] += 1

    # Calculate averages
    category_averages = {}
    for category, total in category_totals.items():
        months = category_months[category]
        category_averages[category] = total / months if months > 0 else 0

    return category_averages


def get_last_month_spending_by_category(user_id: str) -> dict:
    """
    Get actual spending by category for the LAST MONTH only

    Args:
        user_id: User ID

    Returns:
        Dict mapping category to last month's total spending
    """
    # Calculate last month's date range
    today = datetime.now()

    # Go to first day of current month, then subtract 1 day to get last month
    first_of_current = today.replace(day=1)
    last_of_previous = first_of_current - timedelta(days=1)
    first_of_previous = last_of_previous.replace(day=1)

    # Get spending grouped by category for last month
    results = db.session.query(
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        Expense.date >= first_of_previous,
        Expense.date <= last_of_previous,
        Expense.category != 'Income'
    ).group_by(Expense.category).all()

    return {row.category: float(row.total or 0) for row in results}


@budgets_bp.route('/api/budgets/<month>', methods=['GET'])
@require_auth
def get_budgets(month):
    try:
        user_id = g.user_id
        budgets = Budget.query.filter_by(user_id=user_id, month=month).all()
        return jsonify({
            'month': month,
            'budgets': [b.to_dict() for b in budgets],
            'total_budget': sum(float(b.amount) for b in budgets)
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch budgets', 'message': str(e)}), 500


@budgets_bp.route('/api/budgets', methods=['POST'])
@require_auth
def save_budgets():
    try:
        user_id = g.user_id
        data = request.get_json()
        month = data.get('month')
        budgets_data = data.get('budgets', [])
        
        if not month or not budgets_data:
            return jsonify({'error': 'Month and budgets are required'}), 400
        
        saved = []
        for b in budgets_data:
            existing = Budget.query.filter_by(user_id=user_id, month=month, category=b['category']).first()
            if existing:
                existing.amount = b['amount']
                existing.is_ai_suggested = 1 if b.get('is_ai_suggested') else 0
                saved.append(existing)
            else:
                new_budget = Budget(user_id=user_id, month=month, category=b['category'],
                                   amount=b['amount'], is_ai_suggested=1 if b.get('is_ai_suggested') else 0)
                db.session.add(new_budget)
                saved.append(new_budget)
        
        db.session.commit()
        return jsonify({'message': 'Budgets saved', 'budgets': [b.to_dict() for b in saved]}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save budgets', 'message': str(e)}), 500


@budgets_bp.route('/api/budgets/vs-actual/<month>', methods=['GET'])
@require_auth
def compare_budget_vs_actual(month):
    try:
        user_id = g.user_id
        budgets = Budget.query.filter_by(user_id=user_id, month=month).all()
        year, month_num = map(int, month.split('-'))
        
        actual = db.session.query(Expense.category, func.sum(Expense.amount).label('total')).filter(
            Expense.user_id == user_id,
            extract('year', Expense.date) == year,
            extract('month', Expense.date) == month_num,
            Expense.category != 'Income'
        ).group_by(Expense.category).all()
        
        actual_dict = {r.category: float(r.total) for r in actual}
        comparison = []
        
        for b in budgets:
            act = actual_dict.get(b.category, 0)
            diff = act - float(b.amount)
            pct = (act / float(b.amount) * 100) if b.amount > 0 else 0
            comparison.append({
                'category': b.category,
                'budgeted': float(b.amount),
                'actual': act,
                'difference': diff,
                'percentage_used': round(pct, 1),
                'status': 'over' if diff > 0 else 'under' if diff < 0 else 'on_track'
            })
        
        return jsonify({
            'month': month,
            'comparison': comparison,
            'summary': {
                'total_budgeted': sum(float(b.amount) for b in budgets),
                'total_actual': sum(actual_dict.values())
            }
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to compare budgets', 'message': str(e)}), 500
