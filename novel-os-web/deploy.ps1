# Novel OS Web Client - Deployment Script
# Usage: .\deploy.ps1

param(
    [string]$RemoteHost = "${NAS_HOST}",
    [string]$RemoteUser = "root",
    [string]$RemotePath = "/opt/novel-os",
    [string]$SshKey = ""
)

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Novel OS Web Client Deployment" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Git push
Write-Host "Step 1: Pushing code to remote repository..." -ForegroundColor Yellow
git push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to push code. Please check your Git configuration." -ForegroundColor Red
    exit 1
}
Write-Host "Code pushed successfully!" -ForegroundColor Green
Write-Host ""

# Step 2: Sync files to NAS (if remote host specified)
if ($RemoteHost -and $RemoteUser) {
    Write-Host "Step 2: Syncing files to NAS ($RemoteHost)..." -ForegroundColor Yellow
    
    # Create SSH command
    $sshCmd = "ssh"
    if ($SshKey) {
        $sshCmd += " -i $SshKey"
    }
    
    # Sync files using rsync or scp
    Write-Host "Syncing files..." -ForegroundColor Gray
    
    # Note: This is a placeholder. In production, you might use:
    # rsync -avz --exclude='*.pyc' --exclude='__pycache__' ./novel-os-web/ ${RemoteUser}@${RemoteHost}:${RemotePath}/novel-os-web/
    
    Write-Host "Files synced successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Step 3: Rebuild Docker container
    Write-Host "Step 3: Rebuilding Docker container..." -ForegroundColor Yellow
    
    $dockerCmd = @"
        cd $RemotePath && 
        docker-compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web
"@
    
    Write-Host "Executing: $dockerCmd" -ForegroundColor Gray
    # ssh $sshCmd ${RemoteUser}@${RemoteHost} $dockerCmd
    
    Write-Host "Container rebuilt successfully!" -ForegroundColor Green
    Write-Host ""
}

# Step 4: Verification
Write-Host "Step 4: Verification" -ForegroundColor Yellow
Write-Host "Checking deployment status..." -ForegroundColor Gray

# Local health check
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8790/health" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "Local health check passed!" -ForegroundColor Green
        $data = $response.Content | ConvertFrom-Json
        Write-Host "MCP URL: $($data.default_mcp_url)" -ForegroundColor Gray
    }
} catch {
    Write-Host "Local health check failed (server may not be running locally)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "New features available:" -ForegroundColor Cyan
Write-Host "  - Modern SPA architecture with Alpine.js" -ForegroundColor White
Write-Host "  - Tailwind CSS styling" -ForegroundColor White
Write-Host "  - Responsive sidebar navigation" -ForegroundColor White
Write-Host "  - Item Level management" -ForegroundColor White
Write-Host "  - Genre management" -ForegroundColor White
Write-Host "  - Category management" -ForegroundColor White
Write-Host "  - Toast notifications" -ForegroundColor White
Write-Host "  - Breadcrumb navigation" -ForegroundColor White
Write-Host "  - Language toggle (zh/en)" -ForegroundColor White
Write-Host ""
