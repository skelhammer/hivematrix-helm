# HiveMatrix Quick Reference

**Last Updated:** 2025-11-22
**Purpose:** Quick troubleshooting reference for future-you at 2 AM

---

## 🌐 Service URLs

### Production (via Nexus - HTTPS)
```
https://YOUR_SERVER:443/
```

All services accessed through Nexus proxy (single entry point).

### Direct Access (Debugging Only - HTTP)
**⚠️ Only accessible on localhost (127.0.0.1)**

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| **Nexus** | 443 | https://localhost:443 | Gateway/Proxy (HTTPS) |
| **Core** | 5000 | http://localhost:5000 | Auth & JWT minting |
| **Beacon** | 5001 | http://localhost:5001 | Ticket dashboard |
| **Helm** | 5004 | http://localhost:5004 | Service orchestration |
| **Codex** | 5010 | http://localhost:5010 | Master data (companies, contacts, assets) |
| **KnowledgeTree** | 5020 | http://localhost:5020 | Knowledge base (Neo4j) |
| **Ledger** | 5030 | http://localhost:5030 | Billing engine |
| **Brainhair** | 5050 | http://localhost:5050 | AI assistant with PHI filtering |
| **Keycloak** | 8080 | http://localhost:8080 | Identity provider (OAuth2) |

---

## 🔑 Default Credentials

### Keycloak Admin
```
Username: admin
Password: admin
```
**⚠️ Change in production!**

### PostgreSQL
```
User: postgres
Password: [set during installation]
```

### Database Users (per service)
```
User: [service]_user
Password: [see instance/configs/master_config.json]
```

---

## 📁 Important Directories

| Path | Description |
|------|-------------|
| `~/hivematrix/hivematrix-helm/instance/configs/` | Master configuration files |
| `~/hivematrix/hivematrix-helm/logs/` | Service logs (stdout/stderr) |
| `/var/backups/hivematrix/` | Automated daily backups (30-day retention) |
| `/var/lib/postgresql/[version]/main/` | PostgreSQL database files |
| `/var/lib/neo4j/` | Neo4j database files (KnowledgeTree) |

---

## 🗄️ Database Names

| Database | Service | Type |
|----------|---------|------|
| `core_db` | Core | PostgreSQL |
| `codex_db` | Codex | PostgreSQL |
| `ledger_db` | Ledger | PostgreSQL |
| `brainhair_db` | Brainhair | PostgreSQL |
| `helm_db` | Helm | PostgreSQL |
| `knowledgetree` | KnowledgeTree | Neo4j |

---

## ⚡ Quick Commands

### Platform Control

```bash
# Start entire platform
cd ~/hivematrix/hivematrix-helm
./start.sh

# Stop entire platform
./stop.sh

# Restart everything
./stop.sh && ./start.sh

# Check service status
source pyenv/bin/activate
python cli.py status

# Start individual service
python cli.py start codex

# Stop individual service
python cli.py stop codex

# Restart individual service
python cli.py restart codex
```

### View Logs

```bash
cd ~/hivematrix/hivematrix-helm
source pyenv/bin/activate

# View recent logs from specific service
python logs_cli.py codex --tail 50

# View errors only
python logs_cli.py codex --level ERROR --tail 100

# View all services
python logs_cli.py --tail 30

# Watch logs in real-time (use in separate terminal)
watch -n 2 'python logs_cli.py codex --tail 20'
```

### Backup & Restore

```bash
# View backup status (systemd timer)
systemctl status hivematrix-backup.timer
systemctl list-timers | grep hivematrix

# View backup logs
journalctl -u hivematrix-backup.service -n 50

# Manual backup
sudo systemctl stop neo4j
sudo /usr/local/bin/backup-hivematrix.sh
sudo systemctl start neo4j

# List backups
ls -lh /var/backups/hivematrix/

# Restore from backup
cd ~/hivematrix/hivematrix-helm
./stop.sh
sudo systemctl stop neo4j
sudo python3 restore.py /var/backups/hivematrix/backup_YYYY-MM-DD_HH-MM-SS.tar.gz
./start.sh
sudo systemctl start neo4j
```

### Database Access

```bash
# PostgreSQL command line
sudo -u postgres psql codex_db

# List all databases
sudo -u postgres psql -l

# Neo4j browser (if running)
# Open: http://localhost:7474

# Neo4j command line
sudo -u neo4j cypher-shell
```

### Test Authenticated Endpoints

```bash
cd ~/hivematrix/hivematrix-helm
source pyenv/bin/activate

# Generate test JWT token (24-hour expiration)
TOKEN=$(python create_test_token.py 2>/dev/null)

# Test endpoint with token
curl -H "Authorization: Bearer $TOKEN" http://localhost:5010/codex/api/companies

# Test with pretty JSON output
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:5010/codex/api/companies | jq

# Test health endpoints (no auth required)
curl http://localhost:5000/health | jq
curl http://localhost:5010/health | jq
```

### Health Checks

```bash
# Check all service health
for port in 5000 5001 5004 5010 5020 5030 5050; do
  echo "Port $port:"
  curl -s http://localhost:$port/health | jq -r '.service + ": " + .status'
done

# Check specific service with details
curl http://localhost:5010/health | jq

# Check Nexus health (main entry point)
curl -k https://localhost:443/health | jq
```

### Security Audit

```bash
cd ~/hivematrix/hivematrix-helm

# Run port binding audit
python3 security_audit.py --audit

# Generate firewall rules (for production)
python3 security_audit.py --generate-firewall

# Apply firewall rules (production only)
sudo bash secure_firewall.sh

# Verify firewall status
sudo ufw status numbered
```

### Configuration Management

```bash
cd ~/hivematrix/hivematrix-helm
source pyenv/bin/activate

# Sync all service configurations
python config_manager.py sync-all

# Update service registry
python install_manager.py update-config

# View master configuration
cat instance/configs/master_config.json | jq
```

---

## 🔧 Troubleshooting

### Service Won't Start

**Check logs:**
```bash
python logs_cli.py [service] --tail 50
python logs_cli.py [service] --level ERROR
```

**Check if port is already in use:**
```bash
netstat -tlnp | grep [port]
# Example: netstat -tlnp | grep 5010
```

**Check database connection:**
```bash
sudo -u postgres psql -l
# Verify database exists
```

**Check PostgreSQL is running:**
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql  # if stopped
```

**Check service status:**
```bash
python cli.py status
```

---

### Database Errors

**Can't connect to database:**
```bash
# 1. Check PostgreSQL is running
sudo systemctl status postgresql

# 2. Verify database exists
sudo -u postgres psql -l

# 3. Check connection string
cat instance/[service].conf

# 4. Test connection manually
sudo -u postgres psql -d codex_db -c "SELECT 1;"
```

**Database doesn't exist:**
```bash
# Recreate database for service
cd ~/hivematrix/hivematrix-[service]
source pyenv/bin/activate
python init_db.py
```

---

### Authentication Failed

**User can't log in:**
```bash
# 1. Check Keycloak is running
curl http://localhost:8080
systemctl status keycloak  # if using systemd

# 2. Check Core is running
curl http://localhost:5000/health

# 3. Check Nexus is running
curl -k https://localhost:443/health

# 4. Clear browser cookies and try again
```

**JWT token validation failing:**
```bash
# Check Core JWT endpoint
curl http://localhost:5000/.well-known/jwks.json

# Generate test token to verify Core is minting correctly
cd ~/hivematrix/hivematrix-helm
source pyenv/bin/activate
python create_test_token.py
```

---

### Health Check Shows "Degraded"

**Check which component is degraded:**
```bash
curl http://localhost:5010/health | jq
# Look at .checks.database, .checks.disk, .checks.dependencies
```

**If database is degraded:**
```bash
sudo systemctl status postgresql
python logs_cli.py [service] --level ERROR
```

**If disk is degraded:**
```bash
df -h  # Check disk usage
# Clean up old backups if needed
sudo find /var/backups/hivematrix -mtime +30 -delete
```

**If dependency is degraded:**
```bash
# Check the dependency service health
curl http://localhost:5000/health | jq  # Core
curl http://localhost:5010/health | jq  # Codex
```

---

### Service Shows "Not Running" in Health Dashboard

**Start the service:**
```bash
cd ~/hivematrix/hivematrix-helm
source pyenv/bin/activate
python cli.py start [service]
```

**If service crashes immediately:**
```bash
# Check logs for errors
python logs_cli.py [service] --tail 100 --level ERROR

# Common issues:
# - Port already in use
# - Database not accessible
# - Configuration file missing
# - Dependency not running
```

---

### Nexus Proxy Errors

**502 Bad Gateway:**
```bash
# Backend service is down
python cli.py status  # Check which service is down
python cli.py start [service]
```

**Connection refused:**
```bash
# Nexus itself is down
cd ~/hivematrix/hivematrix-nexus
source pyenv/bin/activate
python run.py  # Check for errors
```

**404 Not Found:**
```bash
# Service route not configured
cat ~/hivematrix/hivematrix-helm/instance/configs/services.json
# Verify service is registered
```

---

### Neo4j Issues (KnowledgeTree)

**Neo4j won't start:**
```bash
sudo systemctl status neo4j
sudo journalctl -u neo4j -n 50

# Check disk space (Neo4j needs space)
df -h

# Restart Neo4j
sudo systemctl restart neo4j
```

**Can't connect to Neo4j:**
```bash
# Check if running
sudo systemctl status neo4j

# Check port
netstat -tlnp | grep 7687  # Bolt protocol
netstat -tlnp | grep 7474  # HTTP

# Test connection
curl http://localhost:7474
```

---

## 📊 Common Checks

### All Services Running?
```bash
cd ~/hivematrix/hivematrix-helm
source pyenv/bin/activate
python cli.py status
```

### All Services Healthy?
```bash
for port in 5000 5001 5004 5010 5020 5030 5050; do
  status=$(curl -s http://localhost:$port/health | jq -r '.status')
  service=$(curl -s http://localhost:$port/health | jq -r '.service')
  echo "$service: $status"
done
```

### Disk Space OK?
```bash
df -h
# Watch for /var/backups/hivematrix/ and database directories
```

### Recent Errors?
```bash
cd ~/hivematrix/hivematrix-helm
source pyenv/bin/activate
python logs_cli.py --level ERROR --tail 50
```

### Backups Running?
```bash
systemctl status hivematrix-backup.timer
ls -lht /var/backups/hivematrix/ | head -5
```

---

## 🚨 Emergency Procedures

### Complete System Recovery

**If everything is broken:**
```bash
# 1. Stop all services
cd ~/hivematrix/hivematrix-helm
./stop.sh
sudo systemctl stop neo4j

# 2. Restore from latest backup
latest_backup=$(ls -t /var/backups/hivematrix/backup_*.tar.gz | head -1)
echo "Restoring from: $latest_backup"
sudo python3 restore.py "$latest_backup"

# 3. Restart everything
./start.sh
sudo systemctl start neo4j

# 4. Verify health
source pyenv/bin/activate
python cli.py status
```

### If Keycloak is Broken

**Reset Keycloak (will lose user data!):**
```bash
cd ~/hivematrix/hivematrix-helm
./stop.sh
rm -rf ../keycloak-26.4.0
rm instance/configs/master_config.json
./start.sh
# This will trigger Keycloak auto-configuration
```

**⚠️ WARNING:** This recreates Keycloak from scratch. You'll need to recreate users.

### If Database is Corrupted

**Restore specific database from backup:**
```bash
# Extract backup
cd /tmp
sudo tar -xzf /var/backups/hivematrix/backup_YYYY-MM-DD_HH-MM-SS.tar.gz

# Drop and recreate database
sudo -u postgres dropdb codex_db
sudo -u postgres createdb codex_db -O codex_user

# Restore from backup
sudo -u postgres psql codex_db < /tmp/codex_db.sql

# Clean up
rm -rf /tmp/codex_db.sql
```

---

## 📝 Quick Notes

### Session Management
- Sessions stored in Redis (persistent across Core restarts)
- Default session timeout: 1 hour
- Sessions checked on every request by Nexus

### Authentication Flow
```
User → Nexus → Keycloak Login → Core (JWT mint) → Nexus (store in session)
↓
All requests: Nexus validates JWT → Proxy to backend
```

### Service Dependencies
```
Nexus depends on: Core, Keycloak
Core depends on: Keycloak, Redis
All services depend on: Core (for JWT validation)
Codex, Ledger, Brainhair, Beacon depend on: PostgreSQL
KnowledgeTree depends on: Neo4j
```

### Default Port Bindings
- **Production:** Only Nexus (443) and Keycloak (8080) on 0.0.0.0
- **All other services:** Bound to 127.0.0.1 (localhost only)
- **Access:** All user traffic goes through Nexus proxy

### Backup Schedule
- **When:** Daily at 2:00 AM
- **Retention:** 30 days
- **Location:** `/var/backups/hivematrix/`
- **What:** All PostgreSQL databases + Neo4j + Keycloak config
- **Service:** systemd timer (`hivematrix-backup.timer`)

---

## 🔍 Useful One-Liners

```bash
# Find which service is using a port
sudo netstat -tlnp | grep :[port]

# Kill process on specific port (use with caution!)
sudo kill $(sudo lsof -t -i:[port])

# Check all Python processes
ps aux | grep python

# Find HiveMatrix processes
ps aux | grep "run.py\|flask run"

# Disk usage of backups
du -sh /var/backups/hivematrix/

# Count lines of code in a service
find ~/hivematrix/hivematrix-codex/app -name "*.py" | xargs wc -l

# Find recent errors in logs
cd ~/hivematrix/hivematrix-helm
source pyenv/bin/activate
python logs_cli.py --level ERROR --tail 100 | grep -i "error\|exception\|failed"

# Test all health endpoints
for svc in core beacon helm codex knowledgetree ledger brainhair; do
  echo -n "$svc: "
  curl -s http://localhost:$(grep -r "port.*[0-9]" ~/hivematrix/hivematrix-$svc/.flaskenv | cut -d= -f2)/health | jq -r '.status'
done
```

---

## 📚 Documentation References

- **Architecture:** `hivematrix-docs/docs/ARCHITECTURE.md`
- **Service Overview:** `hivematrix-docs/docs/services-overview.md`
- **Security Audit:** `hivematrix-docs/docs/SECURITY-AUDIT-2025-11-22.md`
- **Backup Guide:** `hivematrix-docs/docs/BACKUP.md`
- **TODO List:** `hivematrix-docs/docs/HIVEMATRIX-TODO.md`

---

## 🆘 When All Else Fails

1. **Check logs:** `python logs_cli.py [service] --level ERROR --tail 100`
2. **Check health:** `curl http://localhost:[port]/health | jq`
3. **Restart service:** `python cli.py restart [service]`
4. **Restore from backup:** Latest in `/var/backups/hivematrix/`
5. **Check documentation:** `hivematrix-docs/docs/`

**Still stuck?** Review the security audit and architecture docs. They contain detailed information about how everything works together.

---

**Remember:** This is an internal tool for 10 users. Don't overthink it. If something breaks, check logs, restart the service, or restore from backup. You've got comprehensive backups running daily. 🛡️

**Last Updated:** 2025-11-22
