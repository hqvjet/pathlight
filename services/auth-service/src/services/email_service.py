import smtplib
import secrets
import time
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import config

logger = logging.getLogger(__name__)

from config import config

def send_email(to_email: str, subject: str, body: str):
    """Send email using SMTP with improved reliability"""
    try:
        if not config.SMTP_USERNAME or not config.SMTP_PASSWORD:
            logger.error("Email credentials not configured. Skipping email send.")
            logger.error(f"SMTP_USERNAME: {'SET' if config.SMTP_USERNAME else 'NOT SET'}")
            logger.error(f"SMTP_PASSWORD: {'SET' if config.SMTP_PASSWORD else 'NOT SET'}")
            return False
            
        logger.info(f"Attempting to send email to {to_email}")
        logger.info(f"Using SMTP server: smtp.gmail.com:587")
        logger.info(f"From: {config.SMTP_USERNAME}")
        
        msg = MIMEMultipart('alternative')
        msg['From'] = f"PathLight <{config.SMTP_USERNAME}>"
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
                logger.info(f"Connection attempt {attempt + 1}/{max_retries}")
                server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
                server.set_debuglevel(0)
                logger.info("Starting TLS...")
                server.starttls()
                logger.info("Logging in...")
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                logger.info("Sending email...")
                refused = server.sendmail(config.SMTP_USERNAME, [to_email], msg.as_string())
                if refused:
                    logger.error(f"Some recipients were refused: {refused}")
                else:
                    logger.info(f"✅ Email sent successfully to {to_email}")
                server.quit()
                return True
            except smtplib.SMTPAuthenticationError as auth_error:
                logger.error(f"❌ SMTP Authentication failed: {str(auth_error)}")
                logger.error("Check SMTP credentials. For Gmail, use App Password instead of regular password.")
                logger.error("Generate App Password at: https://myaccount.google.com/apppasswords")
                return False
            except smtplib.SMTPException as smtp_error:
                logger.error(f"SMTP error on attempt {attempt + 1}: {str(smtp_error)}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Failed to send email after {max_retries} attempts")
                    return False
                time.sleep(2 ** attempt)
            except Exception as conn_error:
                logger.error(f"Connection error on attempt {attempt + 1}: {str(conn_error)}")
                if attempt == max_retries - 1:
                    logger.error(f"❌ Failed to send email after {max_retries} attempts")
                    return False
                time.sleep(2 ** attempt)
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def send_verification_email(email: str, token: str, expire_minutes: int):
    """Send email verification email"""
    try:
        frontend_base = config.FRONTEND_URL
        verification_link = f"{frontend_base}/auth/verify-email?token={token}"
        
        logger.info(f"Preparing verification email for {email}")
        logger.info(f"Verification link: {verification_link}")
        
        email_body = f"""
        <html>
        <body>
            <h2>Xác thực tài khoản PathLight</h2>
            <p>Chào bạn,</p>
            <p>Cảm ơn bạn đã đăng ký tài khoản tại PathLight!</p>
            <p>Vui lòng click vào nút dưới đây để xác thực tài khoản của bạn:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{verification_link}" style="background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Xác thực tài khoản</a>
            </p>
            <p>Hoặc copy và paste link sau vào trình duyệt:</p>
            <p style="word-break: break-all; color: #666;">{verification_link}</p>
            <p style="color: #999; font-size: 12px;">Link này sẽ hết hạn sau {expire_minutes} phút.</p>
        </body>
        </html>
        """
        
        success = send_email(email, "Xác thực tài khoản PathLight", email_body)
        if success:
            logger.info(f"✅ Verification email sent to {email}")
        else:
            logger.error(f"❌ Failed to send verification email to {email}")
        return success
    except Exception as e:
        logger.error(f"Error in send_verification_email: {str(e)}")
        return False

def send_password_reset_email(email: str, token: str):
    """Send password reset email"""
    try:
        frontend_base = config.FRONTEND_URL
        reset_link = f"{frontend_base}/auth/reset-password/{token}"
        
        logger.info(f"Preparing password reset email for {email}")
        logger.info(f"Reset link: {reset_link}")
        
        email_body = f"""
        <html>
        <body>
            <h2>Đặt lại mật khẩu PathLight</h2>
            <p>Chào bạn,</p>
            <p>Bạn đã yêu cầu đặt lại mật khẩu cho tài khoản PathLight của mình.</p>
            <p>Vui lòng click vào nút dưới đây để đặt lại mật khẩu:</p>
            <p style="text-align: center; margin: 30px 0;">
                <a href="{reset_link}" style="background-color: #ff6b35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Đặt lại mật khẩu</a>
            </p>
            <p>Hoặc copy và paste link sau vào trình duyệt:</p>
            <p style="word-break: break-all; color: #666;">{reset_link}</p>
            <p style="color: #999; font-size: 12px;">Link này sẽ hết hạn sau 15 phút.</p>
            <p style="color: #999; font-size: 12px;">Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.</p>
        </body>
        </html>
        """
        
        success = send_email(email, "Đặt lại mật khẩu PathLight", email_body)
        if success:
            logger.info(f"✅ Password reset email sent to {email}")
        else:
            logger.error(f"❌ Failed to send password reset email to {email}")
        return success
    except Exception as e:
        logger.error(f"Error in send_password_reset_email: {str(e)}")
        return False
