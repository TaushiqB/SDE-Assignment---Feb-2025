from flask import Flask, render_template
import plotly.express as px
import pandas as pd
from collections import Counter
import re

app = Flask(__name__)


def parse_log_file(file_path):
    ip_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)')
    hour_pattern = re.compile(r'\[\d{2}/\w+/\d{4}:(\d{2}):\d{2}:\d{2}')
    log_data = []

    with open(file_path, 'r') as file:
        for line in file:
            ip_match = ip_pattern.search(line)
            hour_match = hour_pattern.search(line)
            if ip_match and hour_match:
                ip = ip_match.group(1)
                hour = hour_match.group(1)
                log_data.append((ip, hour))
    return log_data


def generate_ip_histogram(log_data):
    ip_counter = Counter()
    for ip, _ in log_data:
        ip_counter[ip] += 1
    return ip_counter


def generate_hourly_traffic_histogram(log_data):
    hour_counter = Counter()
    for _, hour in log_data:
        hour_counter[hour] += 1
    return hour_counter


def get_ips_for_85_percent_traffic(ip_counter):
    total_requests = sum(ip_counter.values())
    sorted_ips = sorted(ip_counter.items(), key=lambda x: x[1], reverse=True)
    cumulative_requests = 0
    result_ips = []
    for ip, count in sorted_ips:
        cumulative_requests += count
        result_ips.append(ip)
        if cumulative_requests >= 0.85 * total_requests:
            break
    return result_ips


def get_hours_for_70_percent_traffic(hour_counter):
    total_requests = sum(hour_counter.values())
    sorted_hours = sorted(hour_counter.items(), key=lambda x: x[1], reverse=True)
    cumulative_requests = 0
    result_hours = []
    for hour, count in sorted_hours:
        cumulative_requests += count
        result_hours.append(hour)
        if cumulative_requests >= 0.70 * total_requests:
            break
    return result_hours


@app.route('/')
def dashboard():
    file_path = 'apache_combined.log.txt'  

    
    log_data = parse_log_file(file_path)

    
    ip_counter = generate_ip_histogram(log_data)
    ip_df = pd.DataFrame(ip_counter.most_common(), columns=['IP Address', 'Occurrences'])

    
    hour_counter = generate_hourly_traffic_histogram(log_data)
    hour_df = pd.DataFrame(sorted(hour_counter.items()), columns=['Hour', 'Visitors'])

    
    ips_85_percent = get_ips_for_85_percent_traffic(ip_counter)

    
    hours_70_percent = get_hours_for_70_percent_traffic(hour_counter)

    
    ip_fig = px.bar(ip_df, x='IP Address', y='Occurrences', title='IP Address Histogram')
    hour_fig = px.bar(hour_df, x='Hour', y='Visitors', title='Hourly Traffic Histogram')

    
    ip_graph = ip_fig.to_html(full_html=False)
    hour_graph = hour_fig.to_html(full_html=False)

    
    return render_template('dashboard.html', ip_graph=ip_graph, hour_graph=hour_graph,
                          ips_85_percent=ips_85_percent, hours_70_percent=hours_70_percent)

if __name__ == "__main__":
    app.run(debug=True)