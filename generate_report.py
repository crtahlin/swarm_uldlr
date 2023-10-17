import json
import yaml
import csv
import argparse

def load_settings(settings_path):
    with open(settings_path, 'r') as f:
        return yaml.safe_load(f)

def load_filelist(filelist_path):
    with open(filelist_path, 'r') as f:
        return json.load(f)

def calculate_speed_MBps(timestamp_start, timestamp_end, file_size_bytes):
    from datetime import datetime
    FMT = '%Y-%m-%d %H:%M:%S'
    tdelta = datetime.strptime(timestamp_end, FMT) - datetime.strptime(timestamp_start, FMT)
    duration_seconds = tdelta.total_seconds()
    file_size_MB = file_size_bytes / (1024 * 1024)
    
    if duration_seconds > 0:
        speed_MBps = file_size_MB / duration_seconds
        return round(speed_MBps, 2)
    else:
        return None  # To handle division by zero if timestamps are the same

def generate_csv_report(file_list, output_path):
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = [
            'filename', 'size', 'swarmHash', 'first uploaded', 'last uploaded',
            'last successful download', 'number of times successfully downloaded',
            'last successful download speed (MB/s)', 'last successful upload speed (MB/s)'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for file_info in file_list:
            successful_uploads = [attempt for attempt in file_info.get('upload_attempts', []) if 'error' not in attempt]
            successful_downloads = [attempt for attempt in file_info.get('download_attempts', []) if attempt.get('sha256_comparison') == 'Successful']

            # Get the speed of the last successful upload if available
            last_successful_upload = successful_uploads[-1] if successful_uploads else None
            last_upload_speed = None
            if last_successful_upload:
                last_upload_speed = calculate_speed_MBps(
                    last_successful_upload.get('timestamp_start', ''),
                    last_successful_upload.get('timestamp_end', ''),
                    file_info.get('size', 0)
                )
            
            # Get the speed of the last successful download if available
            last_successful_download = successful_downloads[-1] if successful_downloads else None
            last_download_speed = None
            if last_successful_download:
                last_download_speed = calculate_speed_MBps(
                    last_successful_download.get('timestamp_start', ''),
                    last_successful_download.get('timestamp_end', ''),
                    file_info.get('size', 0)
                )

            writer.writerow({
                'filename': file_info.get('filename', ''),
                'size': file_info.get('size', ''),
                'swarmHash': file_info.get('swarmHash', ''),
                'first uploaded': min([x.get('timestamp_end', '') for x in successful_uploads], default=''),
                'last uploaded': max([x.get('timestamp_end', '') for x in successful_uploads], default=''),
                'last successful download': max([x.get('timestamp_end', '') for x in successful_downloads], default=''),
                'number of times successfully downloaded': len(successful_downloads),
                'last successful download speed (MB/s)': last_download_speed,
                'last successful upload speed (MB/s)': last_upload_speed
            })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate CSV report.')
    parser.add_argument('-S', '--settings', help='Path to settings YAML file', default='settings.yaml')
    parser.add_argument('-F', '--filelist', help='Path to filelist JSON file', default=None)
    args = parser.parse_args()

    if args.filelist:
        filelist_path = args.filelist
    else:
        settings = load_settings(args.settings)
        filelist_path = settings['file_info_path']
    
    print(f"Generating report based on {filelist_path}.")
    
    file_list = load_filelist(filelist_path)
    
    output_path = 'report.csv'
    generate_csv_report(file_list, output_path)
    
    print(f"Report successfully generated and saved as {output_path}.")

