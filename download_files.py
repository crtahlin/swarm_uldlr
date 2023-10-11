#!/usr/bin/env python3
import os
import json
import yaml
import argparse
import subprocess
from datetime import datetime
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

def download_file(file_info, settings):
    timestamp_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Working on file: {file_info['filename']}")

    cmd = ['swarm-cli', 'download', file_info['swarmHash'], settings['download_location_path'], '--quiet', '--curl']
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        timestamp_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        download_path = os.path.join(settings['download_location_path'], file_info['filename'])
        calculated_hash = calculate_sha256(download_path)
        
        sha256_comparison = "Failed" if calculated_hash != file_info['sha256'] else "Successful"
        
        return {
            "timestamp_start": timestamp_start,
            "timestamp_end": timestamp_end,
            "sha256_comparison": sha256_comparison,
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

    for file_info in file_list:
        download_attempt = download_file(file_info, settings)

        file_info.setdefault('download_attempts', []).append(download_attempt)
        
        if download_attempt['error']:
            print(f"Download failed for: {file_info['filename']}")
            unsuccessful_count += 1
            
        else:
            successful_count += 1
            if download_attempt['sha256_comparison'] == "Failed":
                print(f"SHA-256 comparison failed for: {file_info['filename']}")
                sha256_failed_count += 1

        save_filelist(file_list, settings['file_info_path'])

    print(f"\nDownload Summary:")
    print(f"Successfully downloaded: {successful_count} files")
    print(f"Failed to download: {unsuccessful_count} files")
    print(f"SHA-256 comparison failed: {sha256_failed_count} files")


