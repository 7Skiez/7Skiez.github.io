#!/usr/bin/env python
"""
Academic Website Builder - A comprehensive static site generator

Usage:
  python scripts/site_builder.py build  # Build the site for production
  python scripts/site_builder.py serve  # Start development server with hot reload
  python scripts/site_builder.py clean  # Remove generated files
"""
import json
import os
import sys
import time
import argparse
import http.server
import socketserver
import shutil
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import jinja2
from markupsafe import Markup
import htmlmin
import markdown
import re

# Configuration
PORT = 8080
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(BASE_DIR, 'content')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
OUTPUT_FILE = os.path.join(BASE_DIR, 'index.html')
BUILD_DIR = os.path.join(BASE_DIR, 'build')
CSS_INPUT = os.path.join(TEMPLATE_DIR, 'styles.css')
CSS_OUTPUT = os.path.join(BUILD_DIR, 'css', 'output.css')
TAILWIND_CONFIG = os.path.join(BASE_DIR, 'tailwind.config.js')
DEBOUNCE_TIME = 0.5
PORT_ATTEMPTS = 10

# Utility functions
def ensure_dir(directory):
    """Ensure a directory exists"""
    os.makedirs(directory, exist_ok=True)
    return directory

def fix_spacing(text):
    """Fix spacing in inline Markdown links"""
    if not text:
        return ''
    return re.sub(r'(\S)\[', r'\1 \[', text)

def copy_css():
    """Copy CSS file to build directory when Tailwind is not available"""
    ensure_dir(os.path.dirname(CSS_OUTPUT))
    shutil.copy2(CSS_INPUT, CSS_OUTPUT)
    print(f"CSS copied to {os.path.relpath(CSS_OUTPUT, BASE_DIR)}")
    return True

def build_tailwind_css(minify=True):
    """Build Tailwind CSS with proper minification for production"""
    try:
        # Create build directory if it doesn't exist
        ensure_dir(os.path.dirname(CSS_OUTPUT))
        
        # Determine the command, adding --minify for production builds
        cmd = ["npx", "tailwindcss", "-i", CSS_INPUT, "-o", CSS_OUTPUT, "--config", TAILWIND_CONFIG]
        if minify:
            cmd.append("--minify")
        
        # For Windows, we need shell=True for npx to work properly
        shell_param = sys.platform.startswith('win')
        
        # Run Tailwind CSS build
        print(f"Building Tailwind CSS {'(minified)' if minify else ''}...")
        if shell_param:
            cmd_str = " ".join(cmd)
            result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, shell=False, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Tailwind CSS build failed: {result.stderr}")
            print("Falling back to simple CSS copy")
            copy_css()
            return False
        
        print(f"Tailwind CSS build completed: {os.path.relpath(CSS_OUTPUT, BASE_DIR)}")
        return True
    
    except Exception as e:
        print(f"Error building Tailwind CSS: {e}")
        print("Falling back to simple CSS copy")
        copy_css()
        return False

def start_tailwind_watch():
    """Start Tailwind CSS in watch mode with proper error handling"""
    try:
        # Create build directory if it doesn't exist
        ensure_dir(os.path.dirname(CSS_OUTPUT))
        
        # Try to start Tailwind in watch mode
        print("Starting Tailwind CSS watch mode...")
        
        # Determine the right command for the platform
        cmd = ["npx", "tailwindcss", "-i", CSS_INPUT, "-o", CSS_OUTPUT, "--config", TAILWIND_CONFIG, "--watch"]
        
        # For Windows, we need shell=True for npx to work properly
        shell_param = sys.platform.startswith('win')
        
        # Create separate process for Tailwind
        if shell_param:
            cmd_str = " ".join(cmd)
            tailwind_process = subprocess.Popen(
                cmd_str,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            tailwind_process = subprocess.Popen(
                cmd,
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
        
        # Check if process started successfully
        time.sleep(1)
        if tailwind_process.poll() is not None:
            print("Tailwind CSS watch mode not started. Using simple CSS copy instead.")
            copy_css()
            return None
        else:
            print("Tailwind CSS watch mode started successfully")
            return tailwind_process
            
    except Exception as e:
        print(f"Error starting Tailwind: {e}")
        print("Falling back to simple CSS copy")
        copy_css()
    
    return None

class WebsiteGenerator:
    """Core website generator"""
    
    def __init__(self):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(TEMPLATE_DIR),
            autoescape=jinja2.select_autoescape(['html']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        # Store config globally for filters to access
        self.config = {}
        self.colors = {}
        self.env.filters['markdown'] = self.md_filter
        self.env.filters['fix_spacing'] = fix_spacing
    
    def md_filter(self, text):
        """Convert markdown to HTML with improved link handling using config colors"""
        if not text:
            return ''
        # Use the 'extra' and 'sane_lists' extensions for better Markdown support
        html = markdown.markdown(text, extensions=['extra', 'sane_lists'])
        
        # Fix a common issue with nested Markdown links 
        # Replace raw markdown links that didn't get processed properly
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        while re.search(link_pattern, html):
            html = re.sub(link_pattern, r'<a href="\2">\1</a>', html)
        
        # Use the colors if available, otherwise use defaults
        link_class = self.colors.get('link', 'text-blue-600')
        hover_class = self.colors.get('linkHover', 'hover:text-blue-800')
        
        html = html.replace('<a href', f'<a class="{link_class} {hover_class}" href')
        
        return Markup(html)
    
    def load_json(self, filename):
        """Load and parse a JSON file, with error handling"""
        path = os.path.join(CONTENT_DIR, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {path}: {e}")
            return {}
    
    def load_content_data(self):
        """Load all content data from JSON files"""
        # Load config and colors first
        config = self.load_json('config.json')
        colors = self.load_json('colors.json')
        
        self.config = config  # Store for filters to access
        self.colors = colors  # Store for filters to access
        
        data = {
            'config': config,
            'colors': colors,
            'header': self.load_json('header.json'),
            'logos': self.load_json('logos.json'),
            'footer': self.load_json('footer.json'),
            'news': self.load_json('news.json'),
            'publications': self.load_json('publications.json'),
            'honors': self.load_json('honors.json'),
            'year': time.strftime('%Y')
        }
        
        # Process bio paragraphs to fix spacing in markdown links
        if 'bio' in data['header']:
            data['header']['bio'] = [fix_spacing(p) for p in data['header']['bio']]
            
        return data
    
    def build(self, minify_css=True):
        """Build the website
        
        Args:
            minify_css (bool): Whether to minify CSS (True for production)
        """
        # Ensure the build directory exists
        ensure_dir(BUILD_DIR)
        
        # Build CSS for production or development
        build_tailwind_css(minify=minify_css)
        
        # Load content and render template
        data = self.load_content_data()
        template = self.env.get_template('base.html')
        html = template.render(**data)
        
        # Minify HTML for production
        minified = htmlmin.minify(html, 
            remove_comments=True,
            remove_empty_space=True,
            reduce_boolean_attributes=True
        )
        
        # Write output file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(minified)
        
        print(f"Site built successfully: {os.path.abspath(OUTPUT_FILE)}")
        return True

    def clean(self):
        """Clean generated files"""
        print("[Academic Website] Cleaning build files...")
        
        # Files and directories to remove
        to_clean = [OUTPUT_FILE]
        
        # Clean build directory if it exists
        if os.path.exists(BUILD_DIR):
            to_clean.append(BUILD_DIR)
        
        for item in to_clean:
            try:
                if os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"Removed directory: {item}")
                elif os.path.isfile(item):
                    os.remove(item)
                    print(f"Removed file: {item}")
            except Exception as e:
                print(f"Error removing {item}: {str(e)}")
        
        print("[Academic Website] Cleanup complete.")
        return True

class ChangeHandler(FileSystemEventHandler):
    """Handles file change events during development"""
    
    def __init__(self, generator):
        self.generator = generator
        self.last_event_time = 0
    
    def on_any_event(self, event):
        current_time = time.time()
        if current_time - self.last_event_time < DEBOUNCE_TIME:
            return
        
        # Skip output file changes to avoid rebuild loops
        if event.src_path.endswith(os.path.basename(OUTPUT_FILE)) or '/build/' in event.src_path:
            return
            
        self.last_event_time = current_time
        print(f"\nChange detected in {event.src_path}")
        self.generator.build(minify_css=False)  # Use non-minified CSS for development

def serve(generator, port=PORT):
    """Start development server with hot reload and Tailwind integration"""
    # Initial build without CSS minification for development
    generator.build(minify_css=False)
    
    # Start Tailwind watch process
    tailwind_process = start_tailwind_watch()
    
    # Setup file change observer
    event_handler = ChangeHandler(generator)
    observer = Observer()
    
    # Define paths to watch
    paths_to_watch = [CONTENT_DIR, TEMPLATE_DIR] 
    for path_to_watch in paths_to_watch:
        if os.path.exists(path_to_watch):
            observer.schedule(event_handler, path_to_watch, recursive=True)
    
    observer.start()
    print(f"Watching for changes in {', '.join(paths_to_watch)}")
    
    # Start HTTP server
    os.chdir(BASE_DIR)  # Change to the base directory for serving files
    handler = http.server.SimpleHTTPRequestHandler
    httpd_instance = None
    
    # Try multiple ports in case the default is busy
    for attempt in range(PORT_ATTEMPTS):
        try:
            current_port = port + attempt
            httpd_instance = socketserver.TCPServer(("", current_port), handler)
            print(f"Serving at http://localhost:{current_port}")
            break
        except OSError as e:
            if e.errno in [10048, 98]:  # Port in use
                print(f"Port {port + attempt} busy, trying next...")
                if attempt == PORT_ATTEMPTS - 1:
                    print("Could not find an available port.")
                    observer.stop()
                    if tailwind_process:
                        tailwind_process.terminate()
                    sys.exit(1)
            else: 
                raise
    
    # Serve until interrupted
    try:
        httpd_instance.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        # Clean up resources
        httpd_instance.shutdown()
        httpd_instance.server_close()
        observer.stop()
        if tailwind_process and tailwind_process.poll() is None:
            print("Stopping Tailwind CSS process...")
            try:
                tailwind_process.terminate()
            except:
                pass
    
    observer.join()

def main():
    """Main entry point with command parsing"""
    parser = argparse.ArgumentParser(description="Academic website generator")
    parser.add_argument('command', choices=['build', 'serve', 'clean'], help='Command to run')
    parser.add_argument('--port', type=int, default=PORT, help='Port for development server')
    parser.add_argument('--no-minify', action='store_true', help='Disable CSS minification for builds')
    args = parser.parse_args()
    
    generator = WebsiteGenerator()
    
    if args.command == 'build':
        generator.build(minify_css=not args.no_minify)
        print("Build complete.")
    elif args.command == 'serve':
        serve(generator, port=args.port)
    elif args.command == 'clean':
        generator.clean()

if __name__ == "__main__":
    main() 