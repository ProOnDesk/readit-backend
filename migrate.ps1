if (-not $args[0]) {
    Write-Host "Usage: .\migration.ps1 <migration_name>"
    exit
}

$migration = $args[0]

docker-compose run --rm web sh -c "alembic revision -m `"$migration`" --autogenerate && alembic upgrade head"

Write-Host "Migration '$migration' has been created and applied."

Write-Host "Press Enter to close..."
[void][System.Console]::ReadLine()
