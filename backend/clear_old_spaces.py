#!/usr/bin/env python3
"""
Utility script to clear proposals from old Storacha spaces.

Usage:
    python backend/clear_old_spaces.py                    # List all spaces
    python backend/clear_old_spaces.py --delete <space>   # Delete proposals from a space
    python backend/clear_old_spaces.py --delete-all-old    # Delete all proposals from non-current spaces
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from backend.app.db import SessionLocal
from backend.app.models import Proposal
from backend.app.utils import get_current_storacha_space

# Load environment variables
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


def list_spaces():
    """List all Storacha spaces that have proposals."""
    db = SessionLocal()
    try:
        all_proposals = db.query(Proposal).all()
        spaces = {}
        no_space_count = 0
        
        for proposal in all_proposals:
            meta = proposal.proposal_metadata or {}
            space = meta.get("storacha_space")
            if space:
                spaces[space] = spaces.get(space, 0) + 1
            else:
                no_space_count += 1
        
        current_space = get_current_storacha_space()
        
        print("\n" + "=" * 60)
        print("STORACHA SPACES WITH PROPOSALS")
        print("=" * 60)
        print(f"\nCurrent active space: {current_space or 'NOT SET'}")
        print(f"\nTotal proposals in database: {len(all_proposals)}")
        print(f"\nProposals by space:")
        
        if spaces:
            for space, count in sorted(spaces.items()):
                marker = " ← CURRENT" if space == current_space else ""
                print(f"  • {space}: {count} proposals{marker}")
        else:
            print("  (No proposals with space tags)")
        
        if no_space_count > 0:
            print(f"\n  • (no space tag): {no_space_count} proposals (legacy)")
        
        print("\n" + "=" * 60)
        
        return spaces, current_space, no_space_count
        
    finally:
        db.close()


def delete_space_proposals(space_name: str, confirm: bool = True):
    """Delete all proposals from a specific space."""
    db = SessionLocal()
    try:
        current_space = get_current_storacha_space()
        
        if space_name == current_space:
            print(f"\n❌ ERROR: Cannot delete proposals from current active space: {space_name}")
            print(f"   Switch to a different space first: storacha space use <other-space>")
            return False
        
        # Find proposals from the specified space
        all_proposals = db.query(Proposal).all()
        to_delete = []
        for proposal in all_proposals:
            meta = proposal.proposal_metadata or {}
            if meta.get("storacha_space") == space_name:
                to_delete.append(proposal)
        
        count = len(to_delete)
        if count == 0:
            print(f"\n✓ No proposals found for space: {space_name}")
            return True
        
        if confirm:
            print(f"\n⚠️  WARNING: This will permanently delete {count} proposals from space: {space_name}")
            response = input("   Are you sure? Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                print("   Cancelled.")
                return False
        
        # Delete proposals
        for proposal in to_delete:
            db.delete(proposal)
        db.commit()
        
        print(f"\n✓ Successfully deleted {count} proposals from space: {space_name}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: Failed to delete proposals: {e}")
        return False
    finally:
        db.close()


def delete_all_old_spaces(confirm: bool = True):
    """Delete proposals from all spaces except the current one."""
    spaces, current_space, no_space_count = list_spaces()
    
    if not spaces:
        print("\n✓ No spaces with proposals found.")
        return True
    
    old_spaces = [s for s in spaces.keys() if s != current_space]
    
    if not old_spaces:
        print(f"\n✓ No old spaces found. All proposals are in current space: {current_space}")
        return True
    
    total_to_delete = sum(spaces[s] for s in old_spaces)
    
    if confirm:
        print(f"\n⚠️  WARNING: This will permanently delete proposals from {len(old_spaces)} old space(s):")
        for space in old_spaces:
            print(f"   • {space}: {spaces[space]} proposals")
        print(f"\n   Total: {total_to_delete} proposals will be deleted")
        response = input("   Are you sure? Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("   Cancelled.")
            return False
    
    success = True
    for space in old_spaces:
        if not delete_space_proposals(space, confirm=False):
            success = False
    
    if success:
        print(f"\n✓ Successfully deleted all proposals from old spaces")
    
    return success


def delete_legacy_proposals(confirm: bool = True):
    """Delete all proposals without space tags (legacy proposals)."""
    db = SessionLocal()
    try:
        all_proposals = db.query(Proposal).all()
        to_delete = []
        
        for proposal in all_proposals:
            meta = proposal.proposal_metadata or {}
            if not meta.get("storacha_space"):
                to_delete.append(proposal)
        
        count = len(to_delete)
        if count == 0:
            print("\n✓ No legacy proposals found (all proposals have space tags)")
            return True
        
        if confirm:
            print(f"\n⚠️  WARNING: This will permanently delete {count} legacy proposals (no space tags)")
            print("   These are proposals created before space tracking was implemented.")
            response = input("   Are you sure? Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                print("   Cancelled.")
                return False
        
        # Delete proposals
        for proposal in to_delete:
            db.delete(proposal)
        db.commit()
        
        print(f"\n✓ Successfully deleted {count} legacy proposals")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: Failed to delete legacy proposals: {e}")
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Manage Storacha space proposals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python backend/clear_old_spaces.py                    # List all spaces
  python backend/clear_old_spaces.py --delete old-space # Delete proposals from 'old-space'
  python backend/clear_old_spaces.py --delete-all-old   # Delete all old space proposals
        """
    )
    parser.add_argument(
        "--delete",
        type=str,
        metavar="SPACE",
        help="Delete proposals from a specific space"
    )
    parser.add_argument(
        "--delete-all-old",
        action="store_true",
        help="Delete proposals from all spaces except the current one"
    )
    parser.add_argument(
        "--delete-legacy",
        action="store_true",
        help="Delete all legacy proposals (those without space tags)"
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompts (use with caution!)"
    )
    
    args = parser.parse_args()
    
    if args.delete:
        delete_space_proposals(args.delete, confirm=not args.no_confirm)
    elif args.delete_all_old:
        delete_all_old_spaces(confirm=not args.no_confirm)
    elif args.delete_legacy:
        delete_legacy_proposals(confirm=not args.no_confirm)
    else:
        list_spaces()


if __name__ == "__main__":
    main()

