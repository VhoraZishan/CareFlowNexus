#!/bin/bash

# ============================================
# CareFlow Nexus - Hugging Face Deployment Script
# ============================================

set -e

echo "============================================"
echo "CareFlow Nexus - Hugging Face Deployment"
echo "============================================"
echo ""

# Check if Hugging Face CLI is installed
if ! command -v huggingface-cli &> /dev/null; then
    echo "❌ Hugging Face CLI not found!"
    echo ""
    echo "Install it with:"
    echo "  pip install huggingface_hub"
    echo ""
    exit 1
fi

# Get Hugging Face username
read -p "Enter your Hugging Face username: " HF_USERNAME

if [ -z "$HF_USERNAME" ]; then
    echo "❌ Username is required!"
    exit 1
fi

# Get Space name
read -p "Enter Space name (default: careflow-nexus-agents): " SPACE_NAME
SPACE_NAME=${SPACE_NAME:-careflow-nexus-agents}

SPACE_URL="https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"

echo ""
echo "Creating Space: $HF_USERNAME/$SPACE_NAME"
echo ""

# Check if logged in
if ! huggingface-cli whoami &> /dev/null; then
    echo "You need to login to Hugging Face first."
    echo "Running: huggingface-cli login"
    echo ""
    huggingface-cli login
fi

echo ""
echo "✓ Logged in to Hugging Face"
echo ""

# Create temporary directory for deployment
DEPLOY_DIR=$(mktemp -d)
echo "Creating deployment package in: $DEPLOY_DIR"

# Copy necessary files
echo "Copying files..."
cp agent_server.py "$DEPLOY_DIR/"
cp memory_agent.py "$DEPLOY_DIR/"
cp allocator_agent.py "$DEPLOY_DIR/"
cp communicator_agent.py "$DEPLOY_DIR/"
cp base_agent.py "$DEPLOY_DIR/"
cp config.py "$DEPLOY_DIR/"
cp requirements.txt "$DEPLOY_DIR/"
cp Dockerfile "$DEPLOY_DIR/"
cp README_HUGGINGFACE.md "$DEPLOY_DIR/README.md"

# Copy directories
cp -r services "$DEPLOY_DIR/"
cp -r prompts "$DEPLOY_DIR/"
cp -r utils "$DEPLOY_DIR/"

# Create .gitignore
cat > "$DEPLOY_DIR/.gitignore" << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.log
.env
config/serviceAccountKey.json
*.db
.DS_Store
EOF

# Create README for Space
cat > "$DEPLOY_DIR/README.md" << EOF
---
title: CareFlow Nexus AI Agents
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
license: mit
---

# CareFlow Nexus AI Agents

AI-powered hospital bed management system using hybrid intelligence (50% rules + 50% Gemini AI).

## 🚀 Quick Start

1. **Set Secrets** in Space Settings:
   - \`FIREBASE_SERVICE_ACCOUNT_JSON\` - Your Firebase service account JSON
   - \`GOOGLE_API_KEY\` - Your Google Gemini API key

2. **Wait for Build** - The Space will automatically build and start

3. **Test API** - Visit \`/docs\` for interactive API documentation

## 📚 API Endpoints

- \`POST /agent/bed-assignment\` - Get bed recommendations
- \`POST /agent/cleaner-assignment\` - Assign cleaners
- \`POST /agent/nurse-assignment\` - Assign nurses
- \`GET /health\` - Health check
- \`GET /docs\` - API documentation

## 🔧 Configuration

Required Secrets:
- \`FIREBASE_SERVICE_ACCOUNT_JSON\` - Firebase credentials
- \`GOOGLE_API_KEY\` - Gemini API key

Optional:
- \`GEMINI_MODEL\` (default: gemini-2.0-flash-exp)
- \`RULE_WEIGHT\` (default: 0.5)
- \`AI_WEIGHT\` (default: 0.5)

## 📖 Full Documentation

See [GitHub Repository](https://github.com/your-repo/careflow-nexus) for complete documentation.

## 🤖 How It Works

This Space provides intelligent bed allocation using:
1. **Rule-Based Scoring** (50%) - Equipment match, ward fit, proximity
2. **AI Reasoning** (50%) - Gemini analyzes context and edge cases
3. **Hybrid Decision** - Combines both for optimal recommendations

Built with FastAPI, Google Gemini AI, and Firebase.
EOF

# Initialize git in deploy directory
cd "$DEPLOY_DIR"
git init
git add .
git commit -m "Initial deployment"

# Add Hugging Face remote
git remote add hf "https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"

echo ""
echo "============================================"
echo "Ready to Deploy!"
echo "============================================"
echo ""
echo "Space URL: $SPACE_URL"
echo ""
echo "Next steps:"
echo ""
echo "1. Create the Space on Hugging Face:"
echo "   Go to: https://huggingface.co/new-space"
echo "   - Name: $SPACE_NAME"
echo "   - SDK: Docker"
echo "   - License: MIT (or your choice)"
echo ""
echo "2. After creating the Space, run:"
echo "   cd $DEPLOY_DIR"
echo "   git push hf main"
echo ""
echo "3. Add secrets in Space Settings:"
echo "   - FIREBASE_SERVICE_ACCOUNT_JSON"
echo "   - GOOGLE_API_KEY"
echo ""
echo "4. Wait for build (5-10 minutes)"
echo ""
echo "5. Test your API at:"
echo "   $SPACE_URL"
echo ""

read -p "Press Enter to push to Hugging Face (make sure Space is created first)..."

echo ""
echo "Pushing to Hugging Face..."
git push hf main

echo ""
echo "============================================"
echo "✓ Deployment Complete!"
echo "============================================"
echo ""
echo "Your Space is being built at:"
echo "$SPACE_URL"
echo ""
echo "Don't forget to add your secrets:"
echo "1. Go to: $SPACE_URL/settings"
echo "2. Click 'Repository secrets'"
echo "3. Add FIREBASE_SERVICE_ACCOUNT_JSON"
echo "4. Add GOOGLE_API_KEY"
echo ""
echo "Check build logs at: $SPACE_URL"
echo ""
echo "API will be available at:"
echo "  - Health: $SPACE_URL/health"
echo "  - Docs: $SPACE_URL/docs"
echo ""
