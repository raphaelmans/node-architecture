#!/bin/bash
#
# generate-pdf.sh - Generate PDF from user stories HTML document
#
# Usage: ./generate-pdf.sh [OPTIONS]
#
# Options:
#   -i, --input FILE      Input HTML file (default: user-stories-document.html)
#   -o, --output FILE     Output PDF file (default: User-Stories-Checkpoint-XX.pdf)
#   -d, --directory DIR   Working directory containing HTML (default: current)
#   -h, --help            Show this help message
#
# Prerequisites:
#   - Google Chrome installed (macOS, Linux, or Windows)
#
# Example:
#   ./generate-pdf.sh -d agent-plans/user-stories -o MyProject-Checkpoint-01.pdf
#

set -e

# Default values
INPUT_FILE="user-stories-document.html"
OUTPUT_FILE=""
WORK_DIR="."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }

# Show help
show_help() {
    head -25 "$0" | tail -20 | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--input)
            INPUT_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -d|--directory)
            WORK_DIR="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Find Chrome executable
find_chrome() {
    local chrome_paths=(
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        "/Applications/Chromium.app/Contents/MacOS/Chromium"
        # Linux
        "$(which google-chrome 2>/dev/null || true)"
        "$(which google-chrome-stable 2>/dev/null || true)"
        "$(which chromium-browser 2>/dev/null || true)"
        "$(which chromium 2>/dev/null || true)"
        # Windows (Git Bash / WSL)
        "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
        "/c/Program Files/Google/Chrome/Application/chrome.exe"
    )
    
    for path in "${chrome_paths[@]}"; do
        if [[ -n "$path" && -x "$path" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    return 1
}

# Main execution
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║          User Story PDF Generator                    ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""

    # Change to working directory
    if [[ ! -d "$WORK_DIR" ]]; then
        print_error "Directory not found: $WORK_DIR"
        exit 1
    fi
    cd "$WORK_DIR"
    print_info "Working directory: $(pwd)"

    # Check if input file exists
    if [[ ! -f "$INPUT_FILE" ]]; then
        print_error "Input HTML file not found: $INPUT_FILE"
        echo ""
        echo "Please ensure the HTML document has been generated first."
        echo "The agent should create 'user-stories-document.html' before running this script."
        exit 1
    fi
    print_success "Found input file: $INPUT_FILE"

    # Set default output filename if not provided
    if [[ -z "$OUTPUT_FILE" ]]; then
        # Try to extract checkpoint number from filename or directory
        CHECKPOINT=$(ls checkpoint-*.md 2>/dev/null | head -1 | sed 's/checkpoint-//' | sed 's/.md//' || echo "01")
        OUTPUT_FILE="User-Stories-Checkpoint-${CHECKPOINT}.pdf"
    fi
    print_info "Output file: $OUTPUT_FILE"

    # Find Chrome
    CHROME=$(find_chrome)
    if [[ -z "$CHROME" ]]; then
        print_error "Google Chrome not found!"
        echo ""
        echo "Please install Google Chrome or Chromium to generate PDFs."
        echo ""
        echo "Installation instructions:"
        echo "  macOS:   brew install --cask google-chrome"
        echo "  Ubuntu:  sudo apt install google-chrome-stable"
        echo "  Fedora:  sudo dnf install google-chrome-stable"
        exit 1
    fi
    print_success "Found Chrome: $CHROME"

    # Generate PDF
    print_info "Generating PDF..."
    echo ""

    HTML_PATH="$(pwd)/$INPUT_FILE"
    
    "$CHROME" \
        --headless \
        --disable-gpu \
        --no-sandbox \
        --disable-software-rasterizer \
        --print-to-pdf="$OUTPUT_FILE" \
        --print-to-pdf-no-header \
        --no-pdf-header-footer \
        "file://$HTML_PATH" 2>/dev/null

    # Check result
    if [[ -f "$OUTPUT_FILE" ]]; then
        FILE_SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
        PAGE_COUNT=$(file "$OUTPUT_FILE" | grep -oP '\d+ page' | grep -oP '\d+' || echo "?")
        
        echo ""
        echo "╔══════════════════════════════════════════════════════╗"
        echo "║                   PDF Generated!                     ║"
        echo "╚══════════════════════════════════════════════════════╝"
        echo ""
        print_success "File: $(pwd)/$OUTPUT_FILE"
        print_success "Size: $FILE_SIZE"
        print_success "Pages: $PAGE_COUNT"
        echo ""
    else
        print_error "PDF generation failed!"
        exit 1
    fi
}

# Run main function
main
