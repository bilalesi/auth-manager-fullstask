#!/bin/bash
set -e  # exit on error
set -u  # exit on undefined variable
set -o pipefail  # exit on pipe failure


HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8000}

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}



run_migrations() {
    log_info "Running database migrations..."
    
    if alembic upgrade head; then
        log_info "Database migrations completed successfully"
    else
        log_error "Database migrations failed"
        exit 1
    fi
}


start_server() {
    log_info "Starting Auth Manager Service..."
    
    exec python -m app entrypoint --host $HOST --port $PORT
}

main() {

    log_info "Auth Manager Service Entrypoint"
    
    run_migrations
    start_server
}

trap 'log_warn "Received SIGTERM, shutting down gracefully..."; exit 0' SIGTERM
trap 'log_warn "Received SIGINT, shutting down gracefully..."; exit 0' SIGINT

main "$@"
