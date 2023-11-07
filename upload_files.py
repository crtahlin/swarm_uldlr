#!/usr/bin/env python3
import os
import json
import yaml
import argparse
import subprocess
from datetime import datetime
import re
import tempfile
import shutil

def load_settings(settings_path):
    with open(settings_path, 'r') as f:
        return yaml.safe_load(f)

def load_filelist(filelist_path):
    with open(filelist_path, 'r') as f:
        return json.load(f)

def save_filelist(filelist, filelist_path):
    with tempfile.NamedTemporaryFile('w', dir=os.path.dirname(filelist_path), delete=False) as tempf:
        json.dump(filelist, tempf, indent=4)
    shutil.move(tempf.name, filelist_path)
    
    
# Function to calculate duration and average speed
def calculate_duration_and_speed(timestamp_start, timestamp_end, file_size_bytes):
    try:
        start_time = datetime.strptime(timestamp_start, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(timestamp_end, "%Y-%m-%d %H:%M:%S")
        duration = (end_time - start_time).total_seconds()
        file_size_MB = file_size_bytes / (1024 * 1024)
        avg_speed = file_size_MB / duration if duration > 0 else 0
        return round(file_size_MB, 2), round(avg_speed, 2)
    except Exception as e:
        return None, None

def upload_file(file_info, settings):
    timestamp_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmd = [
        '/usr/bin/time', '-f', '"%e real,%U user,%S sys,%M KB max memory"', # Formatting for time output
        'swarm-cli', 'upload', file_info['full_path'],
        '--quiet',
        '--stamp', settings['stamp_id'],
        '--deferred', str(settings['deferred_upload']).lower(),
        '--curl',
        '--yes'
    ]

    
    if settings.get('bee_api_endpoint'):
        cmd.extend(['--bee-api-url', settings['bee_api_endpoint']])
        
    cmd.extend([
        '--stamp', settings['stamp_id'],
        '--deferred', str(settings['deferred_upload']).lower(),
        '--curl',
        '--yes'
    ])
    
    print(f"Working on file: {file_info['full_path']}  start: {timestamp_start}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = process.communicate()

        timestamp_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_size_MB, avg_speed = calculate_duration_and_speed(timestamp_start, timestamp_end, file_info['size']) 

        # Process the output
        time_output, swarm_output = output.decode('utf-8').rsplit('\n', 1) # Assuming the last line is time output
        print(f"Time metrics: {time_output}")
        print(f"Swarm output: {swarm_output.strip()}")

        if process.returncode == 0:
            response_body = stdout.decode('utf-8').strip()
            swarm_hash = re.search(r'([a-fA-F0-9]{64})$', response_body)
            if swarm_hash:
                file_info['swarmHash'] = swarm_hash.group(1)
            print(f"Successfully uploaded: {file_info['full_path']}  end: {timestamp_end}  Size: {file_size_MB} MB  Average speed: {avg_speed} MB/s")
            return {"timestamp_start": timestamp_start,
                    "timestamp_end": timestamp_end,
                    "time_metrics": time_output.strip(),
                    "response_body": stdout.decode('utf-8').strip()}
        else:
            print(f"Failed to upload: {file_info['full_path']}  end: {timestamp_end}  Size: {file_size_MB} MB")
            return {"timestamp_start": timestamp_start,
                    "timestamp_end": timestamp_end,
                    "time_metrics": time_output.strip(),
                    "error": stderr.decode('utf-8').strip()}
            
    except Exception as e:
        timestamp_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"An error occurred while uploading: {file_info['full_path']}  end: {timestamp_end}  Size: {file_size_MB} MB")
        return {"timestamp_start": timestamp_start,
                "timestamp_end": timestamp_end,
                "error": str(e)}

if __name__ == '__main__':
    try:
        successful_count = 0
        unsuccessful_count = 0
        total_data_uploaded = 0  # In bytes
        
        parser = argparse.ArgumentParser(description='Upload files.')
        parser.add_argument('-S', '--settings', help='Path to settings YAML file', default='settings.yaml')
        args = parser.parse_args()

        settings = load_settings(args.settings)
        file_list = load_filelist(settings['file_info_path'])
    
        upload_filter = settings.get('upload_filter', 'all')  # Default to 'all' if not specified
        
        # This would get the max_file_size setting from the YAML file
        max_file_size = settings.get('max_file_size', float('inf'))  # Use a large number as the default
    
        for file_info in file_list:
            # Skip this file if we are uploading only 'pending' files and this file has a swarmHash
            if upload_filter == 'pending' and 'swarmHash' in file_info:
                continue
            if file_info['size'] > max_file_size:
                print(f"Skipping {file_info['filename']} due to size exceeding max_file_size.")
                continue
        
            upload_attempt = upload_file(file_info, settings)
        
            if "error" not in upload_attempt:
                successful_count += 1
                total_data_uploaded += file_info['size']
                file_info.setdefault('upload_attempts', []).append(upload_attempt)  # Set default for 'upload_attempts' if not exists
            else:
                unsuccessful_count += 1
                file_info.setdefault('upload_attempts', []).append(upload_attempt)  # Set default for 'upload_attempts' if not exists
            
            save_filelist(file_list, settings['file_info_path'])
    
        total_data_uploaded_MB = total_data_uploaded / (1024 * 1024)
        print(f"\nSuccessfully uploaded {successful_count} files.")
        print(f"Failed to upload {unsuccessful_count} files.")
        print(f"Total data uploaded: {total_data_uploaded_MB:.2f} MBytes")
    except KeyboardInterrupt:
        print("CTRL-C detected. Attempting to save JSON file before exiting.")
        save_filelist(file_list, settings['file_info_path'])
        print("JSON file saved. Exiting now.")

