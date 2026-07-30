#!/bin/bash
# setup_env.sh - Prepares the Python environment for EOS Lab (Windows MT5 + WSL)

set -e

# -------------------------------------------------
# Locate project root
# -------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "EOS Lab Environment Setup (Windows MT5 + WSL)"
echo "=========================================="
echo "Project Root: $PROJECT_ROOT"

# -------------------------------------------------
# Navigate to Python source
# -------------------------------------------------
cd "$PROJECT_ROOT/src/python"

# -------------------------------------------------
# Create virtual environment
# -------------------------------------------------
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# -------------------------------------------------
# Activate environment
# -------------------------------------------------
source venv/bin/activate

# -------------------------------------------------
# Install dependencies
# -------------------------------------------------
echo "Installing Python dependencies..."

python -m pip install --upgrade pip
python -m pip install pandas numpy matplotlib jupyter

echo "✅ Python environment ready."

# -------------------------------------------------
# Locate MT5 EventStore
# -------------------------------------------------
WIN_EVENTSTORE=$(find "/mnt/c/Users" \
    -path "*/AppData/Roaming/MetaQuotes/Terminal/Common/Files/EventStore" \
    -type d 2>/dev/null | head -n 1)

if [ -z "$WIN_EVENTSTORE" ]; then
    echo ""
    echo "⚠️  No existing EventStore found."

    USER_DIR=$(ls /mnt/c/Users | grep -v "Public" | grep -v "Default" | grep -v "All Users" | head -n 1)

    WIN_EVENTSTORE="/mnt/c/Users/$USER_DIR/AppData/Roaming/MetaQuotes/Terminal/Common/Files/EventStore"

    echo "Creating:"
    echo "  $WIN_EVENTSTORE"

    mkdir -p "$WIN_EVENTSTORE"
else
    echo "✅ Found MT5 EventStore:"
    echo "   $WIN_EVENTSTORE"
fi

# -------------------------------------------------
# Link project data/raw -> EventStore
# -------------------------------------------------
rm -rf "$PROJECT_ROOT/data/raw"
ln -s "$WIN_EVENTSTORE" "$PROJECT_ROOT/data/raw"

echo "✅ Linked:"
echo "   $PROJECT_ROOT/data/raw -> $WIN_EVENTSTORE"

# -------------------------------------------------
# Done
# -------------------------------------------------
echo ""
echo "=========================================="
echo "Setup complete!"
echo ""
echo "Activate the environment:"
echo "  source $PROJECT_ROOT/src/python/venv/bin/activate"
echo ""
echo "Run the reader:"
echo "  cd $PROJECT_ROOT/src/python"
echo "  python event_reader.py EURUSD"
echo "=========================================="

EOF
