#!/bin/bash
set -e

# Parameters
PLAYBOOK=$1
INVENTORY=${2:-"inventory/hosts.heezy"}
EXTRA_VARS=${3:-""}
RUNNER_ACCESS_KEY=$4
RUNNER_SECRET_KEY=$5
PROD_AWS_ACCOUNT_NUMBER=$6

# Use provided AWS credentials directly (already from assumed role)
export AWS_ACCESS_KEY_ID=$RUNNER_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=$RUNNER_SECRET_KEY
export AWS_DEFAULT_REGION=us-east-2

# Run Ansible using local container
docker run --rm --network host \
  -v $PWD:/ansible \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  -e AWS_DEFAULT_REGION=us-east-2 \
  ${EXTRA_VARS:+-e} ${EXTRA_VARS} \
  ansible-automation:local \
  -i $INVENTORY \
  playbooks/$PLAYBOOK.yml