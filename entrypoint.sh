#!/bin/bash
set -e

# Set default values from environment variables
ANSIBLE_HOST_KEY_CHECKING=${ANSIBLE_HOST_KEY_CHECKING:-False}
ANSIBLE_STDOUT_CALLBACK=${ANSIBLE_STDOUT_CALLBACK:-yaml}

# Export environment variables for Ansible
export ANSIBLE_HOST_KEY_CHECKING
export ANSIBLE_STDOUT_CALLBACK

# If TAILSCALE_AUTH_KEY is provided, set it for the playbook
if [ -n "$TAILSCALE_AUTH_KEY" ]; then
    export TAILSCALE_AUTH_KEY
fi

# If ENVIRONMENT is provided, set it for the playbook
if [ -n "$ENVIRONMENT" ]; then
    export ENVIRONMENT
fi

# If CUSTOM_ROLE is provided, set it for the playbook
if [ -n "$CUSTOM_ROLE" ]; then
    export CUSTOM_ROLE
fi

# If TARGET_HOSTS is provided, set it for the playbook
if [ -n "$TARGET_HOSTS" ]; then
    export TARGET_HOSTS
fi

# Execute ansible-playbook with all provided arguments
exec ansible-playbook "$@"