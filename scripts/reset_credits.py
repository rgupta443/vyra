#!/usr/bin/env python3
"""
Reset user credits for testing purposes.
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from sqlalchemy import update


def reset_credits(credits: int = 10, email: str = None):
    """
    Reset credits for users.
    
    Args:
        credits: Number of credits to set (default: 10)
        email: Optional email to reset specific user, otherwise resets all users
    """
    db = SessionLocal()
    try:
        if email:
            # Reset specific user
            result = db.execute(
                update(User)
                .where(User.email == email)
                .values(credits=credits)
            )
            db.commit()
            if result.rowcount > 0:
                print(f'✅ Reset credits to {credits} for user: {email}')
            else:
                print(f'❌ User not found: {email}')
        else:
            # Reset all users
            db.execute(update(User).values(credits=credits))
            db.commit()
            print(f'✅ Reset credits to {credits} for all users')
    except Exception as e:
        print(f'❌ Error: {e}')
        db.rollback()
    finally:
        db.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--help':
            print('Usage:')
            print('  python scripts/reset_credits.py              # Reset all users to 10 credits')
            print('  python scripts/reset_credits.py 50           # Reset all users to 50 credits')
            print('  python scripts/reset_credits.py 50 user@example.com  # Reset specific user to 50 credits')
        elif len(sys.argv) == 3:
            reset_credits(int(sys.argv[1]), sys.argv[2])
        else:
            reset_credits(int(sys.argv[1]))
    else:
        reset_credits()
