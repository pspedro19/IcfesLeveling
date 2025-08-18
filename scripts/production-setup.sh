#!/bin/bash

# ICFES Leveling Production Server Setup Script
# Prepares a fresh server for production deployment

set -euo pipefail

# Configuration
LOG_FILE="/var/log/icfes-setup.log"
ICFES_USER="icfes"
DOCKER_COMPOSE_VERSION="2.20.2"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Update system
update_system() {
    log "🔄 Updating system packages..."
    
    apt-get update
    apt-get upgrade -y
    apt-get autoremove -y
    
    # Install essential packages
    apt-get install -y \
        curl \
        wget \
        git \
        vim \
        htop \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        fail2ban \
        ufw \
        certbot \
        python3-certbot-nginx \
        openssl \
        jq \
        net-tools
    
    log_success "System updated"
}

# Configure firewall
setup_firewall() {
    log "🔥 Configuring firewall..."
    
    # Reset UFW
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (adjust port if needed)
    ufw allow 22/tcp
    
    # Allow HTTP/HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow monitoring (restrict to monitoring network)
    ufw allow from 172.22.0.0/16 to any port 3000  # Grafana
    ufw allow from 172.22.0.0/16 to any port 9090  # Prometheus
    
    # Enable firewall
    ufw --force enable
    
    log_success "Firewall configured"
}

# Install Docker
install_docker() {
    log "🐳 Installing Docker..."
    
    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc || true
    
    # Add Docker repository
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Install Docker Compose standalone
    curl -L "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    log_success "Docker installed"
}

# Create icfes user
create_icfes_user() {
    log "👤 Creating ICFES user..."
    
    # Create user if not exists
    if ! id "$ICFES_USER" &>/dev/null; then
        useradd -m -s /bin/bash "$ICFES_USER"
        usermod -aG docker "$ICFES_USER"
        usermod -aG sudo "$ICFES_USER"
        
        # Create SSH directory
        mkdir -p "/home/$ICFES_USER/.ssh"
        chmod 700 "/home/$ICFES_USER/.ssh"
        chown "$ICFES_USER:$ICFES_USER" "/home/$ICFES_USER/.ssh"
        
        log "Created user: $ICFES_USER"
        log "⚠️ Please set up SSH keys and password for the $ICFES_USER user"
    else
        log "User $ICFES_USER already exists"
    fi
    
    log_success "User setup completed"
}

# Create directory structure
create_directories() {
    log "📁 Creating directory structure..."
    
    # Main directories
    mkdir -p /opt/icfes/{data,logs,backups,monitoring,ssl,config}
    mkdir -p /opt/icfes/data/{postgres,redis,clickhouse}
    mkdir -p /opt/icfes/monitoring/{prometheus,grafana,alertmanager,loki}
    mkdir -p /opt/icfes/logs/{nginx,application}
    mkdir -p /opt/icfes/backups/{database,volumes,config}
    
    # Application directories
    mkdir -p "/home/$ICFES_USER/icfes-leveling"
    
    # Set ownership
    chown -R "$ICFES_USER:$ICFES_USER" "/home/$ICFES_USER"
    chown -R "$ICFES_USER:docker" /opt/icfes
    
    # Set permissions
    chmod -R 755 /opt/icfes
    chmod -R 750 /opt/icfes/ssl
    chmod -R 700 /opt/icfes/backups
    
    log_success "Directory structure created"
}

# Configure SSL certificates
setup_ssl() {
    log "🔐 Setting up SSL certificates..."
    
    # Create self-signed certificates for development
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /opt/icfes/ssl/icfes.key \
        -out /opt/icfes/ssl/icfes.crt \
        -subj "/C=CO/ST=Bogota/L=Bogota/O=ICFES/CN=yourdomain.com" \
        2>/dev/null
    
    # Generate DH parameters for nginx
    openssl dhparam -out /opt/icfes/ssl/dhparam.pem 2048 2>/dev/null
    
    # Set permissions
    chmod 600 /opt/icfes/ssl/icfes.key
    chmod 644 /opt/icfes/ssl/icfes.crt
    chmod 644 /opt/icfes/ssl/dhparam.pem
    chown -R "$ICFES_USER:$ICFES_USER" /opt/icfes/ssl
    
    log_success "SSL certificates created"
    log "⚠️ Replace self-signed certificates with real ones from Let's Encrypt or your CA"
}

# Configure system limits
configure_limits() {
    log "⚙️ Configuring system limits..."
    
    # Create limits configuration
    cat > /etc/security/limits.d/icfes.conf << 'EOF'
# ICFES Leveling system limits
icfes soft nofile 65536
icfes hard nofile 65536
icfes soft nproc 32768
icfes hard nproc 32768

# Docker limits
root soft nofile 65536
root hard nofile 65536
EOF

    # Configure sysctl for performance
    cat > /etc/sysctl.d/99-icfes.conf << 'EOF'
# ICFES Leveling kernel parameters

# Network performance
net.core.somaxconn = 1024
net.core.netdev_max_backlog = 5000
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_congestion_control = bbr

# Memory management
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# File system
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288

# Security
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
EOF

    # Apply sysctl settings
    sysctl -p /etc/sysctl.d/99-icfes.conf
    
    log_success "System limits configured"
}

# Install monitoring tools
install_monitoring() {
    log "📊 Installing monitoring tools..."
    
    # Install Node Exporter
    curl -L https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-amd64.tar.gz | tar xz
    mv node_exporter-1.6.1.linux-amd64/node_exporter /usr/local/bin/
    rm -rf node_exporter-1.6.1.linux-amd64
    
    # Create node exporter user
    useradd --no-create-home --shell /bin/false node_exporter || true
    
    # Create systemd service
    cat > /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter \
    --collector.systemd \
    --collector.processes \
    --web.listen-address=127.0.0.1:9100

[Install]
WantedBy=multi-user.target
EOF

    # Start node exporter
    systemctl daemon-reload
    systemctl start node_exporter
    systemctl enable node_exporter
    
    log_success "Monitoring tools installed"
}

# Configure log rotation
setup_log_rotation() {
    log "📋 Setting up log rotation..."
    
    cat > /etc/logrotate.d/icfes << 'EOF'
/opt/icfes/logs/**/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 icfes icfes
    postrotate
        docker exec icfes_nginx_prod nginx -s reload 2>/dev/null || true
    endscript
}

/var/log/icfes/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 icfes icfes
}
EOF

    # Test logrotate configuration
    logrotate -d /etc/logrotate.d/icfes
    
    log_success "Log rotation configured"
}

# Configure fail2ban
setup_fail2ban() {
    log "🛡️ Configuring fail2ban..."
    
    # Create ICFES specific jail
    cat > /etc/fail2ban/jail.d/icfes.conf << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /opt/icfes/logs/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /opt/icfes/logs/nginx/error.log
maxretry = 10
findtime = 600
bantime = 600
EOF

    # Restart fail2ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    log_success "Fail2ban configured"
}

# Create deployment scripts
create_deployment_scripts() {
    log "📜 Creating deployment scripts..."
    
    # Create backup script
    cat > "/home/$ICFES_USER/backup.sh" << 'EOF'
#!/bin/bash
# ICFES Backup Script

BACKUP_DIR="/opt/icfes/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
docker exec icfes_postgres_prod pg_dump -U postgres icfes_production > "$BACKUP_DIR/database.sql"

# Backup volumes
docker run --rm -v postgres_prod_data:/source -v "$BACKUP_DIR":/backup alpine tar czf /backup/postgres_data.tar.gz -C /source .
docker run --rm -v redis_prod_data:/source -v "$BACKUP_DIR":/backup alpine tar czf /backup/redis_data.tar.gz -C /source .

# Backup configuration
cp -r /opt/icfes/config "$BACKUP_DIR/"

# Remove old backups (keep 7 days)
find /opt/icfes/backups -type d -name "20*" -mtime +7 -exec rm -rf {} +

echo "Backup completed: $BACKUP_DIR"
EOF

    # Create update script
    cat > "/home/$ICFES_USER/update.sh" << 'EOF'
#!/bin/bash
# ICFES Update Script

cd /home/icfes/icfes-leveling

# Pull latest code
git pull origin main

# Run deployment
./scripts/deploy-production.sh
EOF

    # Make scripts executable
    chmod +x "/home/$ICFES_USER/backup.sh"
    chmod +x "/home/$ICFES_USER/update.sh"
    chown "$ICFES_USER:$ICFES_USER" "/home/$ICFES_USER/"*.sh
    
    log_success "Deployment scripts created"
}

# Setup cron jobs
setup_cron() {
    log "⏰ Setting up cron jobs..."
    
    # Create cron jobs for icfes user
    cat > "/tmp/icfes-cron" << 'EOF'
# ICFES Leveling cron jobs

# Daily backup at 2 AM
0 2 * * * /home/icfes/backup.sh >> /var/log/icfes/backup.log 2>&1

# Clean old logs weekly
0 1 * * 0 find /opt/icfes/logs -name "*.log.*" -mtime +30 -delete

# Update SSL certificates monthly (if using Let's Encrypt)
0 3 1 * * /usr/bin/certbot renew --quiet --post-hook "docker exec icfes_nginx_prod nginx -s reload"

# System updates monthly
0 4 1 * * apt-get update && apt-get upgrade -y && apt-get autoremove -y
EOF

    # Install cron jobs
    crontab -u "$ICFES_USER" "/tmp/icfes-cron"
    rm "/tmp/icfes-cron"
    
    log_success "Cron jobs configured"
}

# Final security hardening
security_hardening() {
    log "🔒 Applying security hardening..."
    
    # Disable root login
    sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    
    # Configure SSH
    cat >> /etc/ssh/sshd_config << 'EOF'

# ICFES Security Configuration
Protocol 2
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers icfes
PasswordAuthentication no
PubkeyAuthentication yes
EOF

    # Restart SSH
    systemctl restart ssh
    
    # Set password policies
    apt-get install -y libpam-pwquality
    sed -i 's/# minlen = 8/minlen = 12/' /etc/security/pwquality.conf
    sed -i 's/# minclass = 0/minclass = 3/' /etc/security/pwquality.conf
    
    log_success "Security hardening completed"
}

# Print final instructions
print_instructions() {
    echo ""
    echo "=========================================="
    echo "🎉 ICFES Leveling Server Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Next Steps:"
    echo "1. Copy your SSH public key to /home/$ICFES_USER/.ssh/authorized_keys"
    echo "2. Test SSH login as $ICFES_USER user"
    echo "3. Clone the ICFES Leveling repository to /home/$ICFES_USER/icfes-leveling"
    echo "4. Configure production environment variables"
    echo "5. Obtain SSL certificates from Let's Encrypt or your CA"
    echo "6. Run the deployment script"
    echo ""
    echo "Important Files:"
    echo "- Application: /home/$ICFES_USER/icfes-leveling/"
    echo "- Data: /opt/icfes/data/"
    echo "- Logs: /opt/icfes/logs/"
    echo "- Backups: /opt/icfes/backups/"
    echo "- SSL: /opt/icfes/ssl/"
    echo ""
    echo "Monitoring:"
    echo "- Node Exporter: http://localhost:9100/metrics"
    echo "- System logs: journalctl -u icfes-*"
    echo ""
    echo "Security:"
    echo "- Firewall status: ufw status"
    echo "- Fail2ban status: fail2ban-client status"
    echo "- SSH config: /etc/ssh/sshd_config"
    echo ""
    echo "⚠️ Remember to:"
    echo "- Set strong passwords"
    echo "- Configure proper SSL certificates"
    echo "- Review and customize security settings"
    echo "- Set up monitoring alerts"
    echo "=========================================="
}

# Main function
main() {
    log "🚀 Starting ICFES Leveling production server setup..."
    
    check_root
    update_system
    setup_firewall
    install_docker
    create_icfes_user
    create_directories
    setup_ssl
    configure_limits
    install_monitoring
    setup_log_rotation
    setup_fail2ban
    create_deployment_scripts
    setup_cron
    security_hardening
    
    log_success "Server setup completed successfully!"
    print_instructions
}

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi