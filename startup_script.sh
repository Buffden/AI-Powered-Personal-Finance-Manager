#!/bin/bash

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Start Flask backend in the background
echo "Starting Flask backend..."
python backend/flask_app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 3

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
streamlit run frontend/streamlit_app.py

# Cleanup: Kill Flask process when Streamlit exits
kill $FLASK_PID 