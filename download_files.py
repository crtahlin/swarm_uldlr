#!/usr/bin/env python3
import os
import json
import yaml
import argparse
import subprocess
from datetime import datetime, timedelta
import hashlib

def load_settings(settings_path):
    with open(settings_path, 'r') as f:
        return yaml.safe_load(f)

def load_filelist(filelist_path):
    with open(filelist_path, 'r') as f:
        return json.load(f)
        
def calculate_sha256(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            hasher.update(chunk)
    return hasher.hexdigest()
    
def save_filelist(filelist, filelist_path):
    with open(filelist_path, 'w') as f:
        json.dump(filelist, f, indent=4)
        
def calculate_duration_and_speed(timestamp_start, timestamp_end, file_size_bytes):
    FMT = '%Y-%m-%d %H:%M:%S'
    tdelta = datetime.strptime(timestamp_end, FMT) - datetime.strptime(timestamp_start, FMT)
    duration_seconds = tdelta.total_seconds()
    file_size_MB = file_size_bytes / (1024 * 1024)
    if duration_seconds > 0:
        avg_speed = file_size_MB / duration_seconds
    else:
        avg_speed = 0  # Avoid division by zero
    return file_size_MB, avg_speed


def download_file(file_info, settings):
    timestamp_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_size_MB = file_info['size'] / (1024 * 1024)
    
    print(f"Working on file: {file_info['filename']}  start: {timestamp_start}  file size: {file_size_MB:.2f} MB")

    # Modified command to include the 'time' utility
    cmd = [
        '/usr/bin/time', '-f', '"%e real,%U user,%S sys,%M KB max memory,%P CPU"', # Formatting for time output
        'swarm-cli', 'download', file_info['swarmHash'], '--output', os.path.join(settings['download_location_path'], file_info['filename']),
        '--quiet', '--curl'

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        timestamp_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        download_path = os.path.join(settings['download_location_path'], file_info['filename'])
        calculated_hash = calculate_sha256(download_path)
        
        sha256_comparison = "Failed" if calculated_hash != file_info['sha256'] else "Successful"

        # Assuming the last line in stderr is the time utility output
        time_output = stderr.decode('utf-8').strip().split('\n')[-1]

        print(f"Time metrics: {time_output}")  # Print the time metrics

        return {
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "sha256_comparison": sha256_comparison,
            "time_metrics": time_output,  # Save the time metrics
            "response_body": stdout.decode('utf-8').strip(),
            "error": stderr.decode('utf-8').strip() if process.returncode != 0 else None
        }
        
    except Exception as e:
        timestamp_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "sha256_comparison": "Failed",
            "error": str(e)
        }

# Main script
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download files.')
    parser.add_argument('-S', '--settings', help='Path to settings YAML file', default='settings.yaml')
    args = parser.parse_args()

    settings = load_settings(args.settings)
    file_list = load_filelist(settings['file_info_path'])

    # ... (Check and create download directory)

    successful_count = 0
    unsuccessful_count = 0
    sha256_failed_count = 0

try:
        for file_info in file_list:
            if 'swarmHash' not in file_info:
                print(f"Skipping {file_info['filename']} as it does not have a Swarm hash.")
                continue

            download_attempt = download_file(file_info, settings)
            timestamp_start = download_attempt.get('timestamp_start', '')
            timestamp_end = download_attempt.get('timestamp_end', '')
        
            # Record this download attempt in the file_info dictionary
            file_info.setdefault('download_attempts', []).append(download_attempt)  # Add this line

            # Calculate file size in MB and average speed in MB/s
            file_size_MB, avg_speed = calculate_duration_and_speed(timestamp_start, timestamp_end, file_info['size'])

            if download_attempt.get('error'):
                print(f"Download failed for: {file_info['filename']}  Error: {download_attempt['error']}")
                unsuccessful_count += 1
            else:
                print(f"Successfully downloaded: {file_info['filename']}  end: {timestamp_end}  average speed: {avg_speed:.2f} MB/s")
                successful_count += 1

            save_filelist(file_list, settings['file_info_path'])

        print(f"\nDownload Summary:")
        print(f"Successfully downloaded: {successful_count} files")
        print(f"Failed to download: {unsuccessful_count} files")
        print(f"SHA-256 comparison failed: {sha256_failed_count} files")

except KeyboardInterrupt:
    print("\nCTRL-C detected. Attempting to save JSON file before exiting.")
    save_filelist(file_list, settings['file_info_path'])
    print(f"Download Summary:")
    print(f"Successfully downloaded: {successful_count} files")
    print(f"Failed to download: {unsuccessful_count} files")
    print(f"SHA-256 comparison failed: {sha256_failed_count} files")
    print("JSON file saved. Exiting now.")

