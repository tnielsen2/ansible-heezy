# Ansible Automation Repository

Containerized Ansible automation with GitHub workflow dispatch integration for VM provisioning and application deployment.

## Quick Start

```bash
# Build container
docker build -t ansible-automation .

# Run bootstrap
docker run --rm --network host -v $PWD:/ansible -v ~/.ssh:/ansible/keys:ro ansible-automation -i inventory/hosts playbooks/linux-setup.yml
```

## Workflow Dispatch

Trigger via GitHub Actions with:
- `target_hosts`: Comma-separated host list
- `playbook`: `vm-bootstrap` or `custom-role`
- `custom_role`: `minecraft-server`, `web-server`, `game-server`
- `environment`: `dev`, `staging`, `prod`

## Roles

- **baseline**: OS detection and common tools (vim, curl, wget, Docker, AWS CLI, Prometheus exporters)
- **prometheus**: Full Prometheus server with auto-discovery of node exporters
- **github-runner**: Self-hosted GitHub Actions runner with Terraform support
- **tailscale**: Installs and registers Tailscale client automatically
- **prometheus-node-exporter**: Installs Prometheus node exporter for metrics collection
- **minecraft-server**: Java 17, Minecraft server, systemd service
- **web-server**: nginx, SSL setup, security hardening
- **game-server**: Windows game server with Steam CMD

## Infrastructure Setup

```bash
# Setup Tailscale and monitoring on all hosts
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.10" -f playbook="infrastructure" -f tailscale_auth_key="tskey-auth-xxx"

# Deploy custom role with infrastructure
gh workflow run ansible-provision.yml -f target_hosts="192.168.1.10" -f playbook="custom-role" -f custom_role="minecraft-server" -f tailscale_auth_key="tskey-auth-xxx"
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
[prometheus]
192.168.1.50

[runner]
192.168.1.60

[all]
192.168.1.10
192.168.1.20
```

## Monitoring

- Prometheus server runs on port 9090 on prometheus hosts
- Node exporter runs on port 9100 on all Linux hosts
- Windows exporter runs on port 9182 on Windows hosts
