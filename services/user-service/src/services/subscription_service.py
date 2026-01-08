"""Subscription service for handling user subscription upgrades."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict
from sqlalchemy.orm import Session

from models import User

logger = logging.getLogger(__name__)

# VietQR configuration for Vietcombank
VIETQR_BANK_CODE = "VCB"
VIETQR_ACCOUNT_NUMBER = "1013036074"
VIETQR_ACCOUNT_NAME = "PathLight"
VIETQR_TEMPLATE = "compact2"  # or "compact", "print"

SUBSCRIPTION_PRICES = {
    1: 100000,  # Premium: 100k VND
    2: 300000,  # Pro: 300k VND
}

SUBSCRIPTION_NAMES = {
    0: "Free",
    1: "Premium", 
    2: "Pro",
}


def generate_vietqr_url(
    amount: int,
    description: str,
    account_number: str = VIETQR_ACCOUNT_NUMBER,
    bank_code: str = VIETQR_BANK_CODE,
    account_name: str = VIETQR_ACCOUNT_NAME,
    template: str = VIETQR_TEMPLATE,
) -> str:
    """
    Generate VietQR URL for bank transfer QR code.
    
    Args:
        amount: Amount in VND
        description: Transfer description
        account_number: Bank account number
        bank_code: Bank code (VCB for Vietcombank)
        account_name: Account holder name
        template: QR code template (compact, compact2, print)
    
    Returns:
        URL to QR code image
    """
    base_url = f"https://img.vietqr.io/image/{bank_code}-{account_number}-{template}.png"
    params = f"?amount={amount}&addInfo={description}&accountName={account_name}"
    return base_url + params


def create_subscription_request(
    user: User,
    target_subscription: int,
    db: Session
) -> Dict:
    """
    Create a subscription upgrade request and generate payment QR code.
    
    Args:
        user: User requesting the upgrade
        target_subscription: Target subscription level (1=Premium, 2=Pro)
        db: Database session
    
    Returns:
        Dict with payment details and QR code URL
    """
    try:
        current_subscription = getattr(user, 'subscription', 0)
        
        # Validate target subscription
        if target_subscription not in [1, 2]:
            return {
                "success": False,
                "message": "Gói đăng ký không hợp lệ. Chỉ có Premium (1) hoặc Pro (2)."
            }
        
        # Check if user is trying to downgrade
        if target_subscription <= current_subscription:
            return {
                "success": False,
                "message": f"Bạn đang sử dụng gói {SUBSCRIPTION_NAMES[current_subscription]}. Không thể chuyển xuống gói thấp hơn."
            }
        
        # Get price
        amount = SUBSCRIPTION_PRICES[target_subscription]
        
        # Generate unique transaction reference
        transaction_ref = str(uuid.uuid4())[:8].upper()
        
        # Create description for bank transfer
        user_id_short = str(user.id)[:8]
        description = f"PATHLIGHT {transaction_ref} SUB{target_subscription} {user_id_short}"
        
        # Generate QR code URL
        qr_url = generate_vietqr_url(
            amount=amount,
            description=description
        )
        
        logger.info(
            f"Subscription request created: user={user.email}, "
            f"from={current_subscription} to={target_subscription}, "
            f"ref={transaction_ref}"
        )
        
        return {
            "success": True,
            "transaction_ref": transaction_ref,
            "current_subscription": current_subscription,
            "target_subscription": target_subscription,
            "subscription_name": SUBSCRIPTION_NAMES[target_subscription],
            "amount": amount,
            "qr_url": qr_url,
            "bank_info": {
                "bank_name": "Vietcombank",
                "account_number": VIETQR_ACCOUNT_NUMBER,
                "account_name": VIETQR_ACCOUNT_NAME,
                "description": description
            },
            "message": f"Vui lòng chuyển khoản {amount:,} VND với nội dung: {description}"
        }
        
    except Exception as e:
        logger.error(f"Error creating subscription request: {e}")
        return {
            "success": False,
            "message": "Có lỗi xảy ra khi tạo yêu cầu đăng ký. Vui lòng thử lại."
        }


def get_subscription_info(subscription_level: int) -> Dict:
    """
    Get information about a subscription level.
    
    Args:
        subscription_level: Subscription level (0, 1, or 2)
    
    Returns:
        Dict with subscription details
    """
    features = {
        0: {
            "name": "Free",
            "price": 0,
            "quiz_questions": 30,
            "powerup_uses": 1,
            "features": [
                "30 câu hỏi/quiz",
                "1 lần dùng power-up",
                "Tính năng cơ bản"
            ]
        },
        1: {
            "name": "Premium",
            "price": 100000,
            "quiz_questions": 45,
            "powerup_uses": 2,
            "features": [
                "45 câu hỏi/quiz",
                "2 lần dùng power-up",
                "Nhiều tính năng",
                "Hỗ trợ ưu tiên"
            ]
        },
        2: {
            "name": "Pro",
            "price": 300000,
            "quiz_questions": 60,
            "powerup_uses": 3,
            "features": [
                "60 câu hỏi/quiz",
                "3 lần dùng power-up",
                "Tất cả tính năng",
                "Hỗ trợ VIP",
                "Badge đặc biệt"
            ]
        }
    }
    
    return features.get(subscription_level, features[0])


def verify_and_upgrade_subscription(
    user: User,
    transaction_ref: str,
    target_subscription: int,
    db: Session
) -> Dict:
    """
    Verify payment and upgrade user subscription.
    This is a placeholder - in production, you should verify the actual bank transaction.
    
    Args:
        user: User to upgrade
        transaction_ref: Transaction reference code
        target_subscription: Target subscription level
        db: Database session
    
    Returns:
        Dict with upgrade result
    """
    try:
        # In production, you should:
        # 1. Call bank API to verify the transaction
        # 2. Check if amount matches
        # 3. Check if description matches
        # 4. Mark transaction as used to prevent double spending
        
        # For now, admin will manually verify and call this endpoint
        current_subscription = getattr(user, 'subscription', 0)
        
        if target_subscription <= current_subscription:
            return {
                "success": False,
                "message": "Không thể nâng cấp xuống gói thấp hơn hoặc bằng gói hiện tại."
            }
        
        # Update subscription
        setattr(user, 'subscription', target_subscription)
        db.commit()
        
        logger.info(
            f"Subscription upgraded: user={user.email}, "
            f"from={current_subscription} to={target_subscription}, "
            f"ref={transaction_ref}"
        )
        
        return {
            "success": True,
            "new_subscription": target_subscription,
            "subscription_name": SUBSCRIPTION_NAMES[target_subscription],
            "message": f"Nâng cấp lên gói {SUBSCRIPTION_NAMES[target_subscription]} thành công!"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error upgrading subscription: {e}")
        return {
            "success": False,
            "message": "Có lỗi xảy ra khi nâng cấp gói. Vui lòng thử lại."
        }
