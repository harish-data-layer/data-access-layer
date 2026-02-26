# TranAI DAL - Windows Startup Script

Write-Host "🚀 Starting TranAI Data Access Layer..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Docker
Write-Host "Step 1: Checking Docker..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    Write-Host "   Then run this script again." -ForegroundColor Yellow
    exit 1
}

# Step 2: Start Docker services
Write-Host ""
Write-Host "Step 2: Starting infrastructure services..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Infrastructure services started" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}

# Step 3: Wait for services
Write-Host ""
Write-Host "Step 3: Waiting for services to be healthy (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
Write-Host "✅ Services should be ready" -ForegroundColor Green

# Step 4: Generate Prisma client
Write-Host ""
Write-Host "Step 4: Generating Prisma client..." -ForegroundColor Yellow
npm run prisma:generate
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Prisma client generated" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to generate Prisma client" -ForegroundColor Red
    exit 1
}

# Step 5: Run migrations
Write-Host ""
Write-Host "Step 5: Running database migrations..." -ForegroundColor Yellow
npm run prisma:migrate dev -- --name init
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Database migrations completed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Migrations may have failed or already exist" -ForegroundColor Yellow
}

# Step 6: Start API server
Write-Host ""
Write-Host "Step 6: Starting API server..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 Setup complete! Starting development server..." -ForegroundColor Green
Write-Host ""
Write-Host "📊 Key URLs:" -ForegroundColor Cyan
Write-Host "   API: http://localhost:3000" -ForegroundColor White
Write-Host "   Health: http://localhost:3000/health" -ForegroundColor White
Write-Host "   Grafana: http://localhost:3001 (admin/admin)" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

npm run dev
