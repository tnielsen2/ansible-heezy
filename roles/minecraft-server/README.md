# Minecraft Server Role

Deploys dual Minecraft Bedrock servers using Docker Compose.

## Servers

- **Creative Server** (Port 19132): Creative mode with cheats enabled
- **Survival Server** (Port 19133): Survival mode, normal difficulty

## Data Location

- Creative data: `/opt/minecraft/data/`
- Survival data: `/opt/minecraft/survival-data/`

## Data Migration

To preserve existing data, copy your backup to the appropriate directories:

```bash
# Copy existing creative server data
sudo cp -r /path/to/backup/data/* /opt/minecraft/data/

# Copy existing survival server data  
sudo cp -r /path/to/backup/survival-data/* /opt/minecraft/survival-data/

# Set proper ownership
sudo chown -R 1000:1000 /opt/minecraft/data/
sudo chown -R 1000:1000 /opt/minecraft/survival-data/
```

## Usage

```bash
# Deploy minecraft servers
./run-ansible.sh -t local minecraft-server

# Check status
sudo systemctl status minecraft-servers
sudo docker compose -f /opt/minecraft/docker-compose.yml ps

# View logs
sudo docker logs minecraft-bds
sudo docker logs minecraft-survival
```

## Ports

- **19132/udp**: Creative server
- **19133/udp**: Survival server

Both ports are automatically opened in the firewall.