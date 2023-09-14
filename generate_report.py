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

def generate_csv_report(file_list, output_path):
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['filename', 'size', 'swarmHash', 'first uploaded', 'last uploaded', 'last successful download', 'number of times successfully downloaded']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for file_info in file_list:
            successful_uploads = [attempt['timestamp'] for attempt in file_info.get('upload_attempts', []) if 'error' not in attempt]
            successful_downloads = [attempt['timestamp'] for attempt in file_info.get('download_attempts', []) if attempt.get('sha256_comparison') == 'Successful']

            writer.writerow({
                'filename': file_info.get('filename', ''),
                'size': file_info.get('size', ''),
                'swarmHash': file_info.get('swarmHash', ''),
                'first uploaded': min(successful_uploads, default=''),
                'last uploaded': max(successful_uploads, default=''),
                'last successful download': max(successful_downloads, default=''),
                'number of times successfully downloaded': len(successful_downloads)
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

