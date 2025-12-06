"""
Email service for sending notifications to users.
Uses SMTP to send emails when users add their email addresses.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

# Email configuration from environment variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USERNAME)
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "SmartBoard Team")


def send_email(
    to_email: str,
    subject: str,
    message: str,
    html_message: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP.
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        message: Plain text message body
        html_message: Optional HTML message body
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    # Check if email is configured
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning(
            "Email not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables. "
            "Skipping email send."
        )
        return False
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
        msg["To"] = to_email
        
        # Add plain text part
        text_part = MIMEText(message, "plain")
        msg.attach(text_part)
        
        # Add HTML part if provided
        if html_message:
            html_part = MIMEText(html_message, "html")
            msg.attach(html_part)
        
        # Connect to SMTP server and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending email to {to_email}: {str(e)}")
        return False


def send_congratulations_email(wallet_address: str, email: str) -> bool:
    """
    Send a congratulations email when a user adds their email.
    
    Args:
        wallet_address: User's wallet address
        email: User's email address
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    subject = "Welcome to SmartBoard - Your Wallet is Connected!"
    
    plain_message = f"""
Congratulations! You've successfully connected your wallet to SmartBoard.

Wallet Address: {wallet_address}

You'll now receive notifications about important updates, new proposals, and voting deadlines.

Thank you for joining the AI Investment Scout DAO!

Best regards,
The SmartBoard Team
    """.strip()
    
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #19c37a;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 0 0 8px 8px;
        }}
        .wallet-address {{
            background-color: #e8f5e9;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            word-break: break-all;
            margin: 15px 0;
        }}
        .footer {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to SmartBoard!</h1>
        </div>
        <div class="content">
            <p>Congratulations! You've successfully connected your wallet to SmartBoard.</p>
            
            <div class="wallet-address">
                <strong>Wallet Address:</strong><br>
                {wallet_address}
            </div>
            
            <p>You'll now receive notifications about:</p>
            <ul>
                <li>Important updates</li>
                <li>New proposals</li>
                <li>Voting deadlines</li>
            </ul>
            
            <p>Thank you for joining the AI Investment Scout DAO!</p>
            
            <div class="footer">
                <p>Best regards,<br>The SmartBoard Team</p>
            </div>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    return send_email(email, subject, plain_message, html_message)

