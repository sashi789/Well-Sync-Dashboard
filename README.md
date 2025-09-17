# Oil & Gas Drilling Real-Time Streaming Pipeline

A comprehensive real-time streaming pipeline for oil and gas drilling sensor data, built with Apache Kafka, PostgreSQL/TimescaleDB, InfluxDB, and Grafana.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CSV Data      │    │   Kafka         │    │   PostgreSQL/   │
│   Producer      │───▶│   Topic         │───▶│   TimescaleDB   │
│                 │    │                 │    │   (Raw Data)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Kafka         │
                       │   Consumer      │
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   InfluxDB      │    │   Grafana       │
                       │   (Time Series) │◀───│   Dashboards    │
                       └─────────────────┘    └─────────────────┘
```

## Components

### 1. **Kafka Producer Service**
- Reads the CSV dataset row-by-row
- Streams each row as JSON message to Kafka topic `drilling-sensor-data`
- Configurable batch size and delay for real-time simulation
- Built with Python and `kafka-python` library

### 2. **Apache Kafka & Zookeeper**
- Kafka broker for message streaming
- Zookeeper for coordination
- Topic: `drilling-sensor-data`
- Accessible on `localhost:9092`

### 3. **PostgreSQL with TimescaleDB**
- Long-term storage for raw sensor data
- Time-series optimized with hypertables
- Continuous aggregates for real-time analytics
- Retention policies for data management
- Accessible on `localhost:5432`

### 4. **InfluxDB**
- Time-series database for real-time queries
- Optimized for Grafana dashboards
- Stores both raw sensor data and calculated KPIs
- Accessible on `localhost:8086`

### 5. **Kafka Consumer Service**
- Consumes messages from Kafka topic
- Writes raw data to PostgreSQL
- Writes time-series data to InfluxDB
- Calculates drilling KPIs in real-time

### 6. **Grafana**
- Real-time visualization dashboards
- Connected to InfluxDB data source
- Pre-configured dashboards for drilling operations
- Accessible on `localhost:3000`

## Dataset Information

The pipeline processes drilling sensor data from well `78B-32` with the following key parameters:

- **Rate of Penetration (ROP)** - ft/hr
- **Weight on Bit (WOB)** - klbs
- **Rotary RPM** - RPM
- **Standpipe Pressure** - psi
- **Bit Depth** - ft
- **Hook Load** - klbs
- **Rotary Torque** - kft_lb
- **Flow Rate** - gal/min
- **Gamma Ray** - API units

## Quick Start

### Prerequisites
- Docker and Docker Compose
- At least 8GB RAM available for containers
- Ports 3000, 5432, 8086, 9092, 2181 available

### 1. Clone and Setup
```bash
# Copy your CSV file to the project directory
cp "78B-32 1 sec data 27200701.csv" .

# Copy environment variables
cp env.example .env

# Edit .env file if needed (optional)
nano .env
```

### 2. Start the Pipeline
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin |
| InfluxDB | http://localhost:8086 | admin/admin123 |
| PostgreSQL | localhost:5432 | postgres/postgres |
| pgAdmin | http://localhost:5050 | admin@local.com/admin |

### 4. Monitor the Pipeline
```bash
# View producer logs
docker-compose logs -f kafka-producer

# View consumer logs
docker-compose logs -f kafka-consumer

# Check Kafka topic
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Database Configuration
POSTGRES_DB=drilling_data
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# InfluxDB Configuration
INFLUXDB_USER=admin
INFLUXDB_PASSWORD=admin123
INFLUXDB_ORG=drilling
INFLUXDB_BUCKET=sensor-data
INFLUXDB_TOKEN=drilling-token-123

# Grafana Configuration
GRAFANA_USER=admin
GRAFANA_PASSWORD=admin

# Producer Configuration
PRODUCER_BATCH_SIZE=100
PRODUCER_DELAY_MS=1000

# Consumer Configuration
KAFKA_GROUP_ID=drilling-consumer-group
```

### Producer Configuration

The producer can be configured via environment variables:

- `PRODUCER_BATCH_SIZE`: Number of messages to process before logging progress (default: 100)
- `PRODUCER_DELAY_MS`: Delay between messages in milliseconds (default: 1000ms)
- `CSV_FILE_PATH`: Path to the CSV file in the container

### Consumer Configuration

The consumer automatically connects to all services using environment variables and processes messages in real-time.

## Grafana Dashboards

### 1. Drilling Operations Overview
- **URL**: http://localhost:3000/d/drilling-overview
- **Features**:
  - Real-time ROP, WOB, RPM, Standpipe Pressure
  - Bit Depth tracking
  - Drilling Efficiency calculations
  - 5-second refresh rate

### 2. Drilling KPIs Dashboard
- **URL**: http://localhost:3000/d/drilling-kpis
- **Features**:
  - Current KPI values (stat panels)
  - Trend analysis with 5-minute averages
  - Real-time drilling efficiency monitoring

### Dashboard Queries

Example InfluxDB Flux queries used in dashboards:

```flux
// Current ROP
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_kpis")
  |> filter(fn: (r) => r["_field"] == "rop")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> last()

// ROP Trend (5-min average)
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_kpis")
  |> filter(fn: (r) => r["_field"] == "rop")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

## Database Schema

### PostgreSQL/TimescaleDB Tables

#### `raw_sensor_data`
Stores all raw sensor readings with the following key fields:
- `timestamp` - Primary time dimension
- `rate_of_penetration_ft_per_hr` - ROP
- `weight_on_bit_klbs` - WOB
- `rotary_rpm` - RPM
- `standpipe_pressure_psi` - Standpipe pressure
- `bit_depth_ft` - Current bit depth
- And 15+ other sensor fields

#### `drilling_kpis`
Stores calculated KPIs and aggregates:
- `rop_avg_5min` - 5-minute average ROP
- `wob_avg_5min` - 5-minute average WOB
- `drilling_efficiency` - Calculated efficiency metric

### InfluxDB Measurements

#### `drilling_sensors`
Raw sensor data with tags:
- `well_id`: "78B-32"
- `source_file`: Original CSV filename

#### `drilling_kpis`
Calculated KPIs with tags:
- `well_id`: "78B-32"

## Monitoring and Troubleshooting

### Health Checks

```bash
# Check all services are running
docker-compose ps

# Check Kafka topic exists and has messages
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic drilling-sensor-data

# Check message count in topic
docker exec -it kafka kafka-run-class kafka.tools.GetOffsetShell --bootstrap-server localhost:9092 --topic drilling-sensor-data --time -1
```

### Common Issues

1. **Producer not sending messages**
   - Check CSV file path in container
   - Verify Kafka is accessible
   - Check producer logs: `docker-compose logs kafka-producer`

2. **Consumer not processing messages**
   - Verify database connections
   - Check consumer logs: `docker-compose logs kafka-consumer`
   - Ensure InfluxDB is initialized

3. **Grafana dashboards not showing data**
   - Verify InfluxDB data source configuration
   - Check if data is being written to InfluxDB
   - Verify time range in dashboard
   - If Grafana exits with "Datasource provisioning error: data source not found":
     1) `docker compose rm -f grafana`
     2) `docker volume rm dashbord_grafana-data`
     3) `docker compose up -d grafana`

4. **pgAdmin login / connection**
   - Default login is `admin@local.com / admin` (configurable via `PGADMIN_DEFAULT_EMAIL`, `PGADMIN_DEFAULT_PASSWORD` in `docker-compose.yml`)
   - Register server in pgAdmin with:
     - Host: `postgres`, Port: `5432`, Maintenance DB: `postgres`, User: `postgres`, Password: `postgres`

## Daily usage

### Start
```bash
cd "/Users/sashidharchary/Desktop/Cavelle Energy/Dashbord"
docker compose up -d
```

### Stop
```bash
docker compose down
```

### Performance Tuning

1. **Increase Kafka throughput**:
   - Adjust `PRODUCER_BATCH_SIZE` and `PRODUCER_DELAY_MS`
   - Modify Kafka consumer `max_poll_records`

2. **Optimize database performance**:
   - Adjust TimescaleDB chunk intervals
   - Tune InfluxDB retention policies
   - Optimize continuous aggregates refresh intervals

## Data Flow

1. **Producer** reads CSV file row-by-row
2. **Producer** sends JSON messages to Kafka topic
3. **Consumer** receives messages from Kafka
4. **Consumer** stores raw data in PostgreSQL/TimescaleDB
5. **Consumer** stores time-series data in InfluxDB
6. **Consumer** calculates KPIs and stores in InfluxDB
7. **Grafana** queries InfluxDB for real-time visualization

## Scaling Considerations

- **Horizontal scaling**: Add more consumer instances with different group IDs
- **Partitioning**: Partition Kafka topic by well_id for better throughput
- **Database sharding**: Shard PostgreSQL by time periods
- **Load balancing**: Use Kafka Connect for high-throughput scenarios

## Security Notes

- Change default passwords in production
- Use TLS for inter-service communication
- Implement proper network segmentation
- Regular security updates for all components

## Support

For issues or questions:
1. Check the logs: `docker-compose logs [service-name]`
2. Verify environment variables in `.env`
3. Ensure all required ports are available
4. Check Docker resource limits

## License

This project uses open-source components:
- Apache Kafka (Apache 2.0)
- PostgreSQL/TimescaleDB (PostgreSQL License)
- InfluxDB (MIT License)
- Grafana (Apache 2.0)
