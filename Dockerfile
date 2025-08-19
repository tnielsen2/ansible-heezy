FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    openssh-client \
    sshpass \
    curl \
    unzip \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws

RUN pip install ansible boto3 botocore pywinrm requests requests-ntlm

WORKDIR /ansible

COPY . .

RUN ansible-galaxy collection install -r requirements.yml

ENTRYPOINT ["ansible-playbook"]
