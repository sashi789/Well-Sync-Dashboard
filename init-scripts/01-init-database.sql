-- Initialize TimescaleDB extension and create tables for drilling data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create raw sensor data table with only the 5 key metrics
CREATE TABLE IF NOT EXISTS raw_sensor_data (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    rate_of_penetration_ft_per_hr DOUBLE PRECISION,  -- ROP
    rotary_rpm DOUBLE PRECISION,                     -- RPM
    weight_on_bit_klbs DOUBLE PRECISION,             -- WOB
    bit_depth_ft DOUBLE PRECISION,                   -- Bit Depth
    pump_1_strokes_per_min_spm DOUBLE PRECISION,     -- Pump Pressure (SPM)
    produced_at TIMESTAMPTZ,
    source_file TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('raw_sensor_data', 'timestamp', if_not_exists => TRUE);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_raw_sensor_data_timestamp ON raw_sensor_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_raw_sensor_data_bit_depth ON raw_sensor_data (bit_depth_ft);
CREATE INDEX IF NOT EXISTS idx_raw_sensor_data_rop ON raw_sensor_data (rate_of_penetration_ft_per_hr);

-- Create processed KPIs table with only the 5 key metrics
CREATE TABLE IF NOT EXISTS drilling_kpis (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    well_id TEXT DEFAULT '78B-32',
    rop_avg_5min DOUBLE PRECISION,
    rop_avg_15min DOUBLE PRECISION,
    wob_avg_5min DOUBLE PRECISION,
    wob_avg_15min DOUBLE PRECISION,
    rpm_avg_5min DOUBLE PRECISION,
    rpm_avg_15min DOUBLE PRECISION,
    bit_depth_current DOUBLE PRECISION,
    pump_pressure_avg_5min DOUBLE PRECISION,
    pump_pressure_avg_15min DOUBLE PRECISION,
    drilling_efficiency DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
);

-- Convert to hypertable
SELECT create_hypertable('drilling_kpis', 'timestamp', if_not_exists => TRUE);

-- Create indexes for KPIs
CREATE INDEX IF NOT EXISTS idx_drilling_kpis_timestamp ON drilling_kpis (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_drilling_kpis_well_id ON drilling_kpis (well_id);

-- Create continuous aggregates for real-time analytics (5 key metrics only)
CREATE MATERIALIZED VIEW IF NOT EXISTS drilling_kpis_5min
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('5 minutes', timestamp) AS bucket,
    well_id,
    AVG(rate_of_penetration_ft_per_hr) AS rop_avg,
    AVG(weight_on_bit_klbs) AS wob_avg,
    AVG(rotary_rpm) AS rpm_avg,
    AVG(pump_1_strokes_per_min_spm) AS pump_pressure_avg,
    MAX(bit_depth_ft) AS bit_depth_max,
    COUNT(*) AS data_points
FROM raw_sensor_data
WHERE timestamp > NOW() - INTERVAL '1 day'
GROUP BY bucket, well_id;

-- Create materialized view for 15-minute aggregates (5 key metrics only)
CREATE MATERIALIZED VIEW IF NOT EXISTS drilling_kpis_15min
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('15 minutes', timestamp) AS bucket,
    well_id,
    AVG(rate_of_penetration_ft_per_hr) AS rop_avg,
    AVG(weight_on_bit_klbs) AS wob_avg,
    AVG(rotary_rpm) AS rpm_avg,
    AVG(pump_1_strokes_per_min_spm) AS pump_pressure_avg,
    MAX(bit_depth_ft) AS bit_depth_max,
    COUNT(*) AS data_points
FROM raw_sensor_data
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY bucket, well_id;

-- Add refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy('drilling_kpis_5min',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes');

SELECT add_continuous_aggregate_policy('drilling_kpis_15min',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '15 minutes',
    schedule_interval => INTERVAL '15 minutes');

-- Create retention policy (keep raw data for 30 days, aggregated data for 1 year)
SELECT add_retention_policy('raw_sensor_data', INTERVAL '30 days');
SELECT add_retention_policy('drilling_kpis', INTERVAL '1 year');

-- Create a function to calculate drilling efficiency
CREATE OR REPLACE FUNCTION calculate_drilling_efficiency(
    rop DOUBLE PRECISION,
    wob DOUBLE PRECISION,
    rpm DOUBLE PRECISION
) RETURNS DOUBLE PRECISION AS $$
BEGIN
    -- Simple drilling efficiency calculation
    -- Higher ROP with lower WOB and RPM is more efficient
    IF rop IS NULL OR wob IS NULL OR rpm IS NULL OR wob = 0 OR rpm = 0 THEN
        RETURN NULL;
    END IF;
    
    RETURN (rop * 100.0) / (wob * rpm / 1000.0);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
