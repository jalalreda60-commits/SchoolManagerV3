#!/bin/bash
echo "================================"
echo "  Le Schema School ERP v1.0"
echo "  Innover - Creer - Exceller"
echo "================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Install with: sudo apt install python3 python3-pip python3-tk"
    exit 1
fi

# Check tkinter
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing tkinter..."
    sudo apt-get install -y python3-tk 2>/dev/null || brew install python-tk 2>/dev/null
fi

# Install dependencies
echo "Checking dependencies..."
pip3 install -r requirements.txt --quiet

# Launch
echo "Launching Le Schema School ERP..."
python3 main.py
