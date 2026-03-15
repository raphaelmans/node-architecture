#!/bin/bash

# Copy the consumer guide bundle to a target repository.
# Usage: ./copy-guides.sh /absolute/path/to/target/repo

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

for DIR in client server legacy; do
    if [ -d "$SCRIPT_DIR/$DIR" ]; then
        echo "  Copying $DIR/..."
        rm -rf "$GUIDES_DIR/$DIR"
        cp -r "$SCRIPT_DIR/$DIR" "$GUIDES_DIR/$DIR"
    else
        echo -e "${YELLOW}  Warning: $DIR/ not found${NC}"
    fi
done

if [ -f "$SCRIPT_DIR/consumer/README.md" ]; then
    echo "  Copying consumer/README.md -> guides/README.md..."
    cp "$SCRIPT_DIR/consumer/README.md" "$GUIDES_DIR/README.md"
else
    echo -e "${YELLOW}  Warning: consumer/README.md not found${NC}"
fi

for FILE in AGENTS-MD-ALIGNMENT.md UPDATE-ARCHITECTURE.md OPENCODE-INTEGRATION.md; do
    if [ -f "$SCRIPT_DIR/consumer/$FILE" ]; then
        echo "  Copying consumer/$FILE..."
        cp "$SCRIPT_DIR/consumer/$FILE" "$GUIDES_DIR/$FILE"
    else
        echo -e "${YELLOW}  Warning: consumer/$FILE not found${NC}"
    fi
done

find "$GUIDES_DIR" -name '.DS_Store' -delete

echo ""
echo -e "${GREEN}Done!${NC} Guides copied to $GUIDES_DIR"
echo ""
echo "Structure:"
echo "  $GUIDES_DIR/"
echo "  ├── client/"
echo "  ├── server/"
echo "  ├── legacy/"
echo "  ├── README.md                  (DO NOT EDIT — generated)"
echo "  ├── AGENTS-MD-ALIGNMENT.md     (configure AGENTS.md / CLAUDE.md)"
echo "  ├── UPDATE-ARCHITECTURE.md     (how to update these guides)"
echo "  └── OPENCODE-INTEGRATION.md    (OpenCode integration guidance)"
echo ""
echo -e "${YELLOW}Next step:${NC} Open guides/AGENTS-MD-ALIGNMENT.md and follow"
echo "           the steps to update your AGENTS.md or CLAUDE.md."
