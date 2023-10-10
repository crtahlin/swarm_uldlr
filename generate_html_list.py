import json
import yaml
import os

def load_settings(settings_path):
    with open(settings_path, 'r') as f:
        return yaml.safe_load(f)

def load_filelist(filelist_path):
    with open(filelist_path, 'r') as f:
        return json.load(f)

def load_text_from_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()

def generate_html(settings, file_list):
    html = []
    html.append(f"<html>")
    html.append(f"<head>")
    html.append(f"<title>{settings['page_title']}</title>")
    
    if settings.get('page_css_styles'):
        css_content = load_text_from_file(settings['page_css_styles'])
        html.append(f"<style>{css_content}</style>")
    
    html.append(f"</head>")
    html.append(f"<body>")
    html.append(f"<table>")
    html.append(f"<tr><th>File Name</th><th>Swarm Reference Hash</th><th>Size in MB</th></tr>")
    
    for file_info in file_list:
        if 'swarmHash' in file_info:
            file_size_MB = round(file_info['size'] / (1024 * 1024), 2)
            html.append(f"<tr>")
            html.append(f"<td>{file_info['filename']}</td>")
            html.append(f'<td><a href="{settings["swarm_gateway"]}{file_info["swarmHash"]}">{file_info["swarmHash"]}</a></td>')
            html.append(f"<td>{file_size_MB}</td>")
            html.append(f"</tr>")
    
    html.append(f"</table>")
    
    if settings.get('page_footer'):
        footer_content = load_text_from_file(settings['page_footer'])
        html.append(f"<div>{footer_content}</div>")
    
    html.append(f"</body>")
    html.append(f"</html>")
    
    return '\n'.join(html)

if __name__ == '__main__':
    settings = load_settings('settings.yaml')
    file_list = load_filelist(settings['file_info_path'])
    html_content = generate_html(settings, file_list)
    
    with open('generated_page.html', 'w') as f:
        f.write(html_content)

