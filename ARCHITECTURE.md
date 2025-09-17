# Drilling Data Streaming Pipeline - Architecture Document

## System Architecture

### High-Level Overview

The drilling data streaming pipeline is designed as a microservices architecture using containerized services orchestrated with Docker Compose. The system processes large CSV datasets containing drilling sensor data and provides real-time visualization capabilities.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Drilling Data Pipeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   CSV       │    │   Kafka     │    │   PostgreSQL/       │ │
│  │  Producer   │───▶│  Cluster    │───▶│   TimescaleDB       │ │
│  │             │    │             │    │   (Raw Storage)     │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                   │                   ▲              │
│         │                   │                   │              │
│         │                   ▼                   │              │
│         │            ┌─────────────┐            │              │
│         │            │   Kafka     │            │              │
│         │            │  Consumer   │────────────┘              │
│         │            │             │                           │
│         │            └─────────────┘                           │
│         │                   │                                 │
│         │                   ▼                                 │
│         │            ┌─────────────┐    ┌─────────────────────┐ │
│         │            │  InfluxDB   │◀───│     Grafana         │ │
│         │            │ (Time Series│    │   (Visualization)   │ │
│         │            │   Storage)  │    │                     │ │
│         │            └─────────────┘    └─────────────────────┘ │
│         │                                                       │
│         └───────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Ingestion Layer

#### Kafka Producer Service
- **Technology**: Python 3.11 with kafka-python library
- **Function**: Reads CSV data and streams to Kafka
- **Configuration**:
  - Batch processing with configurable size
  - Configurable delay between messages
  - Error handling and retry logic
  - JSON serialization for message format

#### Apache Kafka
- **Version**: 7.4.0 (Confluent Platform)
- **Configuration**:
  - Single broker setup for development
  - Topic: `drilling-sensor-data`
  - Replication factor: 1
  - Partitions: 1 (configurable for scaling)
- **Persistence**: Docker volume for message durability

#### Zookeeper
- **Version**: 7.4.0 (Confluent Platform)
- **Function**: Kafka coordination and metadata management
- **Configuration**: Single node setup

### 2. Data Processing Layer

#### Kafka Consumer Service
- **Technology**: Python 3.11 with multiple libraries
- **Dependencies**:
  - kafka-python: Kafka integration
  - psycopg2: PostgreSQL connectivity
  - influxdb-client: InfluxDB integration
- **Functions**:
  - Message consumption from Kafka
  - Data transformation and validation
  - KPI calculations
  - Dual database writes

### 3. Data Storage Layer

#### PostgreSQL with TimescaleDB
- **Version**: Latest TimescaleDB with PostgreSQL 15
- **Purpose**: Long-term raw data storage and analytics
- **Features**:
  - Hypertables for time-series optimization
  - Continuous aggregates for real-time analytics
  - Retention policies for data lifecycle management
  - Custom functions for drilling efficiency calculations

**Schema Design**:
```sql
-- Raw sensor data table
CREATE TABLE raw_sensor_data (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    -- 20+ sensor fields
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('raw_sensor_data', 'timestamp');

-- Continuous aggregates for real-time analytics
CREATE MATERIALIZED VIEW drilling_kpis_5min
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('5 minutes', timestamp) AS bucket,
    AVG(rate_of_penetration_ft_per_hr) AS rop_avg,
    -- Additional aggregations
FROM raw_sensor_data
GROUP BY bucket;
```

#### InfluxDB
- **Version**: 2.7
- **Purpose**: High-performance time-series storage for real-time queries
- **Configuration**:
  - Organization: `drilling`
  - Bucket: `sensor-data`
  - Token-based authentication
- **Data Model**:
  - Measurement: `drilling_sensors` (raw data)
  - Measurement: `drilling_kpis` (calculated metrics)
  - Tags: `well_id`, `source_file`

### 4. Visualization Layer

#### Grafana
- **Version**: Latest
- **Configuration**:
  - InfluxDB data source with Flux queries
  - Pre-configured dashboards
  - Auto-provisioning of datasources and dashboards
- **Dashboards**:
  - Drilling Operations Overview
  - Drilling KPIs Dashboard

## Data Flow Architecture

### 1. Data Ingestion Flow
```
CSV File → Producer → Kafka Topic → Consumer → Databases
```

**Detailed Steps**:
1. Producer reads CSV file row-by-row
2. Each row is parsed and validated
3. JSON message is created with metadata
4. Message is sent to Kafka topic with row number as key
5. Consumer receives message from Kafka
6. Data is written to both PostgreSQL and InfluxDB
7. KPIs are calculated and stored in InfluxDB

### 2. Real-time Processing Flow
```
Sensor Data → KPI Calculation → InfluxDB → Grafana → Dashboard
```

**KPI Calculations**:
- Rate of Penetration (ROP) - Direct from sensor
- Weight on Bit (WOB) - Direct from sensor
- Drilling Efficiency - Calculated: `(ROP * 100) / (WOB * RPM / 1000)`
- Moving averages (5-minute, 15-minute windows)

### 3. Data Retention Strategy
- **Raw Data**: 30 days in PostgreSQL
- **Aggregated Data**: 1 year in PostgreSQL
- **Time-series Data**: Configurable retention in InfluxDB
- **Continuous Aggregates**: Automatic refresh policies

## Network Architecture

### Docker Network Configuration
- **Network**: `drilling-network` (bridge driver)
- **Services Communication**: Internal Docker networking
- **External Access**: Port mapping for web interfaces

### Port Mapping
| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| Kafka | 29092 | 9092 | TCP |
| Zookeeper | 2181 | 2181 | TCP |
| PostgreSQL | 5432 | 5432 | TCP |
| InfluxDB | 8086 | 8086 | HTTP |
| Grafana | 3000 | 3000 | HTTP |

## Security Architecture

### Authentication & Authorization
- **PostgreSQL**: Username/password authentication
- **InfluxDB**: Token-based authentication
- **Grafana**: Admin user with configurable credentials
- **Kafka**: No authentication (development setup)

### Data Security
- **In Transit**: Internal Docker network (encrypted in production)
- **At Rest**: Docker volumes with host filesystem
- **Access Control**: Environment variable configuration

## Scalability Considerations

### Horizontal Scaling
1. **Kafka Scaling**:
   - Add more brokers
   - Increase topic partitions
   - Implement consumer groups

2. **Consumer Scaling**:
   - Multiple consumer instances
   - Different consumer groups
   - Load balancing across partitions

3. **Database Scaling**:
   - PostgreSQL read replicas
   - InfluxDB clustering
   - Data sharding strategies

### Vertical Scaling
- **Resource Allocation**: Docker resource limits
- **Memory Optimization**: JVM tuning for Kafka
- **Storage Optimization**: SSD storage for databases

## Monitoring Architecture

### Application Monitoring
- **Logging**: Structured logging with timestamps
- **Metrics**: Message processing rates
- **Health Checks**: Service availability monitoring

### Infrastructure Monitoring
- **Container Health**: Docker health checks
- **Resource Usage**: CPU, memory, disk monitoring
- **Network Monitoring**: Inter-service communication

### Business Metrics
- **Data Throughput**: Messages per second
- **Processing Latency**: End-to-end processing time
- **Data Quality**: Success/failure rates

## Disaster Recovery

### Backup Strategy
- **Database Backups**: Regular PostgreSQL dumps
- **Configuration Backups**: Docker Compose and environment files
- **Data Replication**: InfluxDB backup and restore procedures

### Recovery Procedures
- **Service Recovery**: Docker Compose restart procedures
- **Data Recovery**: Database restore from backups
- **Configuration Recovery**: Environment variable restoration

## Performance Characteristics

### Expected Performance
- **Throughput**: 1000+ messages/second
- **Latency**: < 1 second end-to-end
- **Storage**: ~1GB per day of raw data
- **Memory**: 8GB+ recommended for full stack

### Optimization Strategies
- **Batch Processing**: Configurable batch sizes
- **Connection Pooling**: Database connection optimization
- **Caching**: InfluxDB query result caching
- **Indexing**: Optimized database indexes

## Technology Stack Summary

| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| Message Broker | Apache Kafka | 7.4.0 | Event streaming |
| Coordination | Zookeeper | 7.4.0 | Kafka coordination |
| Relational DB | PostgreSQL + TimescaleDB | Latest | Raw data storage |
| Time Series DB | InfluxDB | 2.7 | Real-time analytics |
| Visualization | Grafana | Latest | Dashboards |
| Containerization | Docker | Latest | Service orchestration |
| Orchestration | Docker Compose | Latest | Multi-service deployment |
| Programming | Python | 3.11 | Producer/Consumer logic |

## Future Enhancements

### Planned Improvements
1. **Stream Processing**: Apache Flink or Kafka Streams
2. **Machine Learning**: Real-time anomaly detection
3. **Alerting**: Automated alert system
4. **API Layer**: REST API for data access
5. **Multi-well Support**: Support for multiple drilling operations

### Integration Opportunities
1. **External Systems**: Integration with drilling control systems
2. **Cloud Deployment**: Kubernetes deployment
3. **Data Lake**: Integration with data lake solutions
4. **Real-time Analytics**: Advanced analytics platform integration
