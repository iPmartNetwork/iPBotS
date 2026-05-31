#!/bin/bash
# iPBotS Database Migration Helper
# Usage: bash scripts/migrate.sh [create|upgrade|downgrade]

INSTALL_DIR="/opt/iPBotS"

case "${1:-help}" in
    create)
        echo "Creating new migration..."
        docker compose exec bot alembic revision --autogenerate -m "${2:-auto_migration}"
        ;;
    upgrade)
        echo "Upgrading database..."
        docker compose exec bot alembic upgrade head
        ;;
    downgrade)
        echo "Downgrading database..."
        docker compose exec bot alembic downgrade -1
        ;;
    *)
        echo "Usage: bash scripts/migrate.sh {create|upgrade|downgrade}"
        echo ""
        echo "Commands:"
        echo "  create [msg]  - Create new migration"
        echo "  upgrade       - Apply all pending migrations"
        echo "  downgrade     - Rollback last migration"
        ;;
esac
