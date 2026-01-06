#!/bin/bash

# Copy architecture guides to a target repository
# Usage: ./copy-guides.sh /path/to/target/repo

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory (where this repo lives)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if target path is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage:${NC} ./copy-guides.sh /absolute/path/to/target/repo"
    echo ""
    echo "Example:"
    echo "  ./copy-guides.sh /Users/raphaelm/Documents/Coding/boilerplates/next16bp"
    exit 1
fi

TARGET_REPO="$1"

# Validate target path is absolute
if [[ "$TARGET_REPO" != /* ]]; then
    echo -e "${RED}Error:${NC} Please provide an absolute path (starting with /)"
    exit 1
fi

# Check if target directory exists
if [ ! -d "$TARGET_REPO" ]; then
    echo -e "${RED}Error:${NC} Target directory does not exist: $TARGET_REPO"
    exit 1
fi

# Create guides directory in target repo
GUIDES_DIR="$TARGET_REPO/guides"
mkdir -p "$GUIDES_DIR"

echo -e "${GREEN}Copying guides to:${NC} $GUIDES_DIR"
echo ""

# Copy client/ folder
if [ -d "$SCRIPT_DIR/client" ]; then
    echo "  Copying client/..."
    rm -rf "$GUIDES_DIR/client"
    cp -r "$SCRIPT_DIR/client" "$GUIDES_DIR/client"
else
    echo -e "${YELLOW}  Warning: client/ not found${NC}"
fi

# Copy server/ folder
if [ -d "$SCRIPT_DIR/server" ]; then
    echo "  Copying server/..."
    rm -rf "$GUIDES_DIR/server"
    cp -r "$SCRIPT_DIR/server" "$GUIDES_DIR/server"
else
    echo -e "${YELLOW}  Warning: server/ not found${NC}"
fi

# Copy README.md
if [ -f "$SCRIPT_DIR/README.md" ]; then
    echo "  Copying README.md..."
    cp "$SCRIPT_DIR/README.md" "$GUIDES_DIR/README.md"
else
    echo -e "${YELLOW}  Warning: README.md not found${NC}"
fi

echo ""
echo -e "${GREEN}Done!${NC} Guides copied to $GUIDES_DIR"
echo ""
echo "Structure:"
echo "  $GUIDES_DIR/"
echo "  ├── client/"
echo "  ├── server/"
echo "  └── README.md"
