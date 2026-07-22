#!/bin/bash
cd "$(dirname "$0")"
echo "Installing dependencies..."
pip3 install flask -q
echo ""
echo "Starting Screenshot Organizer on http://localhost:5000"
echo "Press Ctrl+C to stop."
echo ""
sleep 2
open http://localhost:5000
python3 web_app.py
