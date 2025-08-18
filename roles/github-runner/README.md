# GitHub Runner Role

This role sets up a GitHub Actions self-hosted runner with all necessary tools for Terraform operations.

## Requirements

- Ubuntu/Debian Linux system
- AWS credentials configured for accessing Secrets Manager
- GitHub repository access

## AWS Secrets Manager Setup

Create a secret in AWS Secrets Manager with the following path and format:

**Secret Path:** `production/heezy/github/runner-token`

**Secret Format:**
```json
{
  "token": "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

To create the secret using AWS CLI:
```bash
aws secretsmanager create-secret \
  --name "production/heezy/github/runner-token" \
  --description "GitHub Personal Access Token for self-hosted runner" \
  --secret-string '{"token":"ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"}'
```

## GitHub Token Permissions

The GitHub Personal Access Token requires the following permissions:
- `repo` (Full control of private repositories)
- `admin:org` (Full control of orgs and teams, read and write org projects)

## Installed Components

- AWS CLI v2
- Docker CE with Buildx and Compose plugins
- GitHub CLI
- Terraform (latest from HashiCorp repository)
- GitHub Actions Runner
- Common development tools (curl, wget, git, jq, etc.)

## Usage

Add hosts to the `runner` group in your inventory:

```ini
[runner]
192.168.1.100 ansible_user=ubuntu
```

Run the playbook:
```bash
ansible-playbook -i inventory/hosts playbooks/github-runner.yml
```

## Service Management

The runner is installed as a systemd service and will start automatically on boot.

Check status:
```bash
sudo systemctl status actions.runner.tnielsen2-terraform-heezy.heezy-runner.service
```