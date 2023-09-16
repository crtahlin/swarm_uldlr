#!/usr/bin/env python3
import os
import json
import yaml
import argparse
import subprocess
from datetime import datetime
import re

def load_settings(settings_path):
    with open(settings_path, 'r') as f:
        return yaml.safe_load(f)

def load_filelist(filelist_path):
    with open(filelist_path, 'r') as f:
        return json.load(f)

def save_filelist(filelist, filelist_path):
    with open(filelist_path, 'w') as f:
        json.dump(filelist, f, indent=4)

def upload_file(file_info, settings):
    cmd = ['swarm-cli', 'upload', file_info['full_path'], '--quiet']
    
    if settings.get('bee_api_endpoint'):
        cmd.extend(['--bee-api-url', settings['bee_api_endpoint']])
        
    cmd.extend([
        '--stamp', settings['stamp_id'],
        '--deferred', str(settings['deferred_upload']).lower(),
        '--curl'
    ])
    
    print(f"Working on file: {file_info['full_path']}")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if process.returncode == 0:
            response_body = stdout.decode('utf-8').strip()
            swarm_hash = re.search(r'([a-fA-F0-9]{64})$', response_body)
            if swarm_hash:
                file_info['swarmHash'] = swarm_hash.group(1)
            print(f"Successfully uploaded: {file_info['full_path']}")
            return {"timestamp": timestamp, "response_body": response_body}
        else:
            print(f"Failed to upload: {file_info['full_path']}")
            return {"timestamp": timestamp, "error": stderr.decode('utf-8').strip()}
            
    except Exception as e:
        print(f"An error occurred while uploading: {file_info['full_path']}")
        return {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "error": str(e)}

if __name__ == '__main__':
    successful_count = 0
    unsuccessful_count = 0
    total_data_uploaded = 0  # In bytes
    
    parser = argparse.ArgumentParser(description='Upload files.')
    parser.add_argument('-S', '--settings', help='Path to settings YAML file', default='settings.yaml')
    args = parser.parse_args()

    settings = load_settings(args.settings)
    file_list = load_filelist(settings['file_info_path'])

    upload_filter = settings.get('upload_filter', 'all')  # Default to 'all' if not specified

    for file_info in file_list:
        # Skip this file if we are uploading only 'pending' files and this file has a swarmHash
        if upload_filter == 'pending' and 'swarmHash' in file_info:
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

