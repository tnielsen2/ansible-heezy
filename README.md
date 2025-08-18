# Ansible Automation Repository

Containerized Ansible automation with GitHub workflow dispatch integration for VM provisioning and application deployment.

## Quick Start

### Local Development
```bash
# Build and test locally (no AWS required for build)
./build-local.sh --test

# Run specific playbooks locally (requires AWS credentials)
AWS_DEFAULT_PROFILE=myprofile ./run-ansible.sh -t local baseline
./run-ansible.sh -t local custom-role --extra-vars "custom_role=minecraft-server"
```

### GitHub Workflows
Trigger via GitHub Actions with:
- `target_hosts`: Comma-separated host list (e.g., "192.168.1.19,192.168.1.32")
- `playbook`: `baseline`, `prometheus`, `github-runner`, `tailscale`, `custom-role`
- `custom_role`: `minecraft-server`, `web-server`
- `environment`: `prod`

## Roles

- **baseline**: OS detection and package installation (Ubuntu/Windows/Talos support)
  - Ubuntu: Docker, AWS CLI, common tools, node-exporter, tailscale
  - Windows: Chocolatey, Docker Desktop, AWS CLI, common tools, windows-exporter, tailscale
  - Talos: Immutable OS verification
- **prometheus**: Containerized Prometheus server with persistent storage
- **github-runner**: Self-hosted GitHub Actions runner with Terraform support
- **minecraft-server**: Containerized Minecraft Bedrock server (Docker Compose)
- **web-server**: nginx, SSL setup, security hardening
- **tailscale**: VPN network connection (requires auth key)
- **prometheus-node-exporter**: System metrics collection for Linux hosts

## Infrastructure Setup

```bash
# Setup baseline infrastructure on all hosts
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.19,192.168.1.28,192.168.1.29" -f playbook="baseline"

# Deploy Prometheus server
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.19" -f playbook="prometheus"

# Setup GitHub runner
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.19" -f playbook="github-runner"

# Connect to Tailscale VPN
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.19,192.168.1.32" -f playbook="tailscale"

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

## Tailscale Setup

```bash
# Connect hosts to Tailscale VPN (requires auth key)
TAILSCALE_AUTH_KEY=tskey-auth-xxx ./run-ansible.sh -t local tailscale

# Via GitHub workflow
gh workflow run terraform-triggered.yml \
  -f target_hosts="192.168.1.19,192.168.1.32" \
  -f playbook="custom-role" \
  -f custom_role="tailscale" \
  -f tailscale_auth_key="tskey-auth-xxx"
```

## Monitoring

- **Prometheus server**: Port 9090 (containerized with persistent storage)
- **Node exporter**: Port 9100 on Linux hosts
- **Windows exporter**: Port 9182 on Windows hosts
- **Minecraft server**: Port 19132/udp (Bedrock protocol)

### Accessing Prometheus Web UI

```bash
# Direct access (if on same network)
http://192.168.1.19:9090

# Via Tailscale (after connecting hosts to VPN)
http://management:9090

# SSH tunnel for secure access
ssh -L 9090:localhost:9090 trent@192.168.1.19
# Then access: http://localhost:9090
```

## Network

- **Tailscale VPN**: Connects all hosts to private mesh network
- **Firewall**: UFW configured for required ports
- **SSH**: Password authentication via AWS Secrets Manager
- **WinRM**: NTLM authentication for Windows hosts
