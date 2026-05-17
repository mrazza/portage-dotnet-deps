#!/usr/bin/env python3
#
# Copyright 2026 mrazza
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import argparse
import json
import os
import re
import subprocess
import sys

def get_nugets(target_path):
    """Runs dotnet restore and extracts NuGet dependencies from project.assets.json files."""
    # 1. Run dotnet restore
    print(f"Running 'dotnet restore' on {target_path}...", file=sys.stderr)
    try:
        # Run restore. We use --force to ensure project.assets.json is updated/recreated.
        subprocess.run(["dotnet", "restore", target_path], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: 'dotnet restore' failed:\n{e.stderr.decode()}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'dotnet' command not found. Please ensure .NET SDK is installed.", file=sys.stderr)
        sys.exit(1)

    # 2. Find project.assets.json files
    assets_files = []
    search_dir = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)
    if not search_dir:
        search_dir = "."

    for root, dirs, files in os.walk(search_dir):
        if "project.assets.json" in files:
            assets_files.append(os.path.join(root, "project.assets.json"))

    if not assets_files:
        print("Error: No project.assets.json files found. Ensure 'dotnet restore' was successful.", file=sys.stderr)
        sys.exit(1)

    # 3. Parse packages
    nugets = set()
    for assets_file in assets_files:
        with open(assets_file, 'r') as f:
            try:
                data = json.load(f)
                libraries = data.get("libraries", {})
                for lib_id, lib_info in libraries.items():
                    if lib_info.get("type") == "package":
                        # lib_id is "PackageName/Version"
                        if "/" in lib_id:
                            name_ver = lib_id.replace("/", "@")
                            nugets.add(name_ver)
            except json.JSONDecodeError:
                print(f"Warning: Failed to parse {assets_file}", file=sys.stderr)

    return sorted(list(nugets))

def format_nugets_block(nugets):
    """Formats the list of nugets into a Bash variable block."""
    if not nugets:
        return 'NUGETS=""'
    
    block = 'NUGETS="\n'
    for n in nugets:
        block += f"    {n}\n"
    block += '"'
    return block

def update_ebuild(ebuild_path, nugets_block):
    """Updates the NUGETS variable in an ebuild file, or appends it."""
    if not os.path.exists(ebuild_path):
        print(f"Error: Ebuild file {ebuild_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(ebuild_path, 'r') as f:
        content = f.read()

    # Regex to find NUGETS="..." block.
    # Matches NUGETS=" followed by anything (including newlines) until " at the start of a line or end of block.
    pattern = re.compile(r'^NUGETS=".*?"', re.MULTILINE | re.DOTALL)
    
    if pattern.search(content):
        new_content = pattern.sub(nugets_block, content)
        print(f"Updating existing NUGETS block in {ebuild_path}...")
    else:
        # If NUGETS doesn't exist, try to insert it before inherit
        if "inherit " in content:
            new_content = content.replace("inherit ", f"{nugets_block}\n\ninherit ", 1)
            print(f"Inserting NUGETS block before 'inherit' in {ebuild_path}...")
        else:
            new_content = content + f"\n\n{nugets_block}\n"
            print(f"Appending NUGETS block to {ebuild_path}...")

    with open(ebuild_path, 'w') as f:
        f.write(new_content)
    
    print(f"Successfully updated {ebuild_path}.")

def main():
    parser = argparse.ArgumentParser(description="Generate Gentoo NUGETS variable for an ebuild.")
    parser.add_argument("path", nargs="?", default=".", help="Path to dotnet project, solution or directory (default: current directory).")
    parser.add_argument("--ebuild", help="Path to an existing ebuild file to update.")
    
    args = parser.parse_args()
    
    nugets = get_nugets(args.path)
    nugets_block = format_nugets_block(nugets)
    
    if args.ebuild:
        update_ebuild(args.ebuild, nugets_block)
    else:
        print(nugets_block)

if __name__ == "__main__":
    main()
