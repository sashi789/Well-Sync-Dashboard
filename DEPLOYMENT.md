# Deployment Guide - Drilling Data Streaming Pipeline

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows with WSL2
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: Minimum 20GB free disk space
- **CPU**: 4+ cores recommended

### Network Requirements
- **Ports**: 3000 (Grafana), 5432 (Postgres), 8086 (InfluxDB), 9092 (Kafka), 2181 (Zookeeper), 5050 (pgAdmin) must be available
- **Internet**: Required for downloading Docker images
- **Firewall**: Ensure Docker can access required ports

### Data Requirements
- **CSV File**: `78B-32 1 sec data 27200701.csv` in project directory
- **File Size**: ~411MB (as per your dataset)

## Installation Steps

### 1. Environment Setup

```bash
# Clone or download the project
cd "/Users/sashidharchary/Desktop/Cavelle Energy/Dashbord"

# Verify CSV file exists
ls -la "78B-32 1 sec data 27200701.csv"

# Copy environment template
cp env.example .env

# Edit environment variables (optional)
nano .env
```

### 2. Docker Environment Verification

```bash
# Check Docker installation
docker --version
docker-compose --version

# Verify Docker daemon is running
docker info

# Check available resources
docker system df
```

### 3. Initial Deployment

```bash
# Start all services
docker-compose up -d

# Monitor startup process
docker-compose logs -f

# Check service status
docker-compose ps
```

Expected output:
```
Name                     Command               State           Ports
-------------------------------------------------------------------------------
grafana                  /run.sh                          Up      0.0.0.0:3000->3000/tcp
influxdb                 /entrypoint.sh influxd           Up      0.0.0.0:8086->8086/tcp
kafka                    /etc/confluent/docker/run        Up      0.0.0.0:9092->9092/tcp
kafka-consumer           python consumer.py               Up
kafka-producer           python producer.py               Up
postgres                 docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp
zookeeper                /etc/confluent/docker/run        Up      0.0.0.0:2181->2181/tcp
```

### 4. Service Health Verification

```bash
# Check Kafka topic creation
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list

# Verify PostgreSQL connection
docker exec -it postgres psql -U postgres -d drilling_data -c "SELECT COUNT(*) FROM raw_sensor_data;"

# Check InfluxDB setup
curl -i http://localhost:8086/health

# Verify Grafana is accessible
curl -i http://localhost:3000/api/health

# Verify pgAdmin is accessible
curl -i http://localhost:5050
```

## Configuration

### Environment Variables

Edit the `.env` file to customize your deployment:

```bash
# Database Configuration
POSTGRES_DB=drilling_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password

# InfluxDB Configuration
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=your_secure_password
INFLUXDB_ORG=drilling
INFLUXDB_BUCKET=sensor-data
INFLUXDB_TOKEN=your_secure_token

# Grafana Configuration
GRAFANA_USER=admin
GRAFANA_PASSWORD=your_secure_password

# pgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=admin@local.com
PGADMIN_DEFAULT_PASSWORD=your_secure_password

# Producer Configuration
PRODUCER_BATCH_SIZE=100
PRODUCER_DELAY_MS=1000

# Consumer Configuration
KAFKA_GROUP_ID=drilling-consumer-group
```

### Producer Configuration

Adjust producer behavior by modifying environment variables:

```bash
# For faster streaming (reduce delay)
PRODUCER_DELAY_MS=100

# For larger batches
PRODUCER_BATCH_SIZE=500

# For slower streaming (simulate real-time)
PRODUCER_DELAY_MS=5000
```

### Database Configuration

#### PostgreSQL/TimescaleDB Tuning
```sql
-- Connect to database
docker exec -it postgres psql -U postgres -d drilling_data

-- Adjust chunk interval for better performance
SELECT set_chunk_time_interval('raw_sensor_data', INTERVAL '1 hour');

-- Create additional indexes if needed
CREATE INDEX CONCURRENTLY idx_raw_sensor_data_well_id ON raw_sensor_data (well_id);
```

#### InfluxDB Configuration
```bash
# Access InfluxDB CLI
docker exec -it influxdb influx

# Create additional buckets if needed
CREATE BUCKET "historical-data" WITH RETENTION 90d;

# Set up additional retention policies
ALTER RETENTION POLICY "autogen" ON "sensor-data" DURATION 30d;
```

## Monitoring and Maintenance

### Service Monitoring

```bash
# View real-time logs
docker-compose logs -f kafka-producer
docker-compose logs -f kafka-consumer

# Check resource usage
docker stats

# Monitor disk usage
docker system df
```

### Data Monitoring

```bash
# Check message count in Kafka topic
docker exec -it kafka kafka-run-class kafka.tools.GetOffsetShell \
  --bootstrap-server localhost:9092 \
  --topic drilling-sensor-data \
  --time -1

# Monitor PostgreSQL data growth
docker exec -it postgres psql -U postgres -d drilling_data \
  -c "SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM raw_sensor_data;"

# Check InfluxDB data points
curl -G 'http://localhost:8086/query' \
  --data-urlencode "q=SELECT COUNT(*) FROM drilling_sensors"
```

### Performance Monitoring

```bash
# Monitor Kafka consumer lag
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group drilling-consumer-group \
  --describe

# Check database performance
docker exec -it postgres psql -U postgres -d drilling_data \
  -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Services Not Starting

**Problem**: Services fail to start or crash immediately

**Solutions**:
```bash
# Check Docker resources
docker system prune -f
docker volume prune -f

# Restart Docker daemon (if needed)
sudo systemctl restart docker  # Linux
# or restart Docker Desktop on macOS/Windows

# Check port conflicts
netstat -tulpn | grep :3000
netstat -tulpn | grep :5432
netstat -tulpn | grep :8086
netstat -tulpn | grep :9092
```

#### 2. Producer Not Sending Messages

**Problem**: No messages appearing in Kafka topic

**Solutions**:
```bash
# Check CSV file path
docker exec -it kafka-producer ls -la /data/

# Verify Kafka connectivity
docker exec -it kafka-producer python -c "
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers=['kafka:29092'])
print('Kafka connection successful')
"

# Check producer logs
docker-compose logs kafka-producer
```

#### 3. Consumer Not Processing Messages

**Problem**: Messages in Kafka but not in databases

**Solutions**:
```bash
# Check database connections
docker exec -it kafka-consumer python -c "
import psycopg2
conn = psycopg2.connect(host='postgres', port=5432, database='drilling_data', user='postgres', password='postgres')
print('PostgreSQL connection successful')
"

# Check InfluxDB connection
docker exec -it kafka-consumer python -c "
from influxdb_client import InfluxDBClient
client = InfluxDBClient(url='http://influxdb:8086', token='drilling-token-123')
print('InfluxDB connection successful')
"

# Check consumer logs
docker-compose logs kafka-consumer
```

#### 4. Grafana Dashboards Not Loading

**Problem**: Empty dashboards or connection errors

**Solutions**:
```bash
# Verify InfluxDB data source
curl -G 'http://localhost:8086/query' \
  --data-urlencode "q=SHOW MEASUREMENTS"

# Check Grafana data source configuration
curl -H "Authorization: Bearer admin:admin" \
  http://localhost:3000/api/datasources

# Restart Grafana service
docker-compose restart grafana

#### 6. pgAdmin Issues

**Problem**: Invalid email error at startup

**Solution**: Ensure `PGADMIN_DEFAULT_EMAIL` contains a valid email, e.g. `admin@local.com`, then recreate pgAdmin:
```bash
docker compose rm -f pgadmin && docker volume rm dashbord_pgadmin-data && docker compose up -d pgadmin
```

**Problem**: Cannot connect from pgAdmin to Postgres

**Solutions**:
```bash
# Use service name inside Docker network
Host: postgres
Port: 5432
User: postgres
Password: value from POSTGRES_PASSWORD in docker-compose.yml
```
```

#### 5. High Memory Usage

**Problem**: System running out of memory

**Solutions**:
```bash
# Check memory usage by service
docker stats --no-stream

# Reduce batch sizes
# Edit .env file
PRODUCER_BATCH_SIZE=50
PRODUCER_DELAY_MS=2000

# Restart services
docker-compose restart kafka-producer kafka-consumer
```

### Log Analysis

#### Producer Logs
```bash
# Monitor producer progress
docker-compose logs -f kafka-producer | grep "Processed"

# Check for errors
docker-compose logs kafka-producer | grep -i error
```

#### Consumer Logs
```bash
# Monitor consumer processing
docker-compose logs -f kafka-consumer | grep "Successfully processed"

# Check for database errors
docker-compose logs kafka-consumer | grep -i "postgres\|influxdb"
```

#### System Logs
```bash
# Check Docker daemon logs
journalctl -u docker.service  # Linux
# or check Docker Desktop logs on macOS/Windows

# Check system resource usage
htop  # or top
df -h
free -h
```

## Backup and Recovery

### Data Backup

```bash
# Backup PostgreSQL data
docker exec postgres pg_dump -U postgres drilling_data > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup InfluxDB data
docker exec influxdb influx backup /tmp/backup_$(date +%Y%m%d_%H%M%S)

# Backup configuration
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz \
  docker-compose.yml .env grafana/ init-scripts/
```

### Data Recovery

```bash
# Restore PostgreSQL data
docker exec -i postgres psql -U postgres drilling_data < backup_file.sql

# Restore InfluxDB data
docker exec influxdb influx restore /tmp/backup_directory

# Restore configuration
tar -xzf config_backup_file.tar.gz
```

## Scaling and Optimization

### Horizontal Scaling

#### Multiple Consumer Instances
```bash
# Scale consumer service
docker-compose up -d --scale kafka-consumer=3

# Check consumer group
docker exec -it kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group drilling-consumer-group \
  --describe
```

#### Kafka Partitioning
```bash
# Increase topic partitions
docker exec -it kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --alter \
  --topic drilling-sensor-data \
  --partitions 3
```

### Performance Optimization

#### Database Optimization
```sql
-- PostgreSQL optimization
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

#### InfluxDB Optimization
```bash
# Access InfluxDB config
docker exec -it influxdb influx config

# Optimize for write performance
# Edit influxdb.conf (if using file-based config)
[data]
  cache-max-memory-size = "1g"
  cache-snapshot-memory-size = "25m"
```

## Security Hardening

### Production Security

```bash
# Change default passwords
# Edit .env file with strong passwords
POSTGRES_PASSWORD=your_very_secure_password_here
INFLUXDB_PASSWORD=your_very_secure_password_here
GRAFANA_PASSWORD=your_very_secure_password_here

# Use secrets management
echo "your_secure_token" | docker secret create influxdb_token -
```

### Network Security

```yaml
# Add to docker-compose.yml
networks:
  drilling-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Access Control

```bash
# Restrict database access
# Edit PostgreSQL pg_hba.conf
docker exec -it postgres psql -U postgres -c "
ALTER USER postgres PASSWORD 'new_secure_password';
"

# Configure InfluxDB authentication
docker exec -it influxdb influx auth create \
  --org drilling \
  --all-access \
  --description "Admin token"
```

## Maintenance Schedule

### Daily Tasks
- Monitor service health
- Check disk space usage
- Review error logs

### Weekly Tasks
- Backup configuration and data
- Update Docker images
- Performance analysis

### Monthly Tasks
- Security updates
- Capacity planning
- Disaster recovery testing

## Support and Documentation

### Useful Commands Reference

```bash
# Service management
docker-compose up -d                    # Start all services
docker-compose down                     # Stop all services
docker-compose restart [service]        # Restart specific service
docker-compose logs -f [service]        # Follow logs

# Database access
docker exec -it postgres psql -U postgres -d drilling_data
docker exec -it influxdb influx

# Kafka management
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
docker exec -it kafka kafka-consumer-groups --bootstrap-server localhost:9092 --list

# System monitoring
docker stats                           # Resource usage
docker system df                       # Disk usage
docker-compose ps                      # Service status
```

### Getting Help

1. Check service logs: `docker-compose logs [service-name]`
2. Verify environment variables in `.env`
3. Ensure all required ports are available
4. Check Docker resource limits
5. Review the troubleshooting section above

For additional support, refer to the component documentation:
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [TimescaleDB Documentation](https://docs.timescale.com/)
- [InfluxDB Documentation](https://docs.influxdata.com/)
- [Grafana Documentation](https://grafana.com/docs/)
- [pgAdmin Documentation](https://www.pgadmin.org/docs/)
