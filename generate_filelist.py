#!/usr/bin/env python3
import os
import json
import hashlib
import argparse

def sha256(file_path):
    """Generate SHA-256 hash of a file."""
    print(f"Processing {file_path}...")
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_filelist(folder_path, recursive, output_filename):
    """Generate a JSON file containing file information."""
    file_list = []
    
    for root, _, files in os.walk(folder_path):
        if not recursive and root != folder_path:
            continue
        for file in files:
            full_path = os.path.join(root, file)
            file_info = {
                "full_path": full_path,
                "filename": file,
                "sha256": sha256(full_path),
                "size": os.path.getsize(full_path)
            }
            file_list.append(file_info)
    
    with open(output_filename, "w") as f:
        json.dump(file_list, f, indent=4)
        print(f"File list generated: {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a file list with metadata.")
    parser.add_argument("path", type=str, help="Path to the folder.")
    parser.add_argument("-R", "--recursive", action="store_true", help="Look into subfolders.")
    parser.add_argument("-F", "--filename", type=str, default="filelist.json", help="Output filename for JSON.")
    
    args = parser.parse_args()
    
    generate_filelist(args.path, args.recursive, args.filename)

