#!/bin/bash
echo "Installing Requirements..."
pip install -r requirements.txt

# REMOVED: collectstatic --clear
# We are relying on the 'public' folder that is already in Git.

echo "Build Completed!"
