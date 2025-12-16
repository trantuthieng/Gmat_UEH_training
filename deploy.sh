#!/bin/bash
# Auto Deploy Script for GMAT Training System (Linux/Mac)
# Usage: ./deploy.sh

echo "🚀 GMAT Training System - Auto Deploy Script"
echo "============================================="
echo ""

# Configuration
REPO_URL="https://github.com/trantuthieng/Gmat_UEH_training.git"
APP_NAME="gmat-ueh-training"
RESOURCE_GROUP="gmat-rg"
LOCATION="southeastasia"
RUNTIME="PYTHON:3.11"
SKU="B1"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Step 1: Check if git is initialized
echo -e "${YELLOW}📝 Step 1: Checking Git repository...${NC}"
if [ ! -d ".git" ]; then
    echo -e "${GREEN}  Initializing Git repository...${NC}"
    git init
    git branch -M main
else
    echo -e "${GREEN}  ✓ Git repository already initialized${NC}"
fi

# Step 2: Check remote
echo ""
echo -e "${YELLOW}📝 Step 2: Setting up remote repository...${NC}"
if ! git remote | grep -q "origin"; then
    echo -e "${GREEN}  Adding remote origin...${NC}"
    git remote add origin $REPO_URL
else
    echo -e "${GREEN}  ✓ Remote origin already configured${NC}"
fi

# Step 3: Add and commit files
echo ""
echo -e "${YELLOW}📝 Step 3: Committing changes...${NC}"
git add .
COMMIT_MESSAGE="Auto deploy: $(date '+%Y-%m-%d %H:%M:%S')"
git commit -m "$COMMIT_MESSAGE"
echo -e "${GREEN}  ✓ Changes committed${NC}"

# Step 4: Push to GitHub
echo ""
echo -e "${YELLOW}📝 Step 4: Pushing to GitHub...${NC}"
if git push -u origin main 2>/dev/null; then
    echo -e "${GREEN}  ✓ Code pushed to GitHub successfully${NC}"
else
    echo -e "${RED}  ⚠️  Push failed. You may need to:${NC}"
    echo -e "${RED}     1. Set up GitHub authentication (Personal Access Token)${NC}"
    echo -e "${RED}     2. Or use: gh auth login${NC}"
    echo ""
    read -p "Continue with Azure deployment? (y/n) " continue
    if [ "$continue" != "y" ]; then
        exit
    fi
fi

# Step 5: Check if Azure CLI is installed
echo ""
echo -e "${YELLOW}📝 Step 5: Checking Azure CLI...${NC}"
if command -v az &> /dev/null; then
    AZ_VERSION=$(az version --output json | jq -r '.["azure-cli"]')
    echo -e "${GREEN}  ✓ Azure CLI installed: $AZ_VERSION${NC}"
else
    echo -e "${RED}  ✗ Azure CLI not found${NC}"
    echo -e "${YELLOW}  Install: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash${NC}"
    echo ""
    echo -e "${YELLOW}💡 Alternative: Deploy manually via Azure Portal${NC}"
    echo -e "${YELLOW}   See DEPLOYMENT_GUIDE.md for instructions${NC}"
    exit
fi

# Step 6: Login to Azure
echo ""
echo -e "${YELLOW}📝 Step 6: Azure Login...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${GREEN}  Opening browser for Azure login...${NC}"
    az login
else
    echo -e "${GREEN}  ✓ Already logged in to Azure${NC}"
fi

# Step 7: Deploy to Azure
echo ""
echo -e "${YELLOW}📝 Step 7: Deploying to Azure App Service...${NC}"
echo -e "${CYAN}  App Name: $APP_NAME${NC}"
echo -e "${CYAN}  Resource Group: $RESOURCE_GROUP${NC}"
echo -e "${CYAN}  Location: $LOCATION${NC}"
echo ""

read -p "Continue with deployment? (y/n) " deploy
if [ "$deploy" == "y" ]; then
    echo -e "${GREEN}  Deploying... (this may take 3-5 minutes)${NC}"
    
    az webapp up \
        --name $APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --runtime $RUNTIME \
        --sku $SKU \
        --location $LOCATION
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}  ✓ Deployment successful!${NC}"
        
        # Step 8: Get app URL
        echo ""
        echo -e "${YELLOW}📝 Step 8: Getting app URL...${NC}"
        APP_URL=$(az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query defaultHostName -o tsv)
        
        echo ""
        echo -e "${CYAN}=============================================${NC}"
        echo -e "${GREEN}✨ Deployment Complete!${NC}"
        echo -e "${CYAN}=============================================${NC}"
        echo ""
        echo -e "${YELLOW}📱 Your app is live at:${NC}"
        echo -e "${CYAN}   https://$APP_URL${NC}"
        echo ""
        echo -e "${YELLOW}📝 Next steps:${NC}"
        echo "   1. Configure GEMINI_API_KEY in Azure Portal"
        echo "   2. Set startup command if needed"
        echo "   3. Test the app on your browser/phone"
        echo ""
        echo -e "${YELLOW}💡 Tip: Use 'az webapp log tail' to view logs${NC}"
        
        # Ask to open in browser
        read -p "Open app in browser? (y/n) " open_browser
        if [ "$open_browser" == "y" ]; then
            if command -v xdg-open &> /dev/null; then
                xdg-open "https://$APP_URL"
            elif command -v open &> /dev/null; then
                open "https://$APP_URL"
            fi
        fi
    else
        echo ""
        echo -e "${RED}  ✗ Deployment failed${NC}"
        echo -e "${YELLOW}  Check the error messages above${NC}"
        echo -e "${YELLOW}  Or deploy manually via Azure Portal${NC}"
    fi
else
    echo -e "${YELLOW}  Deployment cancelled${NC}"
fi

echo ""
echo -e "${CYAN}📖 For more details, see DEPLOYMENT_GUIDE.md${NC}"
