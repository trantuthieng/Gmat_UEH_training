#!/usr/bin/env pwsh
# Auto Deploy Script for GMAT Training System
# Usage: .\deploy.ps1

Write-Host "🚀 GMAT Training System - Auto Deploy Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$REPO_URL = "https://github.com/trantuthieng/Gmat_UEH_training.git"
$APP_NAME = "gmat-ueh-training"
$RESOURCE_GROUP = "gmat-rg"
$LOCATION = "southeastasia"
$RUNTIME = "PYTHON:3.11"
$SKU = "B1"

# Step 1: Check if git is initialized
Write-Host "📝 Step 1: Checking Git repository..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    Write-Host "  Initializing Git repository..." -ForegroundColor Green
    git init
    git branch -M main
} else {
    Write-Host "  ✓ Git repository already initialized" -ForegroundColor Green
}

# Step 2: Check remote
Write-Host ""
Write-Host "📝 Step 2: Setting up remote repository..." -ForegroundColor Yellow
$remotes = git remote
if ($remotes -notcontains "origin") {
    Write-Host "  Adding remote origin..." -ForegroundColor Green
    git remote add origin $REPO_URL
} else {
    Write-Host "  ✓ Remote origin already configured" -ForegroundColor Green
}

# Step 3: Add and commit files
Write-Host ""
Write-Host "📝 Step 3: Committing changes..." -ForegroundColor Yellow
git add .
$commitMessage = "Auto deploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
git commit -m $commitMessage
Write-Host "  ✓ Changes committed" -ForegroundColor Green

# Step 4: Push to GitHub
Write-Host ""
Write-Host "📝 Step 4: Pushing to GitHub..." -ForegroundColor Yellow
try {
    git push -u origin main
    Write-Host "  ✓ Code pushed to GitHub successfully" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Push failed. You may need to:" -ForegroundColor Red
    Write-Host "     1. Set up GitHub authentication (Personal Access Token)" -ForegroundColor Red
    Write-Host "     2. Or use: gh auth login" -ForegroundColor Red
    Write-Host ""
    $continue = Read-Host "Continue with Azure deployment? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}

# Step 5: Check if Azure CLI is installed
Write-Host ""
Write-Host "📝 Step 5: Checking Azure CLI..." -ForegroundColor Yellow
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "  ✓ Azure CLI installed: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Azure CLI not found" -ForegroundColor Red
    Write-Host "  Please install from: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Alternative: Deploy manually via Azure Portal" -ForegroundColor Yellow
    Write-Host "   See DEPLOYMENT_GUIDE.md for instructions" -ForegroundColor Yellow
    exit
}

# Step 6: Login to Azure
Write-Host ""
Write-Host "📝 Step 6: Azure Login..." -ForegroundColor Yellow
$loginCheck = az account show --output none 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Opening browser for Azure login..." -ForegroundColor Green
    az login
} else {
    Write-Host "  ✓ Already logged in to Azure" -ForegroundColor Green
}

# Step 7: Deploy to Azure
Write-Host ""
Write-Host "📝 Step 7: Deploying to Azure App Service..." -ForegroundColor Yellow
Write-Host "  App Name: $APP_NAME" -ForegroundColor Cyan
Write-Host "  Resource Group: $RESOURCE_GROUP" -ForegroundColor Cyan
Write-Host "  Location: $LOCATION" -ForegroundColor Cyan
Write-Host ""

$deploy = Read-Host "Continue with deployment? (y/n)"
if ($deploy -eq "y") {
    Write-Host "  Deploying... (this may take 3-5 minutes)" -ForegroundColor Green
    
    az webapp up `
        --name $APP_NAME `
        --resource-group $RESOURCE_GROUP `
        --runtime $RUNTIME `
        --sku $SKU `
        --location $LOCATION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "  ✓ Deployment successful!" -ForegroundColor Green
        
        # Step 8: Get app URL
        Write-Host ""
        Write-Host "📝 Step 8: Getting app URL..." -ForegroundColor Yellow
        $appUrl = az webapp show --name $APP_NAME --resource-group $RESOURCE_GROUP --query defaultHostName -o tsv
        
        Write-Host ""
        Write-Host "=============================================" -ForegroundColor Cyan
        Write-Host "✨ Deployment Complete!" -ForegroundColor Green
        Write-Host "=============================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📱 Your app is live at:" -ForegroundColor Yellow
        Write-Host "   https://$appUrl" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "📝 Next steps:" -ForegroundColor Yellow
        Write-Host "   1. Configure GEMINI_API_KEY in Azure Portal" -ForegroundColor White
        Write-Host "   2. Set startup command if needed" -ForegroundColor White
        Write-Host "   3. Test the app on your browser/phone" -ForegroundColor White
        Write-Host ""
        Write-Host "💡 Tip: Use az webapp log tail to view logs" -ForegroundColor Yellow
        
        # Ask to open in browser
        $openBrowser = Read-Host "Open app in browser? (y/n)"
        if ($openBrowser -eq "y") {
            Start-Process "https://$appUrl"
        }
    } else {
        Write-Host ""
        Write-Host "  ✗ Deployment failed" -ForegroundColor Red
        Write-Host "  Check the error messages above" -ForegroundColor Yellow
        Write-Host "  Or deploy manually via Azure Portal" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Deployment cancelled" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📖 For more details, see DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
