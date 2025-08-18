#!/bin/bash
set -e

# Configuration
AWS_REGION="us-east-2"
ECR_REPOSITORY="ansible-automation"
CONTAINER_TAG="latest"
LOCAL_IMAGE="ansible-automation"

# Help function
show_help() {
    cat << EOF
Usage: $0 [OPTIONS] PLAYBOOK [ANSIBLE_ARGS...]

Run Ansible playbooks using containerized automation from ECR.

OPTIONS:
    -h, --help              Show this help message
    -t, --tag TAG          Container tag (default: latest)
    -r, --region REGION    AWS region (default: us-east-2)
    -a, --account ACCOUNT  AWS account number (required)
    -i, --inventory FILE   Inventory file (default: inventory/hosts.heezy)

EXAMPLES:
    $0 -a 123456789012 baseline
    $0 -a 123456789012 -i inventory/dynamic_hosts custom-role
    $0 -a 123456789012 prometheus --extra-vars "prometheus_version=v2.47.0"

EOF
}

# Parse arguments
INVENTORY="inventory/hosts.heezy"
AWS_ACCOUNT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--tag)
            CONTAINER_TAG="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -a|--account)
            AWS_ACCOUNT="$2"
            shift 2
            ;;
        -i|--inventory)
            INVENTORY="$2"
            shift 2
            ;;
        -*)
            echo "Unknown option: $1" >&2
            show_help
            exit 1
            ;;
        *)
            PLAYBOOK="$1"
            shift
            ANSIBLE_ARGS="$@"
            break
            ;;
    esac
done

# Validate required arguments
if [[ -z "$PLAYBOOK" ]]; then
    echo "Error: PLAYBOOK is required" >&2
    show_help
    exit 1
fi

# Check if using local container
if [[ "$CONTAINER_TAG" == "local" ]]; then
    FULL_IMAGE_NAME="${LOCAL_IMAGE}:${CONTAINER_TAG}"
else
    if [[ -z "$AWS_ACCOUNT" ]]; then
        echo "Error: AWS account number is required (-a/--account) for ECR images" >&2
        show_help
        exit 1
    fi
    ECR_REGISTRY="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    FULL_IMAGE_NAME="${ECR_REGISTRY}/${ECR_REPOSITORY}:${CONTAINER_TAG}"
fi

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

# Handle container source
if [[ "$CONTAINER_TAG" == "local" ]]; then
    log "📦 Using local container: ${LOCAL_IMAGE}:${CONTAINER_TAG}"
    if ! docker image inspect "$FULL_IMAGE_NAME" >/dev/null 2>&1; then
        echo "Error: Local image not found. Run ./build-local.sh first" >&2
        exit 1
    fi
    success "Local container found"
else
    log "🔐 Authenticating with AWS ECR..."
    log "Registry: $ECR_REGISTRY"
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_REGISTRY"
    success "ECR authentication successful"
    
    log "📦 Pulling Ansible container: ${ECR_REPOSITORY}:${CONTAINER_TAG}"
    docker pull "$FULL_IMAGE_NAME"
    success "Container pulled successfully"
fi

log "🚀 Running Ansible playbook: $PLAYBOOK"
log "Inventory: $INVENTORY"
log "Arguments: $ANSIBLE_ARGS"

# Pass through AWS credentials and config
AWS_MOUNT_ARGS=""
if [[ -d "$HOME/.aws" ]]; then
    AWS_MOUNT_ARGS="-v $HOME/.aws:/root/.aws:ro"
    log "Mounting AWS credentials from ~/.aws"
fi

docker run --rm --network host \
    -v "$PWD:/ansible" \
    $AWS_MOUNT_ARGS \
    -e AWS_DEFAULT_REGION="$AWS_REGION" \
    -e AWS_PROFILE \
    -e AWS_DEFAULT_PROFILE \
    -e AWS_ACCESS_KEY_ID \
    -e AWS_SECRET_ACCESS_KEY \
    -e AWS_SESSION_TOKEN \
    "$FULL_IMAGE_NAME" \
    -i "$INVENTORY" \
    "playbooks/${PLAYBOOK}.yml" \
    $ANSIBLE_ARGS

if [[ $? -eq 0 ]]; then
    success "Ansible playbook completed successfully"
else
    error "Ansible playbook failed"
    exit 1
fi