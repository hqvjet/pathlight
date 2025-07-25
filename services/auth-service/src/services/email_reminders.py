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

logger = logging.getLogger(__name__)

def create_study_reminder_email_html(user_name: str = "") -> str:
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
    try:
        subject = "🕐 Đến giờ học rồi! - PathLight"
        html_body = create_study_reminder_email_html(user_name)
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = 'noreply@pathlight.com'
        msg['To'] = to_email
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            if config.SMTP_USERNAME and config.SMTP_PASSWORD:
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        return False


def get_users_to_remind(db: Session) -> List[User]:
    try:
        vietnam_time = datetime.now(timezone(timedelta(hours=7)))
        current_time_str = vietnam_time.strftime("%H:%M")
        
        users = db.query(User).filter(
            User.remind_time == current_time_str,
            User.is_email_verified == True,
            User.is_active == True,
            User.remind_time.isnot(None)
        ).all()
        return users
        
    except Exception as e:
        logger.error(f"Error getting users to remind: {str(e)}")
        return []

def send_reminders_to_users(db: Session):
    import threading
    vietnam_time = datetime.now(timezone(timedelta(hours=7)))
    now = vietnam_time.strftime("%H:%M")
    users = db.query(User).filter(
        User.remind_time == now,
        User.is_active == True,
        User.is_email_verified == True
    ).all()
    batch_size = 20
    threads = []
    results = []

    def send_batch(batch):
        try:
            if not config.SMTP_USERNAME or not config.SMTP_PASSWORD:
                return
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            for user in batch:
                user_email = getattr(user, 'email', None)
                if not user_email or not isinstance(user_email, str):
                    results.append((user_email, False))
                    continue
                given_name = getattr(user, 'given_name', None) or user_email or "bạn"
                subject = "🕐 Đến giờ học rồi! - PathLight"
                html_body = create_study_reminder_email_html(str(given_name))
                try:
                    msg = MIMEMultipart('alternative')
                    msg['From'] = "PathLight <noreply@pathlight.com>"
                    msg['To'] = user_email
                    msg['Subject'] = subject
                    msg['Message-ID'] = f"<{secrets.token_urlsafe(16)}@pathlight.com>"
                    msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
                    msg['X-Mailer'] = 'PathLight App'
                    plain_body = html_body.replace('<br>', '\n').replace('<p>', '').replace('</p>', '\n')
                    plain_body = plain_body.replace('<strong>', '').replace('</strong>', '')
                    plain_body = plain_body.replace('<a href="', '').replace('">', ' ').replace('</a>', '')
                    text_part = MIMEText(plain_body, 'plain', 'utf-8')
                    html_part = MIMEText(html_body, 'html', 'utf-8')
                    msg.attach(text_part)
                    msg.attach(html_part)
                    refused = server.sendmail('noreply@pathlight.com', [user_email], msg.as_string())
                    if refused:
                        logger.error(f"Some recipients were refused.")
                        results.append((user_email, False))
                    else:
                        results.append((user_email, True))
                except Exception as e:
                    logger.error(f"Error sending to user: {str(e)}")
                    results.append((user_email, False))
            server.quit()
        except Exception as e:
            logger.error(f"Batch SMTP error: {str(e)}")
            for user in batch:
                user_email = getattr(user, 'email', None)
                results.append((user_email, False))

    for i in range(0, len(users), batch_size):
        batch = users[i:i+batch_size]
        send_batch(batch)
    success_count = sum(1 for _, ok in results if ok)
    fail_count = sum(1 for _, ok in results if not ok)
    return f"Đã gửi nhắc nhở cho {success_count} user thành công, thất bại: {fail_count}"

def send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP with improved reliability"""
    try:
        if not config.SMTP_USERNAME or not config.SMTP_PASSWORD:
            logger.error("Email credentials not configured. Skipping email send.")
            return
        msg = MIMEMultipart('alternative')
        msg['From'] = "PathLight <noreply@pathlight.com>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Message-ID'] = f"<{secrets.token_urlsafe(16)}@pathlight.com>"
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        msg['X-Mailer'] = 'PathLight App'
        plain_body = body.replace('<br>', '\n').replace('<p>', '').replace('</p>', '\n')
        plain_body = plain_body.replace('<strong>', '').replace('</strong>', '')
        plain_body = plain_body.replace('<a href="', '').replace('">', ' ').replace('</a>', '')
        text_part = MIMEText(plain_body, 'plain', 'utf-8')
        html_part = MIMEText(body, 'html', 'utf-8')
        msg.attach(text_part)
        msg.attach(html_part)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
                server.starttls()
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                refused = server.sendmail('noreply@pathlight.com', [to_email], msg.as_string())
                if refused:
                    logger.error(f"Some recipients were refused: {refused}")
                else:
                    logger.info(f"Email sent successfully to {to_email}")
                server.quit()
                return
            except smtplib.SMTPException as smtp_error:
                logger.error(f"SMTP error on attempt {attempt + 1}: {str(smtp_error)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
            except Exception as conn_error:
                logger.error(f"Connection error on attempt {attempt + 1}: {str(conn_error)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
