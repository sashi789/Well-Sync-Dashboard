#!/usr/bin/env python3
"""
Kafka Consumer for Drilling Sensor Data
Consumes messages from Kafka and stores in PostgreSQL and InfluxDB
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DrillingDataConsumer:
    """Kafka consumer for drilling sensor data"""
    
    def __init__(self):
        # Kafka configuration
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic = os.getenv('KAFKA_TOPIC', 'drilling-sensor-data')
        self.group_id = os.getenv('KAFKA_GROUP_ID', 'drilling-consumer-group')
        
        # PostgreSQL configuration
        self.postgres_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'drilling_data'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
        }
        
        # InfluxDB configuration
        self.influxdb_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN', 'drilling-token-123')
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'drilling')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'sensor-data')
        
        # Initialize connections
        self.kafka_consumer = self._create_kafka_consumer()
        self.postgres_conn = self._create_postgres_connection()
        self.influxdb_client = self._create_influxdb_client()
        
    def _create_kafka_consumer(self) -> KafkaConsumer:
        """Create and configure Kafka consumer"""
        try:
            consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_records=100
            )
            logger.info(f"Kafka consumer created successfully. Topic: {self.topic}, Group: {self.group_id}")
            return consumer
        except Exception as e:
            logger.error(f"Failed to create Kafka consumer: {e}")
            raise
    
    def _create_postgres_connection(self):
        """Create PostgreSQL connection"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            conn.autocommit = True
            logger.info("PostgreSQL connection established successfully")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    def _create_influxdb_client(self) -> InfluxDBClient:
        """Create InfluxDB client"""
        try:
            client = InfluxDBClient(
                url=self.influxdb_url,
                token=self.influxdb_token,
                org=self.influxdb_org
            )
            # Test connection
            client.ping()
            logger.info("InfluxDB connection established successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to connect to InfluxDB: {e}")
            raise
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        try:
            # Handle the format: "2021/06/28 00:15:00"
            dt = datetime.strptime(timestamp_str, "%Y/%m/%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.error(f"Error parsing timestamp '{timestamp_str}': {e}")
            return None
    
    def _store_in_postgres(self, data: Dict[str, Any]) -> bool:
        """Store raw data in PostgreSQL"""
        try:
            cursor = self.postgres_conn.cursor()
            
            # Parse timestamp
            timestamp = self._parse_timestamp(data.get('timestamp', ''))
            if timestamp is None:
                return False
            
            # Insert only the 5 key metrics
            insert_query = """
                INSERT INTO raw_sensor_data (
                    timestamp, rate_of_penetration_ft_per_hr, rotary_rpm, 
                    weight_on_bit_klbs, bit_depth_ft, pump_1_strokes_per_min_spm,
                    produced_at, source_file
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            cursor.execute(insert_query, (
                timestamp,
                data.get('rate_of_penetration_ft_per_hr'),  # ROP
                data.get('rotary_rpm'),                     # RPM
                data.get('weight_on_bit_klbs'),             # WOB
                data.get('bit_depth_ft'),                   # Bit Depth
                data.get('pump_1_strokes_per_min_spm'),     # Pump Pressure (SPM)
                data.get('produced_at'),
                data.get('source_file')
            ))
            
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"Error storing data in PostgreSQL: {e}")
            return False
    
    def _store_in_influxdb(self, data: Dict[str, Any]) -> bool:
        """Store time-series data in InfluxDB"""
        try:
            write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)
            
            # Parse timestamp
            timestamp = self._parse_timestamp(data.get('timestamp', ''))
            if timestamp is None:
                logger.error(f"Failed to parse timestamp: {data.get('timestamp', '')}")
                return False
            
            # Create InfluxDB point for drilling sensor data
            point = Point("drilling_sensors") \
                .tag("well_id", "78B-32") \
                .tag("source_file", data.get('source_file', 'unknown')) \
                .time(timestamp)
            
            # Add only the 5 key metrics (only non-null values)
            numeric_fields = [
                'rate_of_penetration_ft_per_hr',  # ROP
                'rotary_rpm',                     # RPM
                'weight_on_bit_klbs',             # WOB
                'bit_depth_ft',                   # Bit Depth
                'pump_1_strokes_per_min_spm'      # Pump Pressure (SPM)
            ]
            
            fields_added = 0
            for field in numeric_fields:
                value = data.get(field)
                if value is not None:
                    point.field(field, value)
                    fields_added += 1
            
            if fields_added == 0:
                logger.warning("No valid fields to write to InfluxDB")
                return False
            
            # Write to InfluxDB
            logger.debug(f"Writing to InfluxDB: {point}")
            write_api.write(bucket=self.influxdb_bucket, org=self.influxdb_org, record=point)
            logger.debug("Successfully wrote to InfluxDB")
            return True
            
        except Exception as e:
            logger.error(f"Error storing data in InfluxDB: {e}")
            return False
    
    def _calculate_kpis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key performance indicators for the 5 key metrics"""
        try:
            kpis = {}
            
            # Store the 5 key metrics
            kpis['rop'] = data.get('rate_of_penetration_ft_per_hr')      # ROP
            kpis['rpm'] = data.get('rotary_rpm')                         # RPM
            kpis['wob'] = data.get('weight_on_bit_klbs')                 # WOB
            kpis['bit_depth'] = data.get('bit_depth_ft')                 # Bit Depth
            kpis['pump_pressure'] = data.get('pump_1_strokes_per_min_spm')  # Pump Pressure (SPM)
            
            # Calculate drilling efficiency using the 3 main parameters
            rop = kpis['rop']
            wob = kpis['wob']
            rpm = kpis['rpm']
            
            if rop is not None and wob is not None and rpm is not None and wob > 0 and rpm > 0:
                kpis['drilling_efficiency'] = (rop * 100.0) / (wob * rpm / 1000.0)
            else:
                kpis['drilling_efficiency'] = None
            
            return kpis
            
        except Exception as e:
            logger.error(f"Error calculating KPIs: {e}")
            return {}
    
    def _store_kpis_in_influxdb(self, kpis: Dict[str, Any], timestamp: datetime) -> bool:
        """Store calculated KPIs in InfluxDB"""
        try:
            write_api = self.influxdb_client.write_api(write_options=SYNCHRONOUS)
            
            # Create InfluxDB point for KPIs
            point = Point("drilling_kpis") \
                .tag("well_id", "78B-32") \
                .time(timestamp)
            
            # Add KPI fields
            fields_added = 0
            for key, value in kpis.items():
                if value is not None:
                    point.field(key, value)
                    fields_added += 1
            
            if fields_added == 0:
                logger.warning("No valid KPI fields to write to InfluxDB")
                return False
            
            # Write to InfluxDB
            logger.debug(f"Writing KPIs to InfluxDB: {point}")
            write_api.write(bucket=self.influxdb_bucket, org=self.influxdb_org, record=point)
            logger.debug("Successfully wrote KPIs to InfluxDB")
            return True
            
        except Exception as e:
            logger.error(f"Error storing KPIs in InfluxDB: {e}")
            return False
    
    def process_message(self, message) -> bool:
        """Process a single Kafka message"""
        try:
            data = message.value
            logger.debug(f"Processing message: {message.key}")
            logger.debug(f"Message data keys: {list(data.keys())}")
            
            # Store raw data in PostgreSQL
            postgres_success = self._store_in_postgres(data)
            logger.debug(f"PostgreSQL write result: {postgres_success}")
            
            # Store time-series data in InfluxDB
            influxdb_success = self._store_in_influxdb(data)
            logger.debug(f"InfluxDB write result: {influxdb_success}")
            
            # Calculate and store KPIs
            timestamp = self._parse_timestamp(data.get('timestamp', ''))
            if timestamp:
                kpis = self._calculate_kpis(data)
                logger.debug(f"Calculated KPIs: {kpis}")
                kpi_success = self._store_kpis_in_influxdb(kpis, timestamp)
                logger.debug(f"KPI InfluxDB write result: {kpi_success}")
            else:
                logger.warning("Failed to parse timestamp for KPIs")
                kpi_success = False
            
            success = postgres_success and influxdb_success and kpi_success
            
            if success:
                logger.debug(f"Successfully processed message: {message.key}")
            else:
                logger.warning(f"Partial failure processing message: {message.key} - PostgreSQL: {postgres_success}, InfluxDB: {influxdb_success}, KPIs: {kpi_success}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return False
    
    def consume_messages(self):
        """Main consumer loop"""
        logger.info("Starting to consume messages from Kafka")
        
        message_count = 0
        success_count = 0
        error_count = 0
        
        try:
            for message in self.kafka_consumer:
                message_count += 1
                
                if self.process_message(message):
                    success_count += 1
                else:
                    error_count += 1
                
                # Log progress
                if message_count % 100 == 0:
                    logger.info(f"Processed {message_count} messages. Success: {success_count}, Errors: {error_count}")
                    
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            raise
        finally:
            # Cleanup
            self.kafka_consumer.close()
            if self.postgres_conn:
                self.postgres_conn.close()
            if self.influxdb_client:
                self.influxdb_client.close()
            
            logger.info(f"Consumer stopped. Total messages: {message_count}, Success: {success_count}, Errors: {error_count}")

def main():
    """Main function"""
    try:
        consumer = DrillingDataConsumer()
        consumer.consume_messages()
    except Exception as e:
        logger.error(f"Consumer failed: {e}")
        raise

if __name__ == "__main__":
    main()
