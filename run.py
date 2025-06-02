#!/usr/bin/env python
"""
Academic Website Builder - Cross-platform launcher script

Usage:
  python run.py build      # Build site for production
  python run.py serve      # Start dev server with hot reload
  python run.py clean      # Clean generated files
"""
import sys
import os
import subprocess
import argparse

def print_banner(msg):
    """Print a formatted banner message"""
    print(f"[Academic Website] {msg}")

def ensure_requirements():
    """Ensure all required Python packages are installed"""
    try:
        import jinja2
        import watchdog
        import markdown
        import htmlmin
        return True
    except ImportError as e:
        missing_package = str(e).split("'")[1]
        print_banner(f"Missing required package: {missing_package}")
        print_banner("Installing required packages...")
        
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True

def run_command(command, args=[]):
    """Run a command with proper error handling"""
    script_path = os.path.join("scripts", "site_builder.py")
    
    try:
        subprocess.check_call([sys.executable, script_path, command] + args)
        return True
    except subprocess.CalledProcessError as e:
        print_banner(f"Error executing command: {e}")
        return False
    except KeyboardInterrupt:
        print_banner("Process interrupted by user")
        return True

def main():
    """Main entry point for the launcher script"""
    parser = argparse.ArgumentParser(description="Academic Website Builder")
    parser.add_argument('command', choices=['build', 'serve', 'clean'], 
                        help='Command to run (build, serve, clean)')
    parser.add_argument('--port', type=int, default=8080, 
                        help='Port for development server (default: 8080)')
    parser.add_argument('--no-minify', action='store_true',
                        help='Disable CSS minification for builds')
    
    args = parser.parse_args()
    
    # Ensure we have all required packages
    if not ensure_requirements():
        sys.exit(1)
    
    # Execute the appropriate command
    if args.command == 'build':
        print_banner("Building site for production...")
        cmd_args = []
        if args.no_minify:
            cmd_args.append('--no-minify')
        run_command('build', cmd_args)
        print_banner("Build complete!")
        
    elif args.command == 'serve':
        print_banner("Starting development server...")
        run_command('serve', ['--port', str(args.port)])
        
    elif args.command == 'clean':
        print_banner("Cleaning generated files...")
        run_command('clean')
        print_banner("Cleanup complete!")

if __name__ == "__main__":
    main() 