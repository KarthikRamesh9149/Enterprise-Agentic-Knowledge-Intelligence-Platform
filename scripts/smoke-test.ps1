$ErrorActionPreference = "Stop"
$base = $env:API_URL
if (-not $base) { $base = "http://localhost:8000" }
$health = Invoke-RestMethod "$base/health"
if ($health.status -ne "ok") { throw "Health check failed" }
Write-Host "Smoke test passed against $base"

