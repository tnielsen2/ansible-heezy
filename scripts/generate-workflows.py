#!/usr/bin/env python3

import yaml
import os
import glob
from pathlib import Path

def load_inventory():
    """Load and parse the YAML inventory file"""
    with open('inventory/hosts.yml', 'r') as f:
        return yaml.safe_load(f)

def get_playbooks():
    """Get list of playbooks from playbooks directory"""
    playbooks = []
    for playbook_file in glob.glob('playbooks/*.yml'):
        playbook_name = Path(playbook_file).stem
        playbooks.append(playbook_name)
    return playbooks

def get_host_groups(inventory):
    """Extract host groups from inventory"""
    groups = []
    if 'all' in inventory and 'children' in inventory['all']:
        for group_name, group_data in inventory['all']['children'].items():
            if 'hosts' in group_data and group_data['hosts']:
                groups.append(group_name)
    return groups

def generate_playbook_workflow(playbook_name, groups):
    """Generate workflow for a specific playbook"""
    
    # Create path filters for the playbook
    path_filters = [
        f"'inventory/**'",
        f"'roles/{playbook_name}/**'",
        f"'playbooks/{playbook_name}.yml'"
    ]
    
    # Add related role paths
    if playbook_name != 'baseline':
        path_filters.append("'roles/baseline/**'")
    
    workflow_content = f"""name: {playbook_name.title()} Playbook Execution

run-name: "{playbook_name.title()} execution by ${{{{ github.actor }}}} - ${{{{ github.sha }}}}"

on:
  push:
    branches: [main]
    paths:
{chr(10).join(f'      - {path}' for path in path_filters)}
  workflow_dispatch:
    inputs:
      target_groups:
        description: 'Target groups (comma-separated)'
        required: false
        type: string
        default: '{",".join(groups)}'
      build_image:
        description: 'Build new image'
        required: false
        type: boolean
        default: false
  schedule:
    - cron: '0 {hash(playbook_name) % 24} * * 0'  # Weekly on Sunday

permissions:
  id-token: write
  contents: read

concurrency:
  group: {playbook_name}-deployment
  cancel-in-progress: false

jobs:
  setup-aws:
    uses: ./.github/workflows/_setup-runner-aws-credentials.yml
    with:
      runner-type: ubuntu-latest
    secrets: inherit

  build-x86:
    if: (github.event_name == 'push' && github.ref == 'refs/heads/main') || github.event.inputs.build_image == 'true'
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::025066240222:role/GitHubActions-MultiRepo
          aws-region: us-east-2
      
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push x86 image
        run: |
          docker build --no-cache --platform linux/amd64 -t 025066240222.dkr.ecr.us-east-2.amazonaws.com/ansible-automation:main-x86 .
          docker push 025066240222.dkr.ecr.us-east-2.amazonaws.com/ansible-automation:main-x86

  deploy:
    needs: [setup-aws, build-x86]
    if: always() && !cancelled() && needs.build-x86.result != 'failure'
    runs-on: self-hosted
    container:
      image: 025066240222.dkr.ecr.us-east-2.amazonaws.com/ansible-automation:main-x86
      credentials:
        username: AWS
        password: ${{{{ needs.setup-aws.outputs.ecr-token }}}}
    timeout-minutes: 60
    steps:
      - name: Run {playbook_name} playbook
        env:
          AWS_ACCESS_KEY_ID: ${{{{ needs.setup-aws.outputs.runner-access-key }}}}
          AWS_SECRET_ACCESS_KEY: ${{{{ needs.setup-aws.outputs.runner-secret-key }}}}
          AWS_DEFAULT_REGION: us-east-2
        run: |
          # Mask initial credentials
          echo "::add-mask::$AWS_ACCESS_KEY_ID"
          echo "::add-mask::$AWS_SECRET_ACCESS_KEY"
          # Assume role using static runner credentials
          CREDS=$(aws sts assume-role --role-arn arn:aws:iam::025066240222:role/GitHubActions-MultiRepo --role-session-name ansible-session)
          
          # Extract and mask credentials
          ASSUMED_ACCESS_KEY=$(echo $CREDS | jq -r '.Credentials.AccessKeyId')
          ASSUMED_SECRET_KEY=$(echo $CREDS | jq -r '.Credentials.SecretAccessKey')
          ASSUMED_SESSION_TOKEN=$(echo $CREDS | jq -r '.Credentials.SessionToken')
          
          echo "::add-mask::$ASSUMED_ACCESS_KEY"
          echo "::add-mask::$ASSUMED_SECRET_KEY"
          echo "::add-mask::$ASSUMED_SESSION_TOKEN"
          
          # Export assumed role credentials
          export AWS_ACCESS_KEY_ID="$ASSUMED_ACCESS_KEY"
          export AWS_SECRET_ACCESS_KEY="$ASSUMED_SECRET_KEY"
          export AWS_SESSION_TOKEN="$ASSUMED_SESSION_TOKEN"
          
          # Run Ansible with assumed role credentials
          ANSIBLE_CONFIG=/ansible/ansible.cfg ANSIBLE_ROLES_PATH=/ansible/roles ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i /ansible/inventory/hosts.yml /ansible/playbooks/{playbook_name}.yml

  notify:
    if: always()
    needs: [deploy]
    uses: ./.github/workflows/_discord-notify.yml
    with:
      status: ${{{{ needs.deploy.result == 'success' && 'success' || 'failure' }}}}
      workflow-name: '{playbook_name.title()} Playbook Execution'
    secrets: inherit
"""
    
    return workflow_content

def generate_all_playbooks_workflow(playbooks):
    """Generate workflow that runs all playbooks"""
    
    workflow_content = f"""name: All Playbooks Execution

run-name: "All playbooks execution by ${{{{ github.actor }}}} - ${{{{ github.sha }}}}"

on:
  workflow_dispatch:
    inputs:
      build_image:
        description: 'Build new image'
        required: false
        type: boolean
        default: false
  schedule:
    - cron: '0 2 * * 6'  # Weekly on Saturday at 2 AM

permissions:
  id-token: write
  contents: read

concurrency:
  group: all-playbooks-deployment
  cancel-in-progress: false

jobs:
  setup-aws:
    uses: ./.github/workflows/_setup-runner-aws-credentials.yml
    with:
      runner-type: ubuntu-latest
    secrets: inherit

  build-x86:
    if: github.event.inputs.build_image == 'true'
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::025066240222:role/GitHubActions-MultiRepo
          aws-region: us-east-2
      
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push x86 image
        run: |
          docker build --no-cache --platform linux/amd64 -t 025066240222.dkr.ecr.us-east-2.amazonaws.com/ansible-automation:main-x86 .
          docker push 025066240222.dkr.ecr.us-east-2.amazonaws.com/ansible-automation:main-x86

  deploy:
    needs: [setup-aws, build-x86]
    if: always() && !cancelled() && needs.build-x86.result != 'failure'
    runs-on: self-hosted
    container:
      image: 025066240222.dkr.ecr.us-east-2.amazonaws.com/ansible-automation:main-x86
      credentials:
        username: AWS
        password: ${{{{ needs.setup-aws.outputs.ecr-token }}}}
    timeout-minutes: 120
    strategy:
      matrix:
        playbook: {playbooks}
      fail-fast: false
    steps:
      - name: Run ${{{{ matrix.playbook }}}} playbook
        env:
          AWS_ACCESS_KEY_ID: ${{{{ needs.setup-aws.outputs.runner-access-key }}}}
          AWS_SECRET_ACCESS_KEY: ${{{{ needs.setup-aws.outputs.runner-secret-key }}}}
          AWS_DEFAULT_REGION: us-east-2
        run: |
          # Mask initial credentials
          echo "::add-mask::$AWS_ACCESS_KEY_ID"
          echo "::add-mask::$AWS_SECRET_ACCESS_KEY"
          # Assume role using static runner credentials
          CREDS=$(aws sts assume-role --role-arn arn:aws:iam::025066240222:role/GitHubActions-MultiRepo --role-session-name ansible-session)
          
          # Extract and mask credentials
          ASSUMED_ACCESS_KEY=$(echo $CREDS | jq -r '.Credentials.AccessKeyId')
          ASSUMED_SECRET_KEY=$(echo $CREDS | jq -r '.Credentials.SecretAccessKey')
          ASSUMED_SESSION_TOKEN=$(echo $CREDS | jq -r '.Credentials.SessionToken')
          
          echo "::add-mask::$ASSUMED_ACCESS_KEY"
          echo "::add-mask::$ASSUMED_SECRET_KEY"
          echo "::add-mask::$ASSUMED_SESSION_TOKEN"
          
          # Export assumed role credentials
          export AWS_ACCESS_KEY_ID="$ASSUMED_ACCESS_KEY"
          export AWS_SECRET_ACCESS_KEY="$ASSUMED_SECRET_KEY"
          export AWS_SESSION_TOKEN="$ASSUMED_SESSION_TOKEN"
          
          # Run Ansible with assumed role credentials
          ANSIBLE_CONFIG=/ansible/ansible.cfg ANSIBLE_ROLES_PATH=/ansible/roles ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i /ansible/inventory/hosts.yml /ansible/playbooks/${{{{ matrix.playbook }}}}.yml

  notify:
    if: always()
    needs: [deploy]
    uses: ./.github/workflows/_discord-notify.yml
    with:
      status: ${{{{ needs.deploy.result == 'success' && 'success' || 'failure' }}}}
      workflow-name: 'All Playbooks Execution'
    secrets: inherit
"""
    
    return workflow_content

def update_terraform_triggered(playbooks):
    """Update terraform-triggered.yml with dynamic playbook options"""
    
    playbook_options = ['baseline'] + [p for p in playbooks if p != 'baseline']
    
    terraform_content = f"""name: Terraform Provisioning

run-name: "Terraform provisioning by ${{{{ github.actor }}}} - ${{{{ github.sha }}}}"

on:
  workflow_dispatch:
    inputs:
      target_hosts:
        description: 'Target hosts (comma-separated IPs or inventory group)'
        required: true
        type: string
      playbooks:
        description: 'Playbooks to execute'
        required: true
        type: choice
        options:
{chr(10).join(f'          - {playbook}' for playbook in playbook_options)}
        default: baseline

permissions:
  id-token: write
  contents: read

jobs:
  setup-aws:
    uses: ./.github/workflows/_setup-runner-aws-credentials.yml
    with:
      runner-type: ubuntu-latest
    secrets: inherit

  provision:
    needs: setup-aws
    runs-on: self-hosted
    container:
      image: 025066240222.dkr.ecr.us-east-2.amazonaws.com/ansible-automation:main-x86
      credentials:
        username: AWS
        password: ${{{{ needs.setup-aws.outputs.ecr-token }}}}
    timeout-minutes: 60
    steps:
      - name: Run playbook
        env:
          AWS_ACCESS_KEY_ID: ${{{{ needs.setup-aws.outputs.runner-access-key }}}}
          AWS_SECRET_ACCESS_KEY: ${{{{ needs.setup-aws.outputs.runner-secret-key }}}}
          AWS_DEFAULT_REGION: us-east-2
        run: |
          # Mask initial credentials
          echo "::add-mask::$AWS_ACCESS_KEY_ID"
          echo "::add-mask::$AWS_SECRET_ACCESS_KEY"
          # Assume role using static runner credentials
          CREDS=$(aws sts assume-role --role-arn arn:aws:iam::025066240222:role/GitHubActions-MultiRepo --role-session-name ansible-session)
          
          # Extract and mask credentials
          ASSUMED_ACCESS_KEY=$(echo $CREDS | jq -r '.Credentials.AccessKeyId')
          ASSUMED_SECRET_KEY=$(echo $CREDS | jq -r '.Credentials.SecretAccessKey')
          ASSUMED_SESSION_TOKEN=$(echo $CREDS | jq -r '.Credentials.SessionToken')
          
          echo "::add-mask::$ASSUMED_ACCESS_KEY"
          echo "::add-mask::$ASSUMED_SECRET_KEY"
          echo "::add-mask::$ASSUMED_SESSION_TOKEN"
          
          # Export assumed role credentials
          export AWS_ACCESS_KEY_ID="$ASSUMED_ACCESS_KEY"
          export AWS_SECRET_ACCESS_KEY="$ASSUMED_SECRET_KEY"
          export AWS_SESSION_TOKEN="$ASSUMED_SESSION_TOKEN"
          
          # Create dynamic inventory for target hosts
          mkdir -p /tmp/inventory
          TARGET_HOSTS="${{ github.event.inputs.target_hosts }}"
          PLAYBOOK="${{ github.event.inputs.playbooks }}"
          
          # Create YAML inventory
          cat > /tmp/inventory/dynamic_hosts.yml << EOF
          all:
            hosts:
          $(echo "$TARGET_HOSTS" | tr ',' '\\n' | while read host; do
            echo "      $host:"
            echo "        hostname: $host"
          done)
            vars:
              ansible_user: "{{{{ lookup('aws_secret', 'production/heezy/ubuntu/cloud-init-credentials', region='us-east-2') | from_json | json_query('username') }}}}"
              ansible_password: "{{{{ lookup('aws_secret', 'production/heezy/ubuntu/cloud-init-credentials', region='us-east-2') | from_json | json_query('password') }}}}"
              ansible_become_password: "{{{{ lookup('aws_secret', 'production/heezy/ubuntu/cloud-init-credentials', region='us-east-2') | from_json | json_query('password') }}}}"
          EOF
          
          # Run playbook
          echo "Running playbook: $PLAYBOOK"
          ANSIBLE_CONFIG=/ansible/ansible.cfg ANSIBLE_ROLES_PATH=/ansible/roles ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i /tmp/inventory/dynamic_hosts.yml /ansible/playbooks/$PLAYBOOK.yml
"""
    
    return terraform_content

def main():
    """Main function to generate all workflows"""
    
    # Load inventory and get playbooks
    inventory = load_inventory()
    playbooks = get_playbooks()
    groups = get_host_groups(inventory)
    
    print(f"Found playbooks: {playbooks}")
    print(f"Found groups: {groups}")
    
    # Create workflows directory if it doesn't exist
    os.makedirs('.github/workflows', exist_ok=True)
    
    # Generate individual playbook workflows
    for playbook in playbooks:
        workflow_content = generate_playbook_workflow(playbook, groups)
        filename = f'.github/workflows/playbook-{playbook}-execution.yml'
        
        with open(filename, 'w') as f:
            f.write(workflow_content)
        
        print(f"Generated: {filename}")
    
    # Generate all playbooks workflow
    all_workflow_content = generate_all_playbooks_workflow(playbooks)
    with open('.github/workflows/playbook-all-execution.yml', 'w') as f:
        f.write(all_workflow_content)
    
    print("Generated: .github/workflows/playbook-all-execution.yml")
    
    # Update terraform-triggered workflow
    terraform_content = update_terraform_triggered(playbooks)
    with open('.github/workflows/terraform-triggered.yml', 'w') as f:
        f.write(terraform_content)
    
    print("Updated: .github/workflows/terraform-triggered.yml")

if __name__ == "__main__":
    main()