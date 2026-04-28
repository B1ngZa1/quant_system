param(
    [switch]$DryRun = $false
)

$targets = @(
    ".venv",
    "backend/.pytest_cache",
    "backend/.mypy_cache",
    "backend/.ruff_cache",
    "backend/logs",
    "frontend/node_modules",
    "frontend/dist",
    "frontend/.vite",
    "logs"
)

foreach ($target in $targets) {
    $fullPath = Join-Path $PSScriptRoot $target
    if (Test-Path $fullPath) {
        if ($DryRun) {
            Write-Host "[DRY-RUN] Will remove: $fullPath"
        } else {
            Remove-Item -Path $fullPath -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "Removed: $fullPath"
        }
    }
}

Write-Host "Cleanup complete."
