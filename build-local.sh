#!/bin/bash
set -e

# Configuration
IMAGE_NAME="ansible-automation"
CONTAINER_TAG="local"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Parse arguments
RUN_TEST=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            CONTAINER_TAG="$2"
            shift 2
            ;;
        --test)
            RUN_TEST=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [-t TAG] [--test]"
            echo "  -t, --tag      Container tag (default: local)"
            echo "  --test         Run baseline playbook against all hosts after build"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log "🏗️  Building Ansible automation container locally..."
log "Image: $IMAGE_NAME:$CONTAINER_TAG"

log "📦 Building Docker image..."
docker build -t "${IMAGE_NAME}:${CONTAINER_TAG}" .
success "Docker image built successfully"

log "🏷️  Tagging additional versions..."
SHORT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

if [[ "$SHORT_COMMIT" != "unknown" ]]; then
    docker tag "${IMAGE_NAME}:${CONTAINER_TAG}" "${IMAGE_NAME}:${SHORT_COMMIT}"
    success "Tagged: $SHORT_COMMIT"
fi

if [[ "$BRANCH_NAME" != "unknown" && "$BRANCH_NAME" != "HEAD" ]]; then
    docker tag "${IMAGE_NAME}:${CONTAINER_TAG}" "${IMAGE_NAME}:${BRANCH_NAME}"
    success "Tagged: $BRANCH_NAME"
fi

success "🎉 Local build completed successfully!"
log "Image available locally: ${IMAGE_NAME}:${CONTAINER_TAG}"

# Run test if requested
if [[ "$RUN_TEST" == "true" ]]; then
    log "🧪 Running test against all hosts..."
    if [[ -f "./run-ansible.sh" ]]; then
        chmod +x ./run-ansible.sh
        ./run-ansible.sh -t local baseline
        if [[ $? -eq 0 ]]; then
            success "Test completed successfully!"
        else
            error "Test failed!"
            exit 1
        fi
    else
        error "run-ansible.sh not found"
        exit 1
    fi
fi