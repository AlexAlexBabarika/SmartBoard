#!/usr/bin/env python3
"""
Standalone script to send a congratulations email to a user.
Can be run directly or imported as a module.

Usage:
    python send_congratulations_email.py <wallet_address> <email>
    
Or as a module:
    from send_congratulations_email import send_congratulations_email
    send_congratulations_email("N...", "user@example.com")
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import from app
sys.path.insert(0, str(Path(__file__).parent))

from app.email_service import send_congratulations_email


def main():
    """Main function to run the script from command line."""
    if len(sys.argv) != 3:
        print("Usage: python send_congratulations_email.py <wallet_address> <email>")
        print("\nExample:")
        print("  python send_congratulations_email.py Nabc123... user@example.com")
        sys.exit(1)
    
    wallet_address = sys.argv[1]
    email = sys.argv[2]
    
    print(f"Sending congratulations email to {email} for wallet {wallet_address}...")
    
    success = send_congratulations_email(wallet_address, email)
    
    if success:
        print("✅ Email sent successfully!")
        sys.exit(0)
    else:
        print("❌ Failed to send email. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()

