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


def send_proposal_outcome_email(
    email: str,
    proposal_title: str,
    proposal_id: int,
    status: str,
    yes_votes: int,
    no_votes: int
) -> bool:
    """
    Send an email notification when a proposal is approved or rejected.
    
    Args:
        email: Recipient email address
        proposal_title: Title of the proposal
        proposal_id: ID of the proposal
        status: "approved" or "rejected"
        yes_votes: Number of yes votes
        no_votes: Number of no votes
    
    Returns:
        True if email was sent successfully, False otherwise
    """
    is_approved = status == "approved"
    subject = f"Proposal {'Approved' if is_approved else 'Rejected'}: {proposal_title}"
    
    status_text = "APPROVED" if is_approved else "REJECTED"
    status_color = "#19c37a" if is_approved else "#ef4444"
    status_message = "has been approved" if is_approved else "has been rejected"
    
    plain_message = f"""
A proposal you voted on has been finalized.

Proposal: {proposal_title}
Proposal ID: {proposal_id}
Status: {status_text}

Voting Results:
- Yes Votes: {yes_votes}
- No Votes: {no_votes}

The proposal {status_message} by the DAO community.

Thank you for participating in the governance process!

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
            background-color: {status_color};
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
        .proposal-info {{
            background-color: #e8f5e9;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }}
        .votes {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .vote-box {{
            flex: 1;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }}
        .vote-yes {{
            background-color: #d1fae5;
            color: #065f46;
        }}
        .vote-no {{
            background-color: #fee2e2;
            color: #991b1b;
        }}
        .vote-count {{
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
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
            <h1>Proposal {status_text}</h1>
        </div>
        <div class="content">
            <p>A proposal you voted on has been finalized.</p>
            
            <div class="proposal-info">
                <strong>Proposal:</strong> {proposal_title}<br>
                <strong>Proposal ID:</strong> #{proposal_id}<br>
                <strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
            </div>
            
            <h3>Voting Results:</h3>
            <div class="votes">
                <div class="vote-box vote-yes">
                    <div>Yes Votes</div>
                    <div class="vote-count">{yes_votes}</div>
                </div>
                <div class="vote-box vote-no">
                    <div>No Votes</div>
                    <div class="vote-count">{no_votes}</div>
                </div>
            </div>
            
            <p>The proposal <strong>{status_message}</strong> by the DAO community.</p>
            
            <p>Thank you for participating in the governance process!</p>
            
            <div class="footer">
                <p>Best regards,<br>The SmartBoard Team</p>
            </div>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    return send_email(email, subject, plain_message, html_message)

