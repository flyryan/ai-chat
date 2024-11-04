#!/bin/bash
echo "Starting application..."
echo "Python version:"
python --version
echo "Pip version:"
pip --version
echo "Installed packages:"
pip list
echo "Current directory:"
pwd
echo "Directory contents:"
ls -la
echo "Starting Gunicorn..."
gunicorn main:app --config gunicorn.conf.py