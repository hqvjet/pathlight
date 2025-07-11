"""
Study Reminder Email System for PathLight Auth Service
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
import secrets
import time

from src.models import User
from src.config import config

# Configure logging
logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = config.SMTP_SERVER
SMTP_PORT = config.SMTP_PORT
SMTP_USERNAME = config.SMTP_USERNAME
SMTP_PASSWORD = config.SMTP_PASSWORD
FROM_EMAIL = config.FROM_EMAIL


def create_study_reminder_email_html(user_name: str = "") -> str:
    """Create HTML content for study reminder email"""
    
    display_name = user_name if user_name else "bạn"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; padding: 0; background-color: #f7f7f7; 
            }}
            .container {{ 
                max-width: 600px; margin: 0 auto; background-color: white; 
                border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{ 
                background: linear-gradient(135deg, #f97316 0%, #dc2626 100%); 
                padding: 30px; text-align: center; 
            }}
            .header h1 {{ 
                color: white; margin: 0; font-size: 28px; 
            }}
            .content {{ 
                padding: 40px 30px; 
            }}
            .reminder-box {{ 
                background: linear-gradient(135deg, #fef3c7 0%, #fed7aa 100%); 
                border-radius: 12px; padding: 25px; margin: 20px 0; text-align: center; 
                border: 2px solid #f59e0b;
            }}
            .reminder-box h2 {{ 
                color: #92400e; margin-top: 0; font-size: 24px; 
            }}
            .reminder-box p {{ 
                color: #78350f; font-size: 16px; line-height: 1.6; margin: 10px 0;
            }}
            .cta-button {{ 
                display: inline-block; 
                background: linear-gradient(135deg, #f97316 0%, #dc2626 100%); 
                color: white; padding: 15px 30px; text-decoration: none; 
                border-radius: 8px; font-weight: bold; font-size: 16px; 
                margin: 20px 0; transition: transform 0.2s;
            }}
            .cta-button:hover {{
                transform: translateY(-2px);
            }}
            .features {{ 
                display: grid; grid-template-columns: 1fr 1fr; gap: 15px; 
                margin: 25px 0; 
            }}
            .feature {{ 
                background: #f8fafc; padding: 20px; border-radius: 8px; 
                text-align: center; border: 1px solid #e2e8f0;
            }}
            .feature-icon {{ 
                font-size: 32px; margin-bottom: 10px; 
            }}
            .tips-box {{
                background: #e0f2fe; padding: 20px; border-radius: 8px; 
                margin: 20px 0; border-left: 4px solid #0277bd;
            }}
            .footer {{ 
                background: #f1f5f9; padding: 20px; text-align: center; 
                color: #64748b; font-size: 14px; 
            }}
            .footer a {{
                color: #f97316; text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 PathLight</h1>
            </div>
            
            <div class="content">
                <div class="reminder-box">
                    <h2>⏰ Đến giờ học rồi!</h2>
                    <p>Chào <strong>{display_name}</strong>! Đây là thời gian bạn đã đặt để học tập hôm nay.</p>
                    <p><strong>🌟 Hãy dành chút thời gian để nâng cao kiến thức của mình nhé!</strong></p>
                </div>
                
                <p style="font-size: 18px; color: #374151; margin: 25px 0;">
                    <strong>🚀 Tại sao nên học đều đặn?</strong>
                </p>
                
                <div class="features">
                    <div class="feature">
                        <div class="feature-icon">🧠</div>
                        <strong>Tăng trí nhớ</strong><br>
                        <small>Học đều đặn giúp não bộ ghi nhớ tốt hơn</small>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">📈</div>
                        <strong>Tiến bộ nhanh</strong><br>
                        <small>Kiến thức tích lũy từng ngày một</small>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">🎯</div>
                        <strong>Đạt mục tiêu</strong><br>
                        <small>Thành công đến từ sự kiên trì</small>
                    </div>
                    <div class="feature">
                        <div class="feature-icon">💪</div>
                        <strong>Xây dựng thói quen</strong><br>
                        <small>Tạo dựng kỷ luật tự giác</small>
                    </div>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://pathlight.vn/dashboard" class="cta-button">
                        🚀 Bắt Đầu Học Ngay
                    </a>
                </div>
                
                <div class="tips-box">
                    <p style="margin: 0; color: #0277bd; font-weight: bold;">💡 Mẹo học hiệu quả:</p>
                    <ul style="color: #0277bd; margin: 10px 0; padding-left: 20px;">
                        <li>Học trong 25-30 phút, nghỉ 5 phút (Kỹ thuật Pomodoro)</li>
                        <li>Tìm không gian yên tĩnh, tập trung cao độ</li>
                        <li>Ghi chú những điểm quan trọng</li>
                        <li>Ôn tập lại kiến thức đã học</li>
                    </ul>
                </div>
                
                <p style="text-align: center; font-size: 16px; color: #059669; font-weight: bold;">
                    🌟 Chúc bạn có buổi học thật hiệu quả!
                </p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">
                
                <p style="font-size: 13px; color: #64748b; text-align: center;">
                    📧 Bạn nhận được email này vì đã đăng ký nhắc nhở học tập trên PathLight.<br>
                    <a href="https://pathlight.vn/settings">Thay đổi thời gian nhắc nhở</a> | 
                    <a href="https://pathlight.vn/settings">Hủy nhắc nhở</a>
                </p>
            </div>
            
            <div class="footer">
                <p><strong>© 2025 PathLight</strong> - Nền tảng học tập trực tuyến hàng đầu Việt Nam</p>
                <p>🌐 <a href="https://pathlight.vn">pathlight.vn</a> | 📞 Hotline: 1900-XXX-XXX</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content


def send_study_reminder_email(to_email: str, user_name: str = "") -> bool:
    """Send study reminder email to user"""
    try:
        # Create email content
        subject = "🕐 Đến giờ học rồi! - PathLight"
        html_body = create_study_reminder_email_html(user_name)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        
        # Add HTML part
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Study reminder email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send study reminder email to {to_email}: {str(e)}")
        return False


def get_users_to_remind(db: Session) -> List[User]:
    """Get users who should receive reminder emails at current time"""
    try:
        # Get current time in Vietnam timezone (UTC+7)
        vietnam_time = datetime.now(timezone(timedelta(hours=7)))
        current_time_str = vietnam_time.strftime("%H:%M")
        
        # Find users who have set remind_time and should be reminded now
        users = db.query(User).filter(
            User.remind_time == current_time_str,
            User.is_email_verified == True,
            User.is_active == True,
            User.remind_time.isnot(None)
        ).all()
        
        logger.info(f"Found {len(users)} users to remind at {current_time_str} (Vietnam time)")
        return users
        
    except Exception as e:
        logger.error(f"Error getting users to remind: {str(e)}")
        return []


# --- remind_time ---
def send_reminders_to_users(db: Session):
    vietnam_time = datetime.now(timezone(timedelta(hours=7)))
    now = vietnam_time.strftime("%H:%M")
    all_users = db.query(User).filter(User.remind_time.isnot(None)).all()
    for u in all_users:
        logger.info(f"[REMINDER DEBUG] User: email={getattr(u, 'email', None)}, remind_time={getattr(u, 'remind_time', None)}, is_active={getattr(u, 'is_active', None)}, is_email_verified={getattr(u, 'is_email_verified', None)}")
    users = db.query(User).filter(
        User.remind_time == now,
        User.is_active == True,
        User.is_email_verified == True
    ).all()
    for user in users:
        logger.info(f"[REMINDER DEBUG] Sẽ gửi cho: email={getattr(user, 'email', None)}, remind_time={getattr(user, 'remind_time', None)}")
    count = 0
    for user in users:
        user_email = getattr(user, 'email', None)
        given_name = getattr(user, 'given_name', None)
        if not given_name:
            given_name = user_email or "bạn"
        remind_time = getattr(user, 'remind_time', now)
        subject = "🕐 Đến giờ học rồi! - PathLight"
        html_body = create_study_reminder_email_html(str(given_name))
        send_email(
            str(user_email),
            subject,
            html_body
        )
        count += 1
    return f"Đã gửi nhắc nhở cho {count} user tại {now}"


def send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP with improved reliability"""
    try:
        logger.info(f"🔍 DEBUG: Attempting to send email to {to_email}")
        logger.info(f"🔍 DEBUG: SMTP_USERNAME={SMTP_USERNAME}")
        logger.info(f"🔍 DEBUG: SMTP_PASSWORD={'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'EMPTY'}")
        logger.info(f"🔍 DEBUG: FROM_EMAIL={FROM_EMAIL}")
        logger.info(f"🔍 DEBUG: SMTP_SERVER={SMTP_SERVER}:{SMTP_PORT}")
        
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("Email credentials not configured. Skipping email send.")
            return
            
        logger.info(f"📧 Creating email message...")
        msg = MIMEMultipart('alternative')
        msg['From'] = f"PathLight <{FROM_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Message-ID'] = f"<{secrets.token_urlsafe(16)}@pathlight.com>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['X-Mailer'] = 'PathLight App'
        
        # Add both HTML and plain text versions
        plain_body = body.replace('<br>', '\n').replace('<p>', '').replace('</p>', '\n')
        plain_body = plain_body.replace('<strong>', '').replace('</strong>', '')
        plain_body = plain_body.replace('<a href="', '').replace('">', ' ').replace('</a>', '')
        
        text_part = MIMEText(plain_body, 'plain', 'utf-8')
        html_part = MIMEText(body, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Try sending with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"📡 Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT} (attempt {attempt + 1}/{max_retries})...")
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
                
                logger.info(f"🔒 Starting TLS...")
                server.starttls()
                
                logger.info(f"🔑 Logging in...")
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                
                logger.info(f"📤 Sending email...")
                refused = server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
                
                if refused:
                    logger.warning(f"⚠️ Some recipients were refused: {refused}")
                else:
                    logger.info(f"✅ Email sent successfully to {to_email}")
                
                server.quit()
                return  # Success, exit retry loop
                
            except smtplib.SMTPException as smtp_error:
                logger.error(f"❌ SMTP error on attempt {attempt + 1}: {str(smtp_error)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as conn_error:
                logger.error(f"❌ Connection error on attempt {attempt + 1}: {str(conn_error)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
                
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
        import traceback
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        print(f"Lỗi không gửi email đến {to_email}: {str(e)}")
