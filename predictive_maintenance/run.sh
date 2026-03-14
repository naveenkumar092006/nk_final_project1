#!/bin/bash
# run.sh — Quick start script for PredictMaint Pro

echo ""
echo "=================================================="
echo "  🏭  PredictMaint Pro — Setup & Launch"
echo "=================================================="

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

# Launch
echo ""
echo "🚀 Starting server at http://127.0.0.1:5000"
echo "👤 Login: admin / Admin@123"
echo ""
python app.py
