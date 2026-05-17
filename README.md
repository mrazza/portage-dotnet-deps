# Portage .NET NuGet Dependency Generator

A Python script to automate the generation of NuGet dependencies for Gentoo Linux ebuilds using the `dotnet-pkg.eclass`.

## Overview

When creating a Gentoo ebuild for a .NET application, you need to list all NuGet dependencies (including transitive ones) in a `NUGETS` variable. This ensures the build is network-isolated and reproducible.

`generate_ebuild_nugets.py` simplifies this by:
1. Running `dotnet restore` on your project/solution to resolve all dependencies.
2. Parsing the generated `project.assets.json` files.
3. Extracting and formatting the dependencies into the `PackageName@Version` format used by Gentoo.
4. Optionally updating an existing `.ebuild` file directly.

## Prerequisites

- Python 3.x
- .NET SDK (installed and in your `PATH`)

## Installation

Simply download the `generate_ebuild_nugets.py` script and make it executable:

```bash
chmod +x generate_ebuild_nugets.py
```

## Usage

### Generate NUGETS block

To generate the `NUGETS` block for a project and print it to the console:

```bash
./generate_ebuild_nugets.py /path/to/your/project_or_solution
```

If no path is provided, it defaults to the current directory.

### Update an existing Ebuild

To update the `NUGETS` variable in an existing Gentoo ebuild file:

```bash
./generate_ebuild_nugets.py /path/to/your/project --ebuild /usr/local/portage/app-misc/my-app/my-app-1.0.0.ebuild
```

The script will:
- Replace the existing `NUGETS="..."` block if found.
- Insert a new `NUGETS` block before the `inherit` line if not found.
- Append to the end of the file if neither is found.

## License

This project is licensed under the Apache License, Version 2.0. See the [LICENSE](LICENSE) file for details.
