#!/bin/bash
set -e

# Parameters
PLAYBOOK=$1
INVENTORY=${2:-"inventory/hosts.heezy"}
EXTRA_VARS=${3:-""}
RUNNER_ACCESS_KEY=$4
RUNNER_SECRET_KEY=$5
PROD_AWS_ACCOUNT_NUMBER=$6

# Get AWS credentials using runner credentials
ANSIBLE_CREDS=$(AWS_ACCESS_KEY_ID=$RUNNER_ACCESS_KEY \
AWS_SECRET_ACCESS_KEY=$RUNNER_SECRET_KEY \
AWS_DEFAULT_REGION=us-east-2 \
aws sts assume-role --role-arn arn:aws:iam::$PROD_AWS_ACCOUNT_NUMBER:role/GitHubActions-MultiRepo --role-session-name ansible-session)

# Set ECR registry
ECR_REGISTRY="$PROD_AWS_ACCOUNT_NUMBER.dkr.ecr.us-east-2.amazonaws.com"

# Login to ECR
export AWS_ACCESS_KEY_ID=$(echo $ANSIBLE_CREDS | jq -r '.Credentials.AccessKeyId')
export AWS_SECRET_ACCESS_KEY=$(echo $ANSIBLE_CREDS | jq -r '.Credentials.SecretAccessKey')
export AWS_SESSION_TOKEN=$(echo $ANSIBLE_CREDS | jq -r '.Credentials.SessionToken')

aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin $ECR_REGISTRY

# Pull container
docker pull $ECR_REGISTRY/ansible-automation:latest

# Run Ansible
docker run --rm --network host \
  -v $PWD:/ansible \
  -e AWS_ACCESS_KEY_ID=$(echo $ANSIBLE_CREDS | jq -r '.Credentials.AccessKeyId') \
  -e AWS_SECRET_ACCESS_KEY=$(echo $ANSIBLE_CREDS | jq -r '.Credentials.SecretAccessKey') \
  -e AWS_SESSION_TOKEN=$(echo $ANSIBLE_CREDS | jq -r '.Credentials.SessionToken') \
  -e AWS_DEFAULT_REGION=us-east-2 \
  ${EXTRA_VARS:+-e} ${EXTRA_VARS} \
  $ECR_REGISTRY/ansible-automation:latest \
  -i $INVENTORY \
  playbooks/$PLAYBOOK.yml