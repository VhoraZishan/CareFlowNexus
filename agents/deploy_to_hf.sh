#!/bin/bash
# CareFlow Nexus - Hugging Face Deployment Script
# Quick deployment script for Hugging Face Spaces

set -e

echo "============================================================"
echo "CareFlow Nexus - Hugging Face Deployment"
echo "============================================================"
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "ERROR: git is not installed. Please install git first."
    exit 1
fi

# Check if Hugging Face CLI is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "Hugging Face CLI not found. Installing..."
    pip install huggingface_hub
fi

# Get Hugging Face username
echo "Enter your Hugging Face username:"
read HF_USERNAME

if [ -z "$HF_USERNAME" ]; then
    echo "ERROR: Username cannot be empty"
    exit 1
fi

# Set space name
SPACE_NAME="careflow-nexus"
echo ""
echo "Space will be created as: $HF_USERNAME/$SPACE_NAME"
echo ""

# Login to Hugging Face
echo "Step 1: Logging in to Hugging Face..."
huggingface-cli login

# Initialize git if not already
if [ ! -d ".git" ]; then
    echo ""
    echo "Step 2: Initializing git repository..."
    git init
    git branch -M main
fi

# Create .gitignore if doesn't exist
if [ ! -f ".gitignore" ]; then
    echo ""
    echo "Step 3: Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
venv/
env/
ENV/

# Secrets - DO NOT COMMIT
.env
.env.local
config/serviceAccountKey.json
serviceAccountKey.json

# Logs
*.log
careflow_agents_*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Test
.pytest_cache/
.coverage
EOF
fi

# Create README for Hugging Face
echo ""
echo "Step 4: Creating README.md for Hugging Face..."
cat > README.md << 'EOF'
---
title: CareFlow Nexus
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# CareFlow Nexus - AI Hospital Bed Management

AI-powered hospital bed management system using **Gemini 2.5 Flash**.

## 🚀 Features

- **Agent 1 (Memory)**: Real-time hospital state management
- **Agent 2 (Bed Allocator)**: 50% rule-based + 50% AI bed recommendations
- **Agent 3 (Communicator)**: Automated task assignment

## 📖 API Documentation

Access the interactive API docs at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **Health Check**: `/health`

## 🔑 Default Login

**Doctor**: `doctor1` / `doc123`
**Receptionist**: `receptionist1` / `recep123`

## 🛠️ Built With

- FastAPI + Uvicorn
- Firebase Firestore
- Google Gemini 2.5 Flash
- Python 3.11

## 📝 License

MIT
EOF

# Add Hugging Face remote
echo ""
echo "Step 5: Adding Hugging Face remote..."
SPACE_URL="https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"

# Remove existing remote if it exists
git remote remove hf 2>/dev/null || true

# Add new remote
git remote add hf "https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"

echo ""
echo "============================================================"
echo "IMPORTANT: Set up your secrets on Hugging Face!"
echo "============================================================"
echo ""
echo "Before pushing, go to your Space settings and add these secrets:"
echo ""
echo "1. FIREBASE_SERVICE_ACCOUNT_JSON"
echo "   Copy entire content of serviceAccountKey.json"
echo ""
echo "2. GOOGLE_API_KEY"
echo "   Your Gemini API key"
echo ""
echo "3. FIREBASE_DATABASE_URL"
echo "   Format: https://your-project-id.firebaseio.com"
echo ""
echo "Space URL: $SPACE_URL"
echo ""
read -p "Press Enter once you've added the secrets..."

# Stage files
echo ""
echo "Step 6: Staging files for deployment..."
git add .

# Commit
echo ""
echo "Step 7: Creating commit..."
git commit -m "Deploy CareFlow Nexus to Hugging Face" || echo "No changes to commit"

# Push to Hugging Face
echo ""
echo "Step 8: Pushing to Hugging Face..."
echo ""
git push hf main --force

echo ""
echo "============================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "============================================================"
echo ""
echo "Your application is deploying to:"
echo "  $SPACE_URL"
echo ""
echo "It may take 5-10 minutes to build and start."
echo ""
echo "Once ready, access:"
echo "  - Swagger UI: https://$HF_USERNAME-$SPACE_NAME.hf.space/docs"
echo "  - Health: https://$HF_USERNAME-$SPACE_NAME.hf.space/health"
echo ""
echo "============================================================"
