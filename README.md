# Log Analyzer

A command-line Python tool that parses timestamped log files, summarizes log-level distribution, searches for keywords, and flags anomalous activity using both a rolling z-score and an Isolation Forest model.

## Features

- **Log parsing**: extracts the timestamp, level, and message from each line and skips malformed lines
- **Level distribution**: counts and percentages for each log level, plus a bar chart
- **Most frequent entries**: identifies the most common log level and the most repeated message
- **Keyword search**: case-insensitive search across log lines via `--search`
- **Time-series bucketing**: aggregates log levels into 5-minute intervals with per-level and total counts
- **Anomaly detection**:
  - *Rolling z-score* (statistical): flags buckets that deviate sharply from the recent trend
  - *Isolation Forest* (ML): flags unusual combinations of counts across levels
- **Summary export**: writes results to `summary.txt`

## Requirements

- Python 3.8+
- pandas
- numpy
- matplotlib
- scikit-learn

```bash
pip install pandas numpy matplotlib scikit-learn
```

## Usage

```bash
python log_analyzer.py <log_file> [--search WORD]
```

| Argument | Description |
|---|---|
| `log_file` | Path to the log file to analyze (required) |
| `--search` | Word or phrase to search for in log lines (optional, case-insensitive) |

### Examples

```bash
# Basic analysis
python log_analyzer.py app.log

# Analysis plus a keyword search
python log_analyzer.py app.log --search timeout
```

## Expected Log Format

Each line should begin with a date, a time, and a log level, followed by the message:

```
YYYY-MM-DD HH:MM:SS LEVEL message text...
```

Example:

```
2026-01-15 08:30:12 INFO Server started on port 8080
2026-01-15 08:31:45 WARNING Slow response from database
2026-01-15 08:32:01 ERROR Connection timeout
```

Supported levels: `INFO`, `DEBUG`, `ERROR`, `WARNING`, `FATAL`, `CRITICAL`.

Lines that have fewer than four whitespace-separated fields, an unparseable timestamp, or an unrecognized level are skipped.

## Output

**Console**
- 5-minute time-series table of level counts and totals
- Level counts, the most common level, and the most repeated message
- All lines matching the search term
- Percentage breakdown per level
- Z-score results (`*_zscore`, `*_is_anomaly` columns)
- Isolation Forest results (`iforest_anomaly`, `iforest_score` columns)

**Files**
- `summary.txt`: total lines, level counts, message counts, search matches, and level percentages (written to the current working directory and overwritten on each run)

**Plot**
- A bar chart of log-level distribution is displayed at the end

## How Anomaly Detection Works

### Rolling z-score
For each of `total`, `ERROR`, `WARNING`, `FATAL`, and `CRITICAL`, the script computes a rolling mean and standard deviation, then calculates a z-score for each bucket.

| Parameter | Default |
|---|---|
| `window` | 10 buckets |
| `threshold` | 2 (absolute z-score) |

A bucket is marked `*_is_anomaly = True` when its z-score exceeds the threshold. Windows with zero variance are ignored to avoid division by zero.

### Isolation Forest
An unsupervised scikit-learn model is trained on the per-bucket counts. Buckets that are easy to isolate from the rest are labeled anomalies.

| Parameter | Default |
|---|---|
| `contamination` | 0.1 (expects ~10% anomalies) |
| `random_state` | 42 |

Results appear in `iforest_anomaly` (boolean) and `iforest_score` (lower means more anomalous).

## Customization

- **Bucket size**: change the interval in `bucket_into_timeseries(records, "5min")`
- **Z-score sensitivity**: adjust `window` and `threshold` in `detect_anomalies_zscore`
- **Expected anomaly rate**: adjust `contamination` in `detect_anomalies_isolation_forest`
- **Monitored columns**: pass a custom `columns` list to either detection function
- **Accepted levels**: edit the `valid_levels` list

## Limitations

- Requires a display for `plt.show()`; on headless systems, swap it for `plt.savefig("log_levels.png")`
- Expects the timestamp format `YYYY-MM-DD HH:MM:SS`; other formats are skipped
- If no valid lines are found, the time-series step will fail on empty data
- The entire file is processed in one pass, with messages held in memory, so very large logs may need chunking

## Possible Future Improvements

- Save plots and anomaly tables to files
- Support additional timestamp formats and JSON logs
- Visualize anomalies on a timeline
- Normalize messages (strip IDs and numbers) before counting repeats
- Wrap the logic in functions and add unit tests
