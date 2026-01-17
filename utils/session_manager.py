"""
Session management for multi-phase file uploads
Uses file-based storage for simplicity (no Redis dependency)
"""
import os
import pickle
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from config import Config
from .exceptions import SessionExpiredError

# Directory for storing session files
TEMP_DIR = 'temp_sessions'

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)


def create_upload_session(data: dict) -> str:
    """
    Create a new upload session and store data

    Args:
        data: Dictionary containing session data
              Typically includes:
              - transactions: List of parsed transactions
              - file_type: Type of uploaded file (pdf, excel, csv)
              - original_filename: Original file name
              - (optional) filtered_transactions: After date range selection

    Returns:
        str: Session ID (UUID)

    Storage:
        Creates a pickle file: temp_sessions/{session_id}.pkl
        Includes timestamp for expiration tracking
    """
    session_id = str(uuid.uuid4())
    session_file = os.path.join(TEMP_DIR, f'{session_id}.pkl')

    session_data = {
        'data': data,
        'created_at': datetime.utcnow(),
        'session_id': session_id
    }

    try:
        with open(session_file, 'wb') as f:
            pickle.dump(session_data, f)

        print(f"Created upload session: {session_id}")
        return session_id

    except Exception as e:
        print(f"Error creating session: {str(e)}")
        raise


def get_upload_session(session_id: str) -> dict:
    """
    Retrieve upload session data

    Args:
        session_id: Session UUID

    Returns:
        dict: Session data

    Raises:
        SessionExpiredError: If session doesn't exist or is expired
    """
    session_file = os.path.join(TEMP_DIR, f'{session_id}.pkl')

    if not os.path.exists(session_file):
        raise SessionExpiredError(
            "Upload session not found or expired. Please upload the file again."
        )

    try:
        with open(session_file, 'rb') as f:
            session_data = pickle.load(f)

        # Check if session is expired
        created_at = session_data['created_at']
        expiration_time = created_at + timedelta(seconds=Config.UPLOAD_SESSION_TIMEOUT)

        if datetime.utcnow() > expiration_time:
            # Clean up expired session
            cleanup_session(session_id)
            raise SessionExpiredError(
                "Upload session expired. Please upload the file again."
            )

        return session_data['data']

    except (pickle.UnpicklingError, KeyError, EOFError) as e:
        # Corrupted session file
        cleanup_session(session_id)
        raise SessionExpiredError(
            f"Session data corrupted: {str(e)}. Please upload the file again."
        )


def update_upload_session(session_id: str, updates: dict) -> None:
    """
    Update existing session with new data

    Args:
        session_id: Session UUID
        updates: Dictionary of updates to merge into session data

    Raises:
        SessionExpiredError: If session doesn't exist
    """
    # Get existing session
    session_data_dict = get_upload_session(session_id)

    # Merge updates
    session_data_dict.update(updates)

    # Re-save session
    session_file = os.path.join(TEMP_DIR, f'{session_id}.pkl')

    session_data = {
        'data': session_data_dict,
        'created_at': datetime.utcnow(),  # Reset timestamp
        'session_id': session_id
    }

    try:
        with open(session_file, 'wb') as f:
            pickle.dump(session_data, f)

        print(f"Updated session: {session_id}")

    except Exception as e:
        print(f"Error updating session: {str(e)}")
        raise


def cleanup_session(session_id: str) -> bool:
    """
    Delete a specific session

    Args:
        session_id: Session UUID

    Returns:
        bool: True if deleted, False if not found
    """
    session_file = os.path.join(TEMP_DIR, f'{session_id}.pkl')

    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            print(f"Cleaned up session: {session_id}")
            return True
        except Exception as e:
            print(f"Error cleaning up session: {str(e)}")
            return False

    return False


def cleanup_old_sessions() -> int:
    """
    Clean up all expired sessions

    Returns:
        int: Number of sessions cleaned up

    Called periodically to prevent disk space buildup
    Should be run on application startup and periodically during operation
    """
    if not os.path.exists(TEMP_DIR):
        return 0

    cleaned_count = 0
    cutoff_time = datetime.utcnow() - timedelta(seconds=Config.UPLOAD_SESSION_TIMEOUT)

    try:
        for filename in os.listdir(TEMP_DIR):
            if not filename.endswith('.pkl'):
                continue

            filepath = os.path.join(TEMP_DIR, filename)

            try:
                # Check file creation time
                file_mtime = datetime.utcfromtimestamp(os.path.getmtime(filepath))

                if file_mtime < cutoff_time:
                    os.remove(filepath)
                    cleaned_count += 1

            except Exception as e:
                print(f"Error processing session file {filename}: {str(e)}")
                continue

        if cleaned_count > 0:
            print(f"Cleaned up {cleaned_count} expired session(s)")

        return cleaned_count

    except Exception as e:
        print(f"Error during session cleanup: {str(e)}")
        return cleaned_count


def get_session_info() -> Dict:
    """
    Get information about all active sessions

    Returns:
        dict: {
            'active_sessions': int,
            'total_size_mb': float,
            'oldest_session_age_minutes': int
        }

    Useful for monitoring and debugging
    """
    if not os.path.exists(TEMP_DIR):
        return {
            'active_sessions': 0,
            'total_size_mb': 0,
            'oldest_session_age_minutes': 0
        }

    session_files = [
        f for f in os.listdir(TEMP_DIR)
        if f.endswith('.pkl')
    ]

    total_size = sum(
        os.path.getsize(os.path.join(TEMP_DIR, f))
        for f in session_files
    )

    oldest_age = 0
    if session_files:
        oldest_mtime = min(
            os.path.getmtime(os.path.join(TEMP_DIR, f))
            for f in session_files
        )
        oldest_age = int((datetime.utcnow().timestamp() - oldest_mtime) / 60)

    return {
        'active_sessions': len(session_files),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'oldest_session_age_minutes': oldest_age
    }
