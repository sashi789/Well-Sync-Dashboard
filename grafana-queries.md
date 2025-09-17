# Grafana Dashboard Queries Reference

This document provides a comprehensive reference for InfluxDB Flux queries used in the drilling data streaming pipeline Grafana dashboards.

## Data Source Configuration

- **Database**: InfluxDB 2.7
- **Organization**: drilling
- **Bucket**: sensor-data
- **Authentication**: Token-based

## Measurement Structure

### drilling_sensors (Raw Sensor Data)
**Tags**:
- `well_id`: "78B-32"
- `source_file`: Original CSV filename

**Fields**:
- `rate_of_penetration_ft_per_hr` - ROP
- `weight_on_bit_klbs` - WOB
- `rotary_rpm` - RPM
- `standpipe_pressure_psi` - Standpipe pressure
- `bit_depth_ft` - Bit depth
- `hook_load_klbs` - Hook load
- `rotary_torque_kft_lb` - Torque
- `total_pump_output_gal_per_min` - Flow rate
- `gamma_api` - Gamma ray
- And 10+ other sensor fields

### drilling_kpis (Calculated KPIs)
**Tags**:
- `well_id`: "78B-32"

**Fields**:
- `rop` - Rate of Penetration
- `wob` - Weight on Bit
- `rpm` - Rotary RPM
- `standpipe_pressure` - Standpipe pressure
- `bit_depth` - Bit depth
- `hook_load` - Hook load
- `torque` - Rotary torque
- `flow_rate` - Flow rate
- `gamma` - Gamma ray
- `drilling_efficiency` - Calculated efficiency

## Dashboard Queries

### 1. Drilling Operations Overview Dashboard

#### Current ROP (Rate of Penetration)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

#### Current WOB (Weight on Bit)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "weight_on_bit_klbs")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

#### Current RPM (Rotary RPM)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rotary_rpm")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

#### Standpipe Pressure
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "standpipe_pressure_psi")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

#### Bit Depth
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "bit_depth_ft")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

#### Drilling Efficiency
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_kpis")
  |> filter(fn: (r) => r["_field"] == "drilling_efficiency")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

### 2. Drilling KPIs Dashboard

#### Current ROP (Stat Panel)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_kpis")
  |> filter(fn: (r) => r["_field"] == "rop")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> last()
```

#### Current WOB (Stat Panel)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_kpis")
  |> filter(fn: (r) => r["_field"] == "wob")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> last()
```

#### Current RPM (Stat Panel)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_kpis")
  |> filter(fn: (r) => r["_field"] == "rpm")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> last()
```

#### Standpipe Pressure (Stat Panel)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_kpis")
  |> filter(fn: (r) => r["_field"] == "standpipe_pressure")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> last()
```

#### ROP Trend (5-minute average)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_kpis")
  |> filter(fn: (r) => r["_field"] == "rop")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

#### Drilling Efficiency Trend
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_kpis")
  |> filter(fn: (r) => r["_field"] == "drilling_efficiency")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

## Advanced Queries

### Multi-Field Queries

#### All Key Parameters in One Panel
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr" or r["_field"] == "weight_on_bit_klbs" or r["_field"] == "rotary_rpm")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> yield(name: "mean")
```

### Statistical Queries

#### ROP Statistics (Min, Max, Avg)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)
  |> group(columns: ["_field"])
  |> reduce(
    fn: (r, accumulator) => ({
      min: if accumulator.min == 0.0 or r._value < accumulator.min then r._value else accumulator.min,
      max: if r._value > accumulator.max then r._value else accumulator.max,
      sum: accumulator.sum + r._value,
      count: accumulator.count + 1
    }),
    identity: {min: 0.0, max: 0.0, sum: 0.0, count: 0}
  )
  |> map(fn: (r) => ({r with avg: r.sum / r.count}))
  |> yield(name: "statistics")
```

### Time-Based Queries

#### Last 1 Hour Data
```flux
from(bucket: "sensor-data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> yield(name: "last_hour")
```

#### Data from Specific Time Range
```flux
from(bucket: "sensor-data")
  |> range(start: 2021-06-28T00:00:00Z, stop: 2021-06-28T12:00:00Z)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> yield(name: "specific_range")
```

### Aggregation Queries

#### 5-Minute Moving Average
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
  |> yield(name: "5min_avg")
```

#### 15-Minute Moving Average
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)
  |> yield(name: "15min_avg")
```

#### Hourly Maximum
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: 1h, fn: max, createEmpty: false)
  |> yield(name: "hourly_max")
```

### Alerting Queries

#### High ROP Alert (> 100 ft/hr)
```flux
from(bucket: "sensor-data")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> filter(fn: (r) => r._value > 100.0)
  |> yield(name: "high_rop_alert")
```

#### Low WOB Alert (< 5 klbs)
```flux
from(bucket: "sensor-data")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "weight_on_bit_klbs")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> filter(fn: (r) => r._value < 5.0)
  |> yield(name: "low_wob_alert")
```

#### High Standpipe Pressure Alert (> 3000 psi)
```flux
from(bucket: "sensor-data")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "standpipe_pressure_psi")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> filter(fn: (r) => r._value > 3000.0)
  |> yield(name: "high_pressure_alert")
```

### Performance Queries

#### Data Points per Second
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> aggregateWindow(every: 1s, fn: count, createEmpty: false)
  |> yield(name: "data_points_per_second")
```

#### Data Quality Check (Null Values)
```flux
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "rate_of_penetration_ft_per_hr")
  |> filter(fn: (r) => r["well_id"] == "78B-32")
  |> filter(fn: (r) => exists r._value)
  |> count()
  |> yield(name: "valid_data_points")
```

## Query Optimization Tips

### 1. Use Appropriate Time Ranges
- Use `v.timeRangeStart` and `v.timeRangeStop` for dashboard queries
- Limit historical queries to necessary time periods
- Use relative time ranges (`-1h`, `-24h`) when possible

### 2. Filter Early and Often
- Apply measurement and field filters first
- Use tag filters to reduce data volume
- Filter by well_id to limit scope

### 3. Optimize Aggregations
- Use `aggregateWindow()` for time-based aggregations
- Choose appropriate aggregation functions (mean, max, min, sum)
- Set `createEmpty: false` to avoid gaps in data

### 4. Use Efficient Functions
- Prefer `last()` over `first()` for current values
- Use `count()` for data quality metrics
- Apply `group()` only when necessary

### 5. Monitor Query Performance
- Check query execution time in Grafana
- Use `yield()` to name query results
- Test queries in InfluxDB Data Explorer first

## Custom Dashboard Creation

### Step 1: Create New Dashboard
1. Go to Grafana → Dashboards → New Dashboard
2. Add new panel
3. Select InfluxDB as data source

### Step 2: Configure Query
1. Switch to Flux query language
2. Use queries from this reference
3. Adjust time ranges and filters as needed

### Step 3: Configure Visualization
1. Choose appropriate visualization type
2. Set units and thresholds
3. Configure colors and legends

### Step 4: Add Variables (Optional)
```flux
// Use dashboard variables
from(bucket: "sensor-data")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> filter(fn: (r) => r["_field"] == "${field}")
  |> filter(fn: (r) => r["well_id"] == "${well_id}")
  |> yield(name: "variable_query")
```

## Troubleshooting Queries

### Common Issues

1. **No Data Returned**
   - Check time range
   - Verify field and measurement names
   - Ensure data exists in the time range

2. **Slow Queries**
   - Reduce time range
   - Add more specific filters
   - Use aggregations to reduce data points

3. **Incorrect Results**
   - Verify field names match exactly
   - Check tag values (case-sensitive)
   - Validate aggregation functions

### Debug Queries

```flux
// Test basic connectivity
from(bucket: "sensor-data")
  |> range(start: -1h)
  |> limit(n: 10)
  |> yield(name: "connectivity_test")

// List available measurements
from(bucket: "sensor-data")
  |> range(start: -1h)
  |> group(columns: ["_measurement"])
  |> distinct(column: "_measurement")
  |> yield(name: "measurements")

// List available fields
from(bucket: "sensor-data")
  |> range(start: -1h)
  |> filter(fn: (r) => r["_measurement"] == "drilling_sensors")
  |> group(columns: ["_field"])
  |> distinct(column: "_field")
  |> yield(name: "fields")
```

This reference provides a comprehensive set of queries for building effective drilling data dashboards in Grafana. Customize the queries based on your specific requirements and data structure.
