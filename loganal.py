import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
from sklearn.ensemble import IsolationForest
import argparse

parser = argparse.ArgumentParser(description="Analyze log files for level distribution and anomalies.")
parser.add_argument("log_file", help="Path to the log file")
parser.add_argument("--search", default="", help="Word to search for in log lines")
args = parser.parse_args()

log_file = args.log_file
word_search = args.search
log_levels = []
valid_levels = ["INFO", "DEBUG", "ERROR", "WARNING", "FATAL", "CRITICAL"]
matches = []
line_counter = {}
total_lines = 0

with open(log_file, "r") as file:
    records = [];
    for line in file:
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            dt = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        level = parts[2]
        if parts[2] not in valid_levels:
            continue
        records.append((dt, level))
        message = " ".join(parts[2:])
        if message in line_counter:
            line_counter[message] += 1
        else:
            line_counter[message] = 1
        level = parts[2]
        if word_search.lower() in line.lower():
            matches.append(line.strip())
        log_levels.append(level)
        total_lines += 1
def bucket_into_timeseries(records, interval="1min"):
    df = pd.DataFrame(records, columns=["timestamp", "level"])
    df.set_index("timestamp", inplace=True)
    level_counts = pd.get_dummies(df["level"]).resample(interval).sum()
    level_counts["total"] = df.resample(interval).size()
    return level_counts
total_per_bucket = bucket_into_timeseries(records, "5min")
print(total_per_bucket)
log_levels_counter = Counter(log_levels)
percentage_text= []
for level,count in log_levels_counter.items():
    log_level_percentage = count / total_lines * 100
    percentage_text.append(f"{level}: {log_level_percentage:.2f}%")
print(log_levels_counter)
print(max(log_levels_counter.items(), key=lambda x: x[1]))
print(max(line_counter.items(), key=lambda x: x[1]))
print(matches)
print(percentage_text)
with open('summary.txt', 'w') as fr:
     fr.write(f"Total lines: {total_lines}\n")
     fr.write(f"Log levels: {log_levels_counter}\n")
     fr.write(f"Line counter: {line_counter}\n")
     fr.write(f"Matches: {matches}\n")
     fr.write(f"Log level percentage: {percentage_text}\n")

def detect_anomalies_zscore(ts, columns=None, window=10, threshold=2):
    if columns is None:
        columns = ["total", "ERROR", "WARNING", "FATAL", "CRITICAL"]
    for col in columns:
        if col not in ts.columns:
            continue
        mean = ts[col].rolling(window).mean()
        std = ts[col].rolling(window).std()
        std = std.replace(0, np.nan)
        ts[f"{col}_zscore"] = (ts[col] - mean) / std
        ts[f"{col}_is_anomaly"] = ts[f"{col}_zscore"].abs() > threshold
    return ts

anomalies = detect_anomalies_zscore(total_per_bucket)
print(anomalies)

def detect_anomalies_isolation_forest(ts, columns=None, contamination=0.1, random_state=42):
    if columns is None:
        columns = ["total", "ERROR", "WARNING", "FATAL", "CRITICAL"]
    filtered = []
    for col in columns:
        if col in ts.columns:
            filtered.append(col)
    columns = filtered
    features = ts[columns].fillna(0).values
    model = IsolationForest(contamination=contamination, random_state=random_state)
    model.fit(features)
    model_predictions = model.predict(features)
    ts["iforest_anomaly"] = model_predictions == -1
    ts["iforest_score"] = model.decision_function(features)
    return ts

anomalies_isolation_forest = detect_anomalies_isolation_forest(total_per_bucket)
print(anomalies_isolation_forest)

df = pd.DataFrame(log_levels_counter.items(), columns=["Level", "Count"])

plt.figure(figsize=(10, 6))
plt.bar(df["Level"], df["Count"])
plt.xlabel("Log Level")
plt.ylabel("Count")
plt.title("Log Level Distribution")
plt.show()


