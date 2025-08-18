FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    openssh-client \
    sshpass \
    && rm -rf /var/lib/apt/lists/*

RUN pip install ansible boto3 botocore

WORKDIR /ansible

COPY . .

RUN ansible-galaxy collection install -r requirements.yml

ENTRYPOINT ["ansible-playbook"]
