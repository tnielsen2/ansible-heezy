# Ansible Automation Repository

Containerized Ansible automation with GitHub workflow dispatch integration for VM provisioning and application deployment.

## Quick Start

### Local Development
```bash
# Build and push to ECR
./build.sh -a YOUR_AWS_ACCOUNT_NUMBER

# Run playbooks locally
./run-ansible.sh -a YOUR_AWS_ACCOUNT_NUMBER baseline
./run-ansible.sh -a YOUR_AWS_ACCOUNT_NUMBER -i inventory/dynamic_hosts custom-role --extra-vars "custom_role=minecraft-server"
```

### GitHub Workflows
Trigger via GitHub Actions with:
- `target_hosts`: Comma-separated host list (e.g., "192.168.1.19,192.168.1.32")
- `playbook`: `baseline`, `prometheus`, `github-runner`, `custom-role`
- `custom_role`: `minecraft-server`, `web-server`
- `environment`: `prod`

## Roles

- **baseline**: OS detection and package installation (Ubuntu/Windows/Talos support)
  - Common tools: vim, curl, wget, Docker, AWS CLI
  - Includes prometheus-node-exporter and tailscale
- **prometheus**: Containerized Prometheus server with auto-discovery
- **github-runner**: Self-hosted GitHub Actions runner with Terraform support
- **minecraft-server**: Containerized Minecraft Bedrock server
- **web-server**: nginx, SSL setup, security hardening
- **tailscale**: VPN client installation and registration
- **prometheus-node-exporter**: System metrics collection

## Infrastructure Setup

```bash
# Setup baseline infrastructure on all hosts
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.19,192.168.1.28,192.168.1.29" -f playbook="baseline"

# Deploy Prometheus server
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.19" -f playbook="prometheus"

# Setup GitHub runner
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.19" -f playbook="github-runner"

# Deploy custom applications
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.30" -f playbook="custom-role" -f custom_role="minecraft-server"
```

## Local Usage

### Build Container
```bash
# Build locally for development
./build-local.sh

# Build and test against all hosts
./build-local.sh --test

# Chain with local execution
./build-local.sh && ./run-ansible.sh -t local baseline
```

### Run Playbooks
```bash
# Local development (requires AWS credentials)
./run-ansible.sh -t local baseline

# With specific AWS profile
AWS_PROFILE=myprofile ./run-ansible.sh -t local baseline

# From ECR (requires AWS account)
./run-ansible.sh -a AWS_ACCOUNT baseline

# Custom inventory
./run-ansible.sh -t local -i inventory/custom_hosts prometheus

# With extra variables
./run-ansible.sh -t local custom-role --extra-vars "custom_role=minecraft-server"

# Different ECR tag
./run-ansible.sh -a AWS_ACCOUNT -t v1.0.0 baseline
```

## Workflows

### Terraform Triggered (`terraform-triggered.yml`)
Triggered by external Terraform CI with host IP inputs for immediate provisioning.

### Scheduled Maintenance (`scheduled-maintenance.yml`)
- **Baseline**: Weekly on Sundays at 3 AM UTC
- **Prometheus**: Weekly on Saturdays at 3 AM UTC

### Commit Triggered (`commit-triggered.yml`)
Automatically runs when changes are detected in:
- `inventory/**`
- `roles/baseline/**`, `roles/prometheus/**`, `roles/github-runner/**`
- Corresponding playbook files

## Inventory Groups

```ini
[management]
192.168.1.19 hostname=management

[testvm]
192.168.1.28 hostname=testvm1
192.168.1.29 hostname=testvm2

[minecraft]
192.168.1.30 hostname=minecraftvm2

[windows]
192.168.1.32 hostname=windows-vm

[prometheus]
192.168.1.19

[runner]
192.168.1.19

[linux:children]
management
testvm
minecraft
```

## AWS Secrets Configuration

### Ubuntu Credentials
```bash
aws secretsmanager create-secret \
  --name "production/heezy/ubuntu/cloud-init-credentials" \
  --secret-string '{"username": "trent", "password": "your_password"}' \
  --region us-east-2
```

### Windows Credentials
```bash
aws secretsmanager create-secret \
  --name "production/heezy/windows/administrator/credentials" \
  --secret-string '{"username": "Administrator", "password": "your_password"}' \
  --region us-east-2
```

### GitHub Runner Token
```bash
aws secretsmanager create-secret \
  --name "production/heezy/github/runner-token" \
  --secret-string '{"token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}' \
  --region us-east-2
```

### Runner AWS Credentials
```bash
aws secretsmanager create-secret \
  --name "production/heezy/github_runner/aws_credentials" \
  --secret-string '{"AWS_ACCESS_KEY_ID": "AKIA...", "AWS_SECRET_ACCESS_KEY": "xxx..."}' \
  --region us-east-2
```

## Monitoring

- Prometheus server runs on port 9090 on prometheus hosts
- Node exporter runs on port 9100 on all Linux hosts
- Windows exporter runs on port 9182 on Windows hosts
