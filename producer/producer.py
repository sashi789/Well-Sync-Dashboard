#!/usr/bin/env python3
"""
Kafka Producer for Drilling Sensor Data
Streams CSV data row-by-row to Kafka topic
"""

import os
import json
import csv
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DrillingDataProducer:
    """Kafka producer for drilling sensor data"""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic = os.getenv('KAFKA_TOPIC', 'drilling-sensor-data')
        self.csv_file_path = os.getenv('CSV_FILE_PATH', '/data/78B-32_1_sec_data_27200701.csv')
        self.batch_size = int(os.getenv('PRODUCER_BATCH_SIZE', '100'))
        self.delay_ms = int(os.getenv('PRODUCER_DELAY_MS', '1000'))
        self.use_original_timestamps = os.getenv('USE_ORIGINAL_TIMESTAMPS', 'true').lower() == 'true'
        
        # Initialize Kafka producer
        self.producer = self._create_producer()
        
    def _create_producer(self) -> KafkaProducer:
        """Create and configure Kafka producer"""
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas to acknowledge
                retries=3,
                retry_backoff_ms=1000,
                batch_size=16384,
                linger_ms=10,
                buffer_memory=33554432,
                max_block_ms=60000,
                request_timeout_ms=30000
            )
            logger.info(f"Kafka producer created successfully. Bootstrap servers: {self.bootstrap_servers}")
            return producer
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            raise
    
    def _parse_csv_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Parse and clean CSV row data"""
        try:
            # Parse timestamp
            date_str = row.get('YYYY/MM/DD', '')
            time_str = row.get('HH:MM:SS', '')
            timestamp = f"{date_str} {time_str}"
            
            # Convert numeric fields, handling -999.25 as null values
            def safe_float(value: str) -> Optional[float]:
                if value == '' or value == '-999.25':
                    return None
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            
            # Parse only the 5 key metrics
            parsed_data = {
                'timestamp': timestamp,
                'rate_of_penetration_ft_per_hr': safe_float(row.get('Rate Of Penetration (ft_per_hr)', '')),  # ROP
                'rotary_rpm': safe_float(row.get('Rotary RPM (RPM)', '')),                                     # RPM
                'weight_on_bit_klbs': safe_float(row.get('Weight on Bit (klbs)', '')),                        # WOB
                'bit_depth_ft': safe_float(row.get('Bit Depth (feet)', '')),                                  # Bit Depth
                'pump_1_strokes_per_min_spm': safe_float(row.get('Pump 1 strokes/min (SPM)', ''))            # Pump Pressure (SPM)
            }
            
            # Add metadata
            parsed_data['produced_at'] = datetime.utcnow().isoformat()
            parsed_data['source_file'] = os.path.basename(self.csv_file_path)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing CSV row: {e}")
            return None
    
    def _send_message(self, message: Dict[str, Any], row_number: int) -> bool:
        """Send message to Kafka topic"""
        try:
            # Use row number as key for partitioning
            key = f"row_{row_number}"
            
            # Send message
            future = self.producer.send(
                self.topic,
                key=key,
                value=message
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            logger.debug(f"Message sent to topic {record_metadata.topic}, partition {record_metadata.partition}, offset {record_metadata.offset}")
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error sending message: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def stream_data(self):
        """Stream CSV data to Kafka topic continuously (looping)."""
        logger.info(f"Starting to stream data from {self.csv_file_path}")
        logger.info(f"Target topic: {self.topic}")
        logger.info(f"Batch size: {self.batch_size}, Delay: {self.delay_ms}ms")
        
        if not os.path.exists(self.csv_file_path):
            logger.error(f"CSV file not found: {self.csv_file_path}")
            return
        
        total_rows_sent = 0
        success_count = 0
        error_count = 0
        
        try:
            while True:
                with open(self.csv_file_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    # Anchor times for real-time simulation
                    sim_start_wallclock = datetime.utcnow()
                    sim_start_data_ts: Optional[datetime] = None
                    for idx, row in enumerate(reader, start=1):
                        total_rows_sent += 1
                        
                        parsed_data = self._parse_csv_row(row)
                        if parsed_data is None:
                            error_count += 1
                            continue
                        # Shift original CSV timestamp to "now" so Grafana/Influx show data in recent window
                        if not self.use_original_timestamps:
                            try:
                                original_ts_str = parsed_data.get('timestamp', '')
                                data_ts = datetime.strptime(original_ts_str, "%Y/%m/%d %H:%M:%S")
                                if sim_start_data_ts is None:
                                    sim_start_data_ts = data_ts
                                delta = data_ts - sim_start_data_ts
                                simulated_ts = sim_start_wallclock + delta
                                parsed_data['timestamp'] = simulated_ts.strftime("%Y/%m/%d %H:%M:%S")
                                logger.info(f"USE_ORIGINAL_TIMESTAMPS: {self.use_original_timestamps}, Simulated timestamp: {simulated_ts.strftime('%Y/%m/%d %H:%M:%S')}")
                            except Exception:
                                # If shifting fails, keep original timestamp
                                logger.warning("Failed to shift timestamp, keeping original")
                                pass
                        else:
                            logger.info(f"USE_ORIGINAL_TIMESTAMPS: {self.use_original_timestamps}, Original timestamp: {parsed_data.get('timestamp', '')}")
                        
                        if self._send_message(parsed_data, total_rows_sent):
                            success_count += 1
                        else:
                            error_count += 1
                        
                        if total_rows_sent % self.batch_size == 0:
                            logger.info(f"Sent {total_rows_sent} messages. Success: {success_count}, Errors: {error_count}")
                        
                        if self.delay_ms > 0:
                            time.sleep(self.delay_ms / 1000.0)
                # When file ends, loop again to simulate continuous real-time stream
                logger.info("Reached end of CSV. Looping to start to continue real-time stream.")
        except FileNotFoundError:
            logger.error(f"File not found: {self.csv_file_path}")
        except KeyboardInterrupt:
            logger.info("Producer interrupted by user. Shutting down...")
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
        finally:
            self.producer.flush()
            self.producer.close()
            logger.info("Producer closed successfully")

def main():
    """Main function"""
    try:
        producer = DrillingDataProducer()
        producer.stream_data()
    except KeyboardInterrupt:
        logger.info("Producer interrupted by user")
    except Exception as e:
        logger.error(f"Producer failed: {e}")
        raise

if __name__ == "__main__":
    main()
