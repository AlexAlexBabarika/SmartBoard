#!/usr/bin/env python3
"""
Setup Verification Script for AI Investment Scout DAO
Checks if all dependencies and components are properly configured.
"""

import sys
import subprocess
import os
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    """Print success message."""
    print(f"✅ {text}")

def print_error(text):
    """Print error message."""
    print(f"❌ {text}")

def print_warning(text):
    """Print warning message."""
    print(f"⚠️  {text}")

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (requires 3.10+)")
        return False

def check_python_package(package_name):
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        print_success(f"{package_name}")
        return True
    except ImportError:
        print_error(f"{package_name} not installed")
        return False

def check_node():
    """Check Node.js installation."""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print_success(f"Node.js {version}")
        return True
    except FileNotFoundError:
        print_error("Node.js not installed")
        return False

def check_npm():
    """Check npm installation."""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        version = result.stdout.strip()
        print_success(f"npm {version}")
        return True
    except FileNotFoundError:
        print_error("npm not installed")
        return False

def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print_success(f"{description}: {filepath}")
        return True
    else:
        print_error(f"{description} not found: {filepath}")
        return False

def check_directory_exists(dirpath, description):
    """Check if a directory exists."""
    if Path(dirpath).is_dir():
        print_success(f"{description}: {dirpath}")
        return True
    else:
        print_error(f"{description} not found: {dirpath}")
        return False

def check_env_file():
    """Check environment file."""
    if Path('.env').exists():
        print_success(".env file exists")
        return True
    else:
        print_warning(".env file not found (demo mode will be used)")
        print("   Create .env from ENV_TEMPLATE.txt for full functionality")
        return False

def main():
    """Main verification function."""
    print_header("AI Investment Scout DAO - Setup Verification")
    
    issues = []
    
    # Check Python version
    print_header("1. Python Environment")
    if not check_python_version():
        issues.append("Python version too old")
    
    # Check Python packages
    print("\nRequired Python packages:")
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'requests',
        'jinja2',
        'pytest',
        'dotenv'
    ]
    
    for package in required_packages:
        if not check_python_package(package):
            issues.append(f"Missing Python package: {package}")
    
    # Check optional Python packages
    print("\nOptional Python packages:")
    optional_packages = {
        'weasyprint': 'PDF generation',
        'neo': 'NEO blockchain (neo-mamba)',
        'boa3': 'Smart contract compilation (neo3-boa)'
    }
    
    for package, description in optional_packages.items():
        try:
            __import__(package)
            print_success(f"{package} ({description})")
        except ImportError:
            print_warning(f"{package} not installed ({description})")
    
    # Check Node.js and npm
    print_header("2. Node.js Environment")
    if not check_node():
        issues.append("Node.js not installed")
    if not check_npm():
        issues.append("npm not installed")
    
    # Check project structure
    print_header("3. Project Structure")
    
    directories = [
        ('backend', 'Backend directory'),
        ('backend/app', 'Backend app directory'),
        ('backend/tests', 'Backend tests'),
        ('spoon_agent', 'SpoonOS agent directory'),
        ('spoon_agent/tests', 'Agent tests'),
        ('contracts', 'Contracts directory'),
        ('contracts/tests', 'Contract tests'),
        ('frontend', 'Frontend directory'),
        ('frontend/src', 'Frontend source')
    ]
    
    for dirpath, description in directories:
        if not check_directory_exists(dirpath, description):
            issues.append(f"Missing directory: {dirpath}")
    
    # Check key files
    print("\nKey files:")
    files = [
        ('requirements.txt', 'Python dependencies'),
        ('backend/app/main.py', 'Backend main file'),
        ('spoon_agent/main.py', 'Agent main file'),
        ('contracts/proposal_contract.py', 'Smart contract'),
        ('frontend/package.json', 'Frontend dependencies'),
        ('README.md', 'Documentation'),
        ('QUICKSTART.md', 'Quick start guide')
    ]
    
    for filepath, description in files:
        if not check_file_exists(filepath, description):
            issues.append(f"Missing file: {filepath}")
    
    # Check environment configuration
    print_header("4. Configuration")
    check_env_file()
    
    # Check if frontend dependencies are installed
    if Path('frontend/node_modules').exists():
        print_success("Frontend dependencies installed")
    else:
        print_warning("Frontend dependencies not installed")
        print("   Run: cd frontend && npm install")
    
    # Final summary
    print_header("Summary")
    
    if not issues:
        print_success("All checks passed! ✨")
        print("\n🚀 You're ready to start!")
        print("\nNext steps:")
        print("1. Create .env from ENV_TEMPLATE.txt (optional for demo)")
        print("2. Start backend: cd backend && uvicorn app.main:app --reload")
        print("3. Start frontend: cd frontend && npm run dev")
        print("4. Run agent demo: python spoon_agent/main.py --demo")
        print("\nSee QUICKSTART.md for detailed instructions.")
        return 0
    else:
        print_error(f"Found {len(issues)} issue(s):")
        for issue in issues:
            print(f"  • {issue}")
        print("\n🔧 Fix the issues above and run this script again.")
        print("\nFor help, see:")
        print("  • README.md - Full documentation")
        print("  • QUICKSTART.md - Quick start guide")
        print("  • ENV_TEMPLATE.txt - Environment variables template")
        return 1

if __name__ == '__main__':
    sys.exit(main())

