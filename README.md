# Academic Website Generator

A streamlined, minimal static site generator for academic personal websites, built with Python and Tailwind CSS.

## Features

- 🎨 Clean and modern design
- 📱 Fully responsive layout
- 🌓 Dark mode support
- 📊 Publication showcase with hover effects
- 📰 News and updates timeline
- 🏆 Honors and awards section
- 🔍 SEO optimized
- ⚡ Fast loading and performance
- 🎯 Easy to customize

## Quick Start

### Prerequisites

- Python 3.6 or newer
- Node.js and npm (for Tailwind CSS) - optional but recommended

### Installation

1. Clone the repository
2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Install Node dependencies:
   ```
   npm install
   ```

### Usage

All commands can be run through the `run.py` script, which provides a unified interface on all platforms:

```
# Build site for production
python run.py build

# Start development server with hot reload
python run.py serve

# Clean generated files
python run.py clean
```

## Project Structure

```
.
├── assets/              # Static assets (images, documents)
│   ├── fonts/           # Self-hosted web fonts
│   ├── images/          # Images and logos
│   └── documents/       # PDF and other downloadable files
├── build/               # Generated CSS output
├── content/             # JSON content files
│   ├── config.json      # Site configuration
│   ├── header.json      # Header content with bio
│   ├── publications.json# Publications list
│   └── ...              # Other content sections
├── scripts/             # Build scripts
│   └── site_builder.py  # Main generator script
├── templates/           # HTML templates
│   ├── base.html        # Base template
│   ├── styles.css       # Source CSS for Tailwind
│   └── partials/        # Template components
├── run.py               # Cross-platform launcher script
├── index.html           # Generated output
├── requirements.txt     # Python dependencies
└── tailwind.config.js   # Tailwind CSS configuration
```

## Customization

### Content

Edit the JSON files in the `content/` directory to update your site's content. Each section of the website has its own dedicated JSON file.

### Templates

The site's appearance is controlled by templates in the `templates/` directory. The `base.html` file defines the overall structure, while partials in the `partials/` directory handle specific sections.

### Styling

Styles are defined in `templates/styles.css` using Tailwind CSS utility classes. Run the development server to see changes in real-time.

## Deployment

After building your site with `python run.py build`, the resulting `index.html` file and `assets/` directory can be deployed to any static hosting service.

## License

MIT License
