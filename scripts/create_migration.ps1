if (-not $args[0]) {
    Write-Host "Usage: .\migration.ps1 <migration_name>"
    exit
}

$migration = $args[0]

docker-compose run --rm web sh -c "alembic revision -m `"$migration`" --autogenerate"

Write-Host "Migration '$migration' has been created."
