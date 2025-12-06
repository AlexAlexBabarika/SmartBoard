#!/usr/bin/env python3
"""
Database cleaning utility script.

This script provides multiple options to clean the database:
1. Delete all records (soft clean) - keeps tables, removes data
2. Drop and recreate tables (hard clean) - drops and recreates tables
3. Delete database file (nuclear) - completely removes the database file

Usage:
    python clean_db.py [--mode soft|hard|nuclear] [--confirm]
    
Examples:
    python clean_db.py                    # Interactive mode
    python clean_db.py --mode soft        # Delete all records
    python clean_db.py --mode hard        # Drop and recreate tables
    python clean_db.py --mode nuclear     # Delete database file
    python clean_db.py --mode soft --confirm  # Skip confirmation
"""

import os
import sys
import argparse
from pathlib import Path
from sqlalchemy import text
from dotenv import load_dotenv

# Add parent directory to path to import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

from backend.app.db import engine, SessionLocal
from backend.app.models import Base, Proposal, Vote


def get_db_path():
    """Get the database file path."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///./proposals.db")
    if "sqlite" in database_url:
        # Extract path from sqlite:///./proposals.db or sqlite:///path/to/db
        if database_url.startswith("sqlite:///"):
            db_path = database_url.replace("sqlite:///", "")
            # Handle relative paths
            if db_path.startswith("./"):
                db_path = str(Path(__file__).parent.parent / db_path[2:])
            return db_path
    return None


def count_records():
    """Count records in each table."""
    db = SessionLocal()
    try:
        proposal_count = db.query(Proposal).count()
        vote_count = db.query(Vote).count()
        return proposal_count, vote_count
    finally:
        db.close()


def soft_clean():
    """Delete all records from tables (keeps table structure)."""
    print("🗑️  Soft clean: Deleting all records from tables...")
    db = SessionLocal()
    try:
        # Delete votes first (foreign key constraint)
        vote_count = db.query(Vote).count()
        db.query(Vote).delete()
        
        # Delete proposals
        proposal_count = db.query(Proposal).count()
        db.query(Proposal).delete()
        
        db.commit()
        print(f"✅ Deleted {proposal_count} proposals and {vote_count} votes")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during soft clean: {e}")
        raise
    finally:
        db.close()


def hard_clean():
    """Drop all tables and recreate them."""
    print("🔥 Hard clean: Dropping and recreating all tables...")
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("✅ Dropped all tables")
        
        # Recreate tables
        Base.metadata.create_all(bind=engine)
        print("✅ Recreated all tables")
    except Exception as e:
        print(f"❌ Error during hard clean: {e}")
        raise


def nuclear_clean():
    """Delete the database file entirely."""
    db_path = get_db_path()
    if not db_path:
        print("❌ Cannot determine database file path (not using SQLite?)")
        return
    
    db_path_obj = Path(db_path)
    if not db_path_obj.exists():
        print(f"ℹ️  Database file does not exist: {db_path}")
        return
    
    try:
        # Close any open connections
        engine.dispose()
        
        # Delete the file
        db_path_obj.unlink()
        print(f"✅ Deleted database file: {db_path}")
    except Exception as e:
        print(f"❌ Error deleting database file: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Clean the database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--mode",
        choices=["soft", "hard", "nuclear"],
        help="Cleaning mode: soft (delete records), hard (drop/recreate tables), nuclear (delete file)"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    # Show current database state
    try:
        proposal_count, vote_count = count_records()
        print(f"\n📊 Current database state:")
        print(f"   Proposals: {proposal_count}")
        print(f"   Votes: {vote_count}")
    except Exception as e:
        print(f"⚠️  Could not read database state: {e}")
        print("   (This might be okay if database doesn't exist yet)\n")
    
    # Interactive mode if no mode specified
    if not args.mode:
        print("\nSelect cleaning mode:")
        print("1. Soft clean - Delete all records (keeps tables)")
        print("2. Hard clean - Drop and recreate tables")
        print("3. Nuclear clean - Delete database file entirely")
        print("4. Cancel")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            mode = "soft"
        elif choice == "2":
            mode = "hard"
        elif choice == "3":
            mode = "nuclear"
        else:
            print("❌ Cancelled")
            return
    else:
        mode = args.mode
    
    # Confirmation
    if not args.confirm:
        if mode == "nuclear":
            print(f"\n⚠️  WARNING: This will DELETE the entire database file!")
            confirm = input("Are you sure? Type 'yes' to confirm: ").strip().lower()
        else:
            confirm = input(f"\n⚠️  Are you sure you want to perform {mode} clean? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("❌ Cancelled")
            return
    
    # Perform the cleaning
    print()
    try:
        if mode == "soft":
            soft_clean()
        elif mode == "hard":
            hard_clean()
        elif mode == "nuclear":
            nuclear_clean()
        
        print("\n✅ Database cleaning completed successfully!")
        
        # Show final state
        try:
            if mode != "nuclear":
                proposal_count, vote_count = count_records()
                print(f"\n📊 Final database state:")
                print(f"   Proposals: {proposal_count}")
                print(f"   Votes: {vote_count}")
        except Exception:
            pass  # Database might not exist after nuclear clean
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

