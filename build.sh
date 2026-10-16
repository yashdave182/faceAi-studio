#!/usr/bin/env bash
# Build script for unified deployment (Frontend + Backend on single Render Web Service)
set -o errexit

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Building React frontend..."
cd faceAi-client
npm install
npm run build
cd ..

echo "==> Build finished successfully!"
