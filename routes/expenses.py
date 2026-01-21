"""
Expense management routes
Handles CRUD operations and multi-format statement upload for expenses
Supports CSV, PDF, Excel (.xlsx, .xls) with password-protected PDFs
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from models import db, Expense, validate_category
from utils.categorizer import categorize_expense, categorize_with_ai, is_ambiguous_description, categorize_by_keywords, CATEGORY_KEYWORDS
from utils.csv_parser import parse_csv_file, validate_csv_format
from utils.unified_parser import parse_statement, parse_statement_with_summary
from utils.date_range_extractor import filter_by_date_range
from utils.session_manager import create_upload_session, get_upload_session, cleanup_session
from utils.exceptions import PDFPasswordError, InvalidFileFormatError, UnsupportedFormatError, ColumnDetectionError
from utils.auth_helpers import require_auth
from utils.transaction_parser import parse_transaction_description
from utils.merchant_categorizer import get_categorization_strategy
from utils.merchant_learning import get_learned_category
import json

# Create Blueprint for expense routes
expenses_bp = Blueprint('expenses', __name__)


@expenses_bp.route('/api/expenses', methods=['POST'])
@require_auth
@require_auth
def add_expense():
    """Add a single expense"""
    try:
        user_id = g.user_id
        data = request.get_json()

        # Validate required fields
        if not data or 'amount' not in data:
            return jsonify({'error': 'Missing required field: amount'}), 400

        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({'error': 'Amount must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid amount format'}), 400

        # Get or auto-categorize
        description = data.get('description', '').strip()
        category = data.get('category', '').strip()

        if not category:
            if description:
                category = categorize_expense(description, amount)
            else:
                category = 'Other'
        else:
            if not validate_category(category):
                return jsonify({'error': 'Invalid category'}), 400

        # Parse date (default to today)
        date_str = data.get('date')
        if date_str:
            try:
                expense_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        else:
            expense_date = datetime.utcnow()

        # Create expense
        expense = Expense(
            user_id=user_id,
            amount=amount,
            category=category,
            date=expense_date,
            description=description or None
        )

        db.session.add(expense)
        db.session.commit()

        return jsonify({
            'message': 'Expense added successfully',
            'expense': expense.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add expense', 'message': str(e)}), 500


@expenses_bp.route('/api/expenses', methods=['GET'])
@require_auth
@require_auth
def get_expenses():
    """Get all expenses for authenticated user"""
    try:
        user_id = g.user_id
        query = Expense.query.filter_by(user_id=user_id)

        # Apply filters
        start_date = request.args.get('start_date')
        if start_date:
            try:
                start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(Expense.date >= start)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400

        end_date = request.args.get('end_date')
        if end_date:
            try:
                end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(Expense.date <= end)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400

        category = request.args.get('category')
        if category:
            if not validate_category(category):
                return jsonify({'error': 'Invalid category'}), 400
            query = query.filter(Expense.category == category)

        # Order by date (most recent first)
        query = query.order_by(Expense.date.desc())

        # Apply pagination
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)

        if limit:
            query = query.limit(limit).offset(offset)

        # Execute query
        expenses = query.all()

        return jsonify({
            'expenses': [expense.to_dict() for expense in expenses],
            'count': len(expenses)
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to fetch expenses', 'message': str(e)}), 500


@expenses_bp.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@require_auth
def delete_expense(expense_id):
    """Delete an expense"""
    try:
        expense = Expense.query.get(expense_id)

        if not expense:
            return jsonify({'error': 'Expense not found'}), 404

        db.session.delete(expense)
        db.session.commit()

        return jsonify({'message': 'Expense deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete expense', 'message': str(e)}), 500


@expenses_bp.route('/api/expenses/<int:expense_id>/category', methods=['PATCH'])
@require_auth
def update_expense_category(expense_id):
    """
    Update the category of an expense and learn the merchant mapping

    Request:
        {
            "category": "Groceries"
        }

    Returns:
        200: {
            "message": "Category updated successfully",
            "expense": {...},
            "learned": bool  # True if mapping was saved/updated
        }
    """
    try:
        user_id = g.user_id
        # Get request data
        data = request.get_json()
        new_category = data.get('category')

        if not new_category:
            return jsonify({'error': 'Category is required'}), 400

        # Validate category
        if not validate_category(new_category):
            return jsonify({'error': f'Invalid category. Must be one of: {", ".join(EXPENSE_CATEGORIES)}'}), 400

        # Find expense
        expense = Expense.query.get(expense_id)
        if not expense:
            return jsonify({'error': 'Expense not found'}), 404

        # Update category
        old_category = expense.category
        expense.category = new_category
        db.session.commit()

        # LEARNING: Save merchant mapping so future imports use this category
        learned = False
        similar_updated = 0
        similar_items = []
        try:
            from utils.merchant_learning import save_merchant_category, normalize_merchant_name
            result = save_merchant_category(
                user_id=expense.user_id,
                description=expense.description,
                category=new_category
            )

            # AUTO-UPDATE: Find all similar transactions with same normalized merchant name
            merchant_name = normalize_merchant_name(expense.description)
            if merchant_name:
                # Find all similar transactions with same user - use normalized comparison
                similar_expenses = Expense.query.filter(
                    Expense.user_id == expense.user_id,
                    Expense.id != expense_id  # Exclude current expense
                ).all()
                
                # Filter by normalized merchant match (more reliable than LIKE)
                for similar_exp in similar_expenses:
                    similar_merchant_name = normalize_merchant_name(similar_exp.description)
                    if similar_merchant_name == merchant_name:
                        similar_items.append(similar_exp)

                # Update all similar transactions to the same category
                for similar_exp in similar_items:
                    similar_exp.category = new_category
                    similar_updated += 1

                if similar_updated > 0:
                    db.session.commit()
                    print(f"Auto-updated {similar_updated} similar transactions for merchant: {merchant_name}")
                    print(f"Updated descriptions: {[s.description for s in similar_items]}")
            learned = True
            print(f"Learned mapping: {expense.description} -> {new_category} ({result['action']})")
        except Exception as learn_error:
            # Don't fail the update if learning fails
            print(f"Warning: Could not save learned mapping: {learn_error}")
            import traceback
            traceback.print_exc()

        message = 'Category updated successfully'
        if similar_updated > 0:
            message += f' and {similar_updated} similar transaction(s) auto-updated'

        return jsonify({
            'message': message,
            'expense': expense.to_dict(),
            'learned': learned,
            'similar_updated': similar_updated,
            'similar_items': [s.to_dict() for s in similar_items],
            'old_category': old_category,
            'new_category': new_category
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update category', 'message': str(e)}), 500


@expenses_bp.route('/api/upload-statement', methods=['POST'])
@require_auth
def upload_statement():
    """
    Phase 1: Upload and extract transactions from bank statement

    Supports: CSV, PDF (encrypted/regular), Excel (.xlsx, .xls)

    Three-phase process:
    1. Upload & Extract → Returns date range info and session_id
    2. Select date range → Filter transactions (separate endpoint)
    3. Categorize & Import → Import with clarifications (separate endpoint)

    Request:
        - file: Uploaded file (CSV, PDF, Excel)
        - password: Optional password for encrypted PDFs

    Returns:
        200: {
            "status": "extracted",
            "file_type": str,
            "date_range": {...},
            "transaction_count": int,
            "preview": [...],
            "session_id": str
        }

        200 (password needed): {
            "status": "password_required",
            "message": str,
            "file_type": "pdf"
        }

        400: Error responses
    """
    try:
        user_id = g.user_id
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Validate file extension
        allowed_extensions = {'.csv', '.pdf', '.xlsx', '.xls'}
        file_ext = '.' + file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

        if file_ext not in allowed_extensions:
            return jsonify({
                'error': 'Unsupported file format',
                'message': f'Allowed formats: CSV, PDF, Excel (.xlsx, .xls)'
            }), 400

        # Read file content
        file_content = file.read()

        # Get password if provided
        password = request.form.get('password')

        # Parse statement using unified parser
        try:
            result = parse_statement_with_summary(
                file_content,
                file_type=None,  # Auto-detect
                password=password
            )

        except PDFPasswordError as e:
            # PDF needs password
            return jsonify({
                'status': 'password_required',
                'message': str(e),
                'file_type': 'pdf'
            }), 200

        except (InvalidFileFormatError, UnsupportedFormatError, ColumnDetectionError) as e:
            # File format errors
            return jsonify({
                'error': 'Invalid file format',
                'message': str(e)
            }), 400

        # Extract data from result
        transactions = result['transactions']
        file_type = result['file_type']
        date_range = result['date_range']
        summary = result['summary']

        if not transactions:
            return jsonify({'error': 'No valid transactions found in file'}), 400

        # Get clear_previous flag for later use
        clear_previous = request.form.get('clear_previous', 'true').lower() == 'true'

        # Create upload session
        session_data = {
            'transactions': transactions,
            'file_type': file_type,
            'filename': file.filename,
            'date_range': date_range,
            'summary': summary,
            'clear_previous': clear_previous
        }

        session_id = create_upload_session(session_data)

        # Create preview (first 5 transactions)
        preview = []
        for txn in transactions[:5]:
            preview.append({
                'date': txn['date'].strftime('%Y-%m-%d'),
                'description': txn['description'],
                'amount': txn['amount']
            })

        return jsonify({
            'status': 'extracted',
            'file_type': file_type,
            'date_range': date_range,
            'transaction_count': len(transactions),
            'summary': summary,
            'preview': preview,
            'session_id': session_id
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Failed to process bank statement',
            'message': str(e)
        }), 500


@expenses_bp.route('/api/select-date-range', methods=['POST'])
@require_auth
def select_date_range():
    """
    Phase 2: Filter transactions by user-selected date range

    Request:
        {
            "session_id": str,
            "start_date": str (YYYY-MM-DD),
            "end_date": str (YYYY-MM-DD)
        }

    Returns:
        200: {
            "status": "filtered",
            "filtered_count": int,
            "needs_clarification": bool,
            "ambiguous_items": [...] (if needs_clarification=true),
            "clear_count": int
        }

        Or if all clear:
        200: {
            "status": "ready",
            "filtered_count": int,
            "needs_clarification": false
        }
    """
    try:
        user_id = g.user_id
        data = request.get_json()

        # Validate request
        session_id = data.get('session_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400

        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required'}), 400

        # Get session data
        session_data = get_upload_session(session_id)

        if not session_data:
            return jsonify({'error': 'Upload session expired or not found. Please upload again.'}), 400

        # Filter transactions by date range
        transactions = session_data['transactions']
        filtered_transactions = filter_by_date_range(transactions, start_date, end_date)

        if not filtered_transactions:
            return jsonify({'error': 'No transactions found in selected date range'}), 400

        # Analyze filtered transactions for ambiguous items
        ambiguous_items = []
        clear_items = []

        # Import learning utilities
        from utils.merchant_learning import get_learned_category, normalize_merchant_name

        # Track which merchants we've already seen for grouping
        seen_merchants = {}  # normalized_name -> first occurrence info
        merchant_transaction_indices = {}  # normalized_name -> list of indices

        for idx, transaction in enumerate(filtered_transactions):
            description = transaction['description']
            amount = transaction['amount']
            transaction_type = transaction.get('type', 'expense')

            # Auto-categorize income transactions
            if transaction_type == 'income':
                clear_items.append({
                    'transaction': transaction,
                    'category': 'Income'
                })
                continue

            # Normalize merchant name for grouping
            normalized_name = normalize_merchant_name(description)

            # PRIORITY 1: Check if we've learned this merchant before
            learned = get_learned_category(user_id, description)

            if learned['found'] and learned['confidence'] >= 3:
                # Very high-confidence learned mapping - automatically categorize
                clear_items.append({
                    'transaction': transaction,
                    'category': learned['category']
                })
            elif learned['found'] and learned['confidence'] >= 1:
                # Medium-confidence learned mapping - use as AI suggestion but may need confirmation
                # Create a pseudo-suggestion object for learned mappings
                suggestion = {
                    'suggested_category': learned['category'],
                    'confidence': 'medium' if learned['confidence'] == 1 else 'high',
                    'alternatives': [],
                    'reasoning': f"Previously categorized as {learned['category']} ({learned['confidence']} time{'s' if learned['confidence'] > 1 else ''})",
                    'needs_clarification': False  # Don't require clarification for learned mappings
                }
                clear_items.append({
                    'transaction': transaction,
                    'category': learned['category']
                })
            else:
                # PRIORITY 2: Try keyword matching first (free, no API needed)
                keyword_category = categorize_by_keywords(description)
                if keyword_category:
                    # Keyword match found - auto-categorize without AI
                    clear_items.append({
                        'transaction': transaction,
                        'category': keyword_category
                    })
                    continue

                # PRIORITY 3: Only call AI if description is ambiguous (save tokens!)
                # Skip AI for non-ambiguous descriptions
                if is_ambiguous_description(description):
                    # Only AI for truly unclear items
                    suggestion = categorize_with_ai(description, amount, return_suggestions=True)

                    # Check if needs clarification
                    if suggestion['needs_clarification']:
                        # Track transaction index for this merchant
                        if normalized_name not in merchant_transaction_indices:
                            merchant_transaction_indices[normalized_name] = []
                        merchant_transaction_indices[normalized_name].append(idx)

                        # Only add to ambiguous_items if we haven't seen this merchant before
                        if normalized_name not in seen_merchants:
                            # Use AI suggestion
                            seen_merchants[normalized_name] = {
                                'index': idx,
                                'description': description,
                                'amount': amount,
                                'date': transaction['date'].isoformat(),
                                'suggested_category': suggestion['suggested_category'],
                                'confidence': suggestion['confidence'],
                                'alternatives': suggestion['alternatives'],
                                'reasoning': suggestion['reasoning'],
                                'normalized_merchant': normalized_name
                            }
                    else:
                        # AI categorized it clearly
                        clear_items.append({
                            'transaction': transaction,
                            'category': suggestion['suggested_category']
                        })
                else:
                    # Not ambiguous but no keyword match - use fallback
                    # This is rare but happens for unique merchant names that aren't in keywords
                    clear_items.append({
                        'transaction': transaction,
                        'category': 'Other'
                    })

        # Build final ambiguous_items list with transaction counts
        for normalized_name, item_info in seen_merchants.items():
            transaction_count = len(merchant_transaction_indices.get(normalized_name, [1]))
            item_info['transaction_count'] = transaction_count
            item_info['all_indices'] = merchant_transaction_indices.get(normalized_name, [item_info['index']])
            if transaction_count > 1:
                item_info['reasoning'] = f"{item_info['reasoning']} ({transaction_count} similar transactions)"
            ambiguous_items.append(item_info)

        # Update session with filtered transactions and analysis
        session_data['filtered_transactions'] = filtered_transactions
        session_data['ambiguous_items'] = ambiguous_items
        session_data['clear_items'] = clear_items
        session_data['selected_date_range'] = {'start_date': start_date, 'end_date': end_date}

        # Save updated session
        from utils.session_manager import update_upload_session
        update_upload_session(session_id, session_data)

        # Return response
        if ambiguous_items:
            return jsonify({
                'status': 'filtered',
                'filtered_count': len(filtered_transactions),
                'needs_clarification': True,
                'ambiguous_count': len(ambiguous_items),
                'clear_count': len(clear_items),
                'total_count': len(filtered_transactions),
                'ambiguous_items': ambiguous_items,
                'message': f'Found {len(ambiguous_items)} transaction(s) that need clarification'
            }), 200
        else:
            return jsonify({
                'status': 'ready',
                'filtered_count': len(filtered_transactions),
                'needs_clarification': False,
                'message': 'All transactions are ready to import'
            }), 200

    except ValueError as e:
        # Date parsing errors
        return jsonify({'error': 'Invalid date format', 'message': str(e)}), 400

    except Exception as e:
        return jsonify({
            'error': 'Failed to filter date range',
            'message': str(e)
        }), 500


@expenses_bp.route('/api/import-transactions', methods=['POST'])
@require_auth
def import_transactions():
    """
    Phase 3: Import transactions with user clarifications

    Request:
        {
            "session_id": str,
            "clarifications": {
                "0": "Food",
                "5": "Transportation"
            }
        }

    Returns:
        201: {
            "status": "imported",
            "message": str,
            "imported": int,
            "skipped": int,
            "total": int
        }
    """
    try:
        user_id = g.user_id
        data = request.get_json()

        # Validate request
        session_id = data.get('session_id')
        clarifications = data.get('clarifications', {})

        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400

        # Get session data
        session_data = get_upload_session(session_id)

        if not session_data:
            return jsonify({'error': 'Upload session expired or not found. Please upload again.'}), 400

        # Get filtered transactions (or all if no filtering was done)
        transactions = session_data.get('filtered_transactions', session_data['transactions'])
        clear_previous = session_data.get('clear_previous', True)

        # Clear previous expenses if requested
        if clear_previous:
            deleted_count = Expense.query.filter_by(user_id=user_id).delete()
            print(f"Cleared {deleted_count} previous expenses before import")

        # Import transactions
        imported_count = 0
        skipped_count = 0

        # Import learning utilities
        from utils.merchant_learning import save_merchant_category, normalize_merchant_name

        # STEP 1: Build a map of normalized merchant names to categories from clarifications
        # This allows applying the same category to all transactions with the same merchant
        clarification_merchant_map = {}
        for idx_str, category in clarifications.items():
            idx = int(idx_str)
            if idx < len(transactions):
                description = transactions[idx].get('description', '')
                normalized_name = normalize_merchant_name(description)
                if normalized_name and validate_category(category):
                    clarification_merchant_map[normalized_name] = category
                    # Save the learning immediately
                    try:
                        save_merchant_category(
                            user_id=user_id,
                            description=description,
                            category=category
                        )
                    except Exception as learn_error:
                        print(f"Warning: Could not save learned mapping: {learn_error}")

        for idx, transaction in enumerate(transactions):
            try:
                transaction_type = transaction.get('type', 'expense')

                # Check if user provided clarification for this transaction
                user_provided_category = False

                # First check by index (direct clarification)
                if str(idx) in clarifications:
                    category = clarifications[str(idx)]
                    user_provided_category = True
                    # Validate category
                    if not validate_category(category):
                        category = 'Uncategorized'
                        user_provided_category = False
                else:
                    # Check if another transaction with the same merchant was clarified
                    normalized_name = normalize_merchant_name(transaction.get('description', ''))
                    if normalized_name and normalized_name in clarification_merchant_map:
                        category = clarification_merchant_map[normalized_name]
                        user_provided_category = True  # Treat as user-provided since it came from a clarification

                # Parse transaction description for payment details
                parsed_transaction = parse_transaction_description(transaction['description'] or '')

                # If no category yet from clarifications, auto-categorize
                if not user_provided_category:
                    # Auto-categorize - use transaction type for income
                    if transaction_type == 'income':
                        category = 'Income'
                    else:
                        # PRIORITY 1: Check if we've learned this merchant before
                        learned = get_learned_category(user_id, transaction['description'])
                        if learned['found'] and learned['confidence'] >= 1:
                            # Use learned category (confidence >= 1 means user has confirmed it before)
                            category = learned['category']
                            print(f"Using learned category for '{transaction['description']}': {category} (confidence: {learned['confidence']})")
                        else:
                            # PRIORITY 2: Try keyword matching first (free, reliable, no API calls)
                            keyword_category = categorize_by_keywords(transaction['description'])
                            if keyword_category:
                                category = keyword_category
                            else:
                                # PRIORITY 3: Check if description is ambiguous (skip AI for clear descriptions)
                                if is_ambiguous_description(transaction['description']):
                                    # Only call AI for truly ambiguous descriptions (save tokens!)
                                    try:
                                        suggestion = categorize_with_ai(
                                            transaction['description'],
                                            transaction['amount'],
                                            return_suggestions=True
                                        )
                                        category = suggestion['suggested_category']
                                    except Exception as ai_error:
                                        # AI failed (likely rate limited) - use default
                                        print(f"Warning: AI categorization failed for '{transaction['description']}': {ai_error}")
                                        category = 'Other'
                                else:
                                    # Not ambiguous and no keyword match - rare case
                                    category = 'Other'

                # Create expense record with parsed transaction data
                expense = Expense(
                    user_id=user_id,
                    amount=transaction['amount'],
                    category=category,
                    date=transaction['date'],
                    description=transaction['description'],
                    payment_method=parsed_transaction['payment_method'],
                    upi_id=parsed_transaction['upi_id'],
                    transaction_ref=parsed_transaction['transaction_ref'],
                    merchant_id=None  # Will be linked later via merchant learning
                )

                db.session.add(expense)
                imported_count += 1

            except Exception as e:
                print(f"Error importing transaction {idx}: {str(e)}")
                skipped_count += 1
                continue

        # Commit all imports
        db.session.commit()

        # Cleanup session
        cleanup_session(session_id)

        return jsonify({
            'status': 'imported',
            'message': 'Bank statement imported successfully',
            'imported': imported_count,
            'skipped': skipped_count,
            'total': len(transactions)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to import transactions',
            'message': str(e)
        }), 500


def _analyze_transactions(transactions, clear_previous=False):
    """
    Analyze transactions and identify which ones need clarification

    Args:
        transactions: Parsed transactions from CSV
        clear_previous: If True, delete all previous expenses before importing

    Returns:
        - If ambiguous items found: Returns list of ambiguous transactions
        - If all clear: Imports directly and returns success
    """
    auto_categorize = True
    ambiguous_items = []
    clear_items = []

    for idx, transaction in enumerate(transactions):
        description = transaction['description']
        amount = transaction['amount']

        # PRIORITY 1: Try keyword matching first (free, no API needed)
        keyword_category = categorize_by_keywords(description)
        if keyword_category:
            # Keyword match found - auto-categorize without AI
            clear_items.append({
                'transaction': transaction,
                'category': keyword_category
            })
            continue

        # PRIORITY 2: Get AI suggestion with confidence (only if no keyword match)
        suggestion = categorize_with_ai(description, amount, return_suggestions=True)

        # Check if needs clarification
        if suggestion['needs_clarification']:
            ambiguous_items.append({
                'index': idx,
                'description': description,
                'amount': amount,
                'date': transaction['date'].isoformat(),
                'suggested_category': suggestion['suggested_category'],
                'confidence': suggestion['confidence'],
                'alternatives': suggestion['alternatives'],
                'reasoning': suggestion['reasoning']
            })
        else:
            # Auto-categorize clear transactions
            clear_items.append({
                'transaction': transaction,
                'category': suggestion['suggested_category']
            })

    # If there are ambiguous items, return them for user clarification
    if ambiguous_items:
        return jsonify({
            'needs_clarification': True,
            'ambiguous_count': len(ambiguous_items),
            'clear_count': len(clear_items),
            'total_count': len(transactions),
            'ambiguous_items': ambiguous_items,
            'clear_previous': clear_previous,  # Pass along the flag
            'message': f'Found {len(ambiguous_items)} transaction(s) that need clarification'
        }), 200

    # If all items are clear, import them directly
    # Clear previous expenses if requested
    if clear_previous:
        deleted_count = Expense.query.filter_by(user_id=user_id).delete()
        print(f"Cleared {deleted_count} previous expenses")

    imported_count = 0
    for item in clear_items:
        try:
            expense = Expense(
                user_id=user_id,
                amount=item['transaction']['amount'],
                category=item['category'],
                date=item['transaction']['date'],
                description=item['transaction']['description']
            )
            db.session.add(expense)
            imported_count += 1
        except Exception as e:
            print(f"Error importing transaction: {str(e)}")
            continue

    db.session.commit()

    return jsonify({
        'needs_clarification': False,
        'message': 'All transactions imported successfully',
        'imported': imported_count,
        'total': len(transactions)
    }), 201


def _import_with_clarifications(transactions, clarifications, clear_previous=False):
    """
    Import transactions with user-provided clarifications

    Args:
        transactions: Parsed transactions from CSV
        clarifications: Dict mapping transaction index to user-selected category
        clear_previous: If True, delete all previous expenses before importing
    """
    # Clear previous expenses if requested
    if clear_previous:
        deleted_count = Expense.query.filter_by(user_id=user_id).delete()
        print(f"Cleared {deleted_count} previous expenses before import")

    imported_count = 0
    skipped_count = 0

    for idx, transaction in enumerate(transactions):
        try:
            # Check if user provided clarification for this transaction
            if str(idx) in clarifications:
                category = clarifications[str(idx)]
                # Validate category
                if not validate_category(category):
                    category = 'Uncategorized'
            else:
                # Auto-categorize if no clarification provided
                suggestion = categorize_with_ai(
                    transaction['description'],
                    transaction['amount'],
                    return_suggestions=True
                )
                category = suggestion['suggested_category']

            # Create expense record
            expense = Expense(
                user_id=user_id,
                amount=transaction['amount'],
                category=category,
                date=transaction['date'],
                description=transaction['description']
            )

            db.session.add(expense)
            imported_count += 1

        except Exception as e:
            print(f"Error importing transaction {idx}: {str(e)}")
            skipped_count += 1
            continue

    # Commit all imports
    db.session.commit()

    return jsonify({
        'needs_clarification': False,
        'message': 'Bank statement imported successfully',
        'imported': imported_count,
        'skipped': skipped_count,
        'total': len(transactions)
    }), 201


@expenses_bp.route('/api/categorize-suggestion', methods=['POST'])
@require_auth
def get_category_suggestion():
    """
    Get AI-powered category suggestions for ambiguous expenses

    Request body:
        {
            "description": str (required),
            "amount": float (optional)
        }

    Returns:
        200: {
            "is_ambiguous": bool,
            "suggested_category": str,
            "confidence": str ("high", "medium", "low"),
            "alternatives": [str],
            "reasoning": str,
            "needs_clarification": bool
        }
    """
    try:
        user_id = g.user_id
        data = request.get_json()

        description = data.get('description', '').strip()
        if not description:
            return jsonify({'error': 'Description is required'}), 400

        amount = data.get('amount')

        # Check if description is ambiguous
        is_amb = is_ambiguous_description(description)

        # Get AI suggestions
        suggestion = categorize_with_ai(description, amount, return_suggestions=True)

        return jsonify({
            'is_ambiguous': is_amb,
            **suggestion
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to get suggestion', 'message': str(e)}), 500
