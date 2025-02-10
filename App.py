from flask import Flask, render_template, request, redirect, url_for
import plotly.express as px
import pandas as pd
from collections import Counter
import re
import os
import requests

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads' 


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


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


@app.route('/', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                log_data = parse_log_file(file_path)
        # Check if a URL was provided
        elif 'url' in request.form:
            url = request.form['url']
            response = requests.get(url)
            if response.status_code == 200:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'log_from_url.txt')
                with open(file_path, 'w') as f:
                    f.write(response.text)
                log_data = parse_log_file(file_path)
            else:
                return "Failed to fetch log data from the URL."
        else:
            return "No file or URL provided."

        # Generate IP address histogram
        ip_counter = generate_ip_histogram(log_data)
        ip_df = pd.DataFrame(ip_counter.most_common(), columns=['IP Address', 'Occurrences'])

        # Generate hourly traffic histogram
        hour_counter = generate_hourly_traffic_histogram(log_data)
        hour_df = pd.DataFrame(sorted(hour_counter.items()), columns=['Hour', 'Visitors'])

        # Generate IPs contributing to 85% of traffic
        ips_85_percent = get_ips_for_85_percent_traffic(ip_counter)

        # Generate hours contributing to 70% of traffic
        hours_70_percent = get_hours_for_70_percent_traffic(hour_counter)

        # Create Plotly charts
        # Improved IP Address Histogram
        ip_fig = px.bar(
            ip_df,
            x='IP Address',
            y='Occurrences',
            title='<b>IP Address Histogram</b>',
            labels={'Occurrences': 'Number of Occurrences', 'IP Address': 'IP Address'},
            color='Occurrences',  # Add color gradient
            color_continuous_scale='Viridis',  # Use a color scale
            text='Occurrences'  # Display count on bars
        )
        ip_fig.update_traces(
            textposition='outside',  # Move text outside bars
            marker_line_color='black',  # Add black borders to bars
            marker_line_width=1.5  # Border width
        )
        ip_fig.update_layout(
            xaxis_tickangle=-45,  # Rotate x-axis labels for better readability
            xaxis_title='IP Address',
            yaxis_title='Number of Occurrences',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            font=dict(size=12, color='black')  # Font settings
        )

        # Hourly Traffic Histogram
        hour_fig = px.bar(
            hour_df,
            x='Hour',
            y='Visitors',
            title='<b>Hourly Traffic Histogram</b>',
            labels={'Visitors': 'Number of Visitors', 'Hour': 'Hour of the Day'},
            color='Visitors',  # Add color gradient
            color_continuous_scale='Plasma',  # Use a color scale
            text='Visitors'  # Display count on bars
        )
        hour_fig.update_traces(
            textposition='outside',  # Move text outside bars
            marker_line_color='black',  # Add black borders to bars
            marker_line_width=1.5  # Border width
        )
        hour_fig.update_layout(
            xaxis_title='Hour of the Day',
            yaxis_title='Number of Visitors',
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
            font=dict(size=12, color='black')  # Font settings
        )

        # Convert charts to HTML
        ip_graph = ip_fig.to_html(full_html=False)
        hour_graph = hour_fig.to_html(full_html=False)

        # Render the dashboard template
        return render_template('dashboard.html', ip_graph=ip_graph, hour_graph=hour_graph,
                              ips_85_percent=ips_85_percent, hours_70_percent=hours_70_percent)

    return render_template('upload.html')

if __name__ == "__main__":
    app.run(debug=True)