"""
SMTP and Email Service Tests

Tests for email functionality including SMTP connection, 
email sending, verification emails, and password reset emails.
"""
import pytest
import smtplib
from unittest.mock import patch, MagicMock, call
from email.mime.multipart import MIMEMultipart


class TestEmailService:
    """Test suite for email service functionality"""

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp_class, mock_config, mock_smtp_server):
        """Test successful email sending"""
        # Setup
        mock_smtp_class.return_value = mock_smtp_server
        
        with patch('services.email_service.config', mock_config):
            from services.email_service import send_email
            
            # Execute
            send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body="<p>Test body</p>"
            )
            
            # Verify
            mock_smtp_class.assert_called_once_with('smtp.gmail.com', 587, timeout=30)
            mock_smtp_server.starttls.assert_called_once()
            mock_smtp_server.login.assert_called_once_with(
                mock_config.SMTP_USERNAME, 
                mock_config.SMTP_PASSWORD
            )
            mock_smtp_server.sendmail.assert_called_once()
            mock_smtp_server.quit.assert_called_once()

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_missing_credentials(self, mock_smtp_class, mock_config):
        """Test email sending with missing credentials"""
        # Setup
        mock_config.SMTP_USERNAME = None
        mock_config.SMTP_PASSWORD = None
        
        with patch('services.email_service.config', mock_config):
            from services.email_service import send_email
            
            # Execute
            send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body="Test body"
            )
            
            # Verify - SMTP should not be called
            mock_smtp_class.assert_not_called()

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_smtp_exception_retry(self, mock_smtp_class, mock_config):
        """Test email sending with SMTP exception and retry logic"""
        # Setup
        mock_server = MagicMock()
        mock_server.starttls.side_effect = smtplib.SMTPException("Connection failed")
        mock_smtp_class.return_value = mock_server
        
        with patch('services.email_service.config', mock_config):
            with patch('services.email_service.time.sleep'):  # Speed up test
                from services.email_service import send_email
                
                # Execute - should not raise exception due to error handling
                send_email(
                    to_email="test@example.com",
                    subject="Test Subject",
                    body="Test body"
                )
                
                # Verify retry attempts (should try 3 times)
                assert mock_smtp_class.call_count == 3

    @patch('services.email_service.smtplib.SMTP')
    def test_send_email_connection_timeout(self, mock_smtp_class, mock_config):
        """Test email sending with connection timeout"""
        # Setup
        mock_smtp_class.side_effect = ConnectionError("Connection timeout")
        
        with patch('services.email_service.config', mock_config):
            with patch('services.email_service.time.sleep'):  # Speed up test
                from services.email_service import send_email
                
                # Execute - should not raise exception
                send_email(
                    to_email="test@example.com",
                    subject="Test Subject", 
                    body="Test body"
                )
                
                # Verify retry attempts
                assert mock_smtp_class.call_count == 3

    @patch('services.email_service.send_email')
    def test_send_verification_email(self, mock_send_email, mock_config):
        """Test verification email content and formatting"""
        with patch('services.email_service.config', mock_config):
            from services.email_service import send_verification_email
            
            # Execute
            send_verification_email(
                email="user@example.com",
                token="test_token_123",
                expire_minutes=10
            )
            
            # Verify
            mock_send_email.assert_called_once()
            args, kwargs = mock_send_email.call_args
            
            assert args[0] == "user@example.com"
            assert args[1] == "Xác thực tài khoản PathLight"
            assert "test_token_123" in args[2]
            assert "http://localhost:3000/auth/verify-email?token=test_token_123" in args[2]
            assert "10 phút" in args[2]

    @patch('services.email_service.send_email')
    def test_send_password_reset_email(self, mock_send_email, mock_config):
        """Test password reset email content and formatting"""
        with patch('services.email_service.config', mock_config):
            from services.email_service import send_password_reset_email
            
            # Execute
            send_password_reset_email(
                email="user@example.com",
                token="reset_token_456"
            )
            
            # Verify
            mock_send_email.assert_called_once()
            args, kwargs = mock_send_email.call_args
            
            assert args[0] == "user@example.com"
            assert args[1] == "Đặt lại mật khẩu PathLight"
            assert "reset_token_456" in args[2]
            assert "http://localhost:3000/auth/reset-password/reset_token_456" in args[2]
            assert "15 phút" in args[2]

    def test_email_html_content_structure(self, mock_config):
        """Test that emails contain proper HTML structure"""
        with patch('services.email_service.config', mock_config):
            with patch('services.email_service.send_email') as mock_send:
                from services.email_service import send_verification_email
                
                send_verification_email("test@example.com", "token123", 10)
                
                args, kwargs = mock_send.call_args
                html_content = args[2]
                
                # Check HTML structure
                assert "<html>" in html_content
                assert "<body>" in html_content
                assert "<h2>" in html_content
                assert "</html>" in html_content
                assert "</body>" in html_content

    @patch('services.email_service.smtplib.SMTP')
    def test_email_message_format(self, mock_smtp_class, mock_config, mock_smtp_server):
        """Test that email message is properly formatted"""
        mock_smtp_class.return_value = mock_smtp_server
        
        with patch('services.email_service.config', mock_config):
            from services.email_service import send_email
            
            send_email(
                to_email="test@example.com",
                subject="Test Subject",
                body="<p>HTML content</p>"
            )
            
            # Get the message that was sent
            sendmail_call = mock_smtp_server.sendmail.call_args
            message_content = sendmail_call[0][2]  # Third argument is the message
            
            # Verify message contains both plain text and HTML parts
            assert "Content-Type: text/plain" in message_content
            assert "Content-Type: text/html" in message_content
            assert "PathLight <noreply@pathlight.com>" in message_content
            assert "Subject: Test Subject" in message_content

    @patch('services.email_service.smtplib.SMTP')
    def test_smtp_security_settings(self, mock_smtp_class, mock_config, mock_smtp_server):
        """Test that SMTP uses secure connection settings"""
        mock_smtp_class.return_value = mock_smtp_server
        
        with patch('services.email_service.config', mock_config):
            from services.email_service import send_email
            
            send_email("test@example.com", "Test", "Body")
            
            # Verify secure connection
            mock_smtp_class.assert_called_with('smtp.gmail.com', 587, timeout=30)
            mock_smtp_server.starttls.assert_called_once()  # TLS encryption
