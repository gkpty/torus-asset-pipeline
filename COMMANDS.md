# Torus Asset Pipeline CLI Commands

This document describes all available commands in the Torus Asset Pipeline CLI tool.

## Overview

The Torus Asset Pipeline CLI provides a command-line interface for managing various asset pipeline operations. All commands are built using Typer and provide helpful documentation and error handling.

## Installation

Before using the CLI, install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the CLI using Python:

```bash
python cli.py <command> [options]
```

Or make it executable and run directly:

```bash
chmod +x cli.py
./cli.py <command> [options]
```

## Commands

### `download`

Download photos from a Google Drive folder and organize them by supplier and SKU.

#### Description

This command will:
1. Authenticate with Google Drive API
2. List all suppliers found in the folder
3. Ask for confirmation (unless `--yes` flag is used)
4. Download all images from all suppliers
5. Organize them by supplier/SKU structure
6. Keep original file formats (no conversion)

If `FOLDER_ID` and `MODEL` are not provided, they will be loaded from `config.yaml`.

#### Usage

```bash
python cli.py download [FOLDER_ID] [MODEL] [OPTIONS]
```

#### Arguments

- `FOLDER_ID` (optional): Google Drive folder ID to download from (uses config default if not provided)
- `MODEL` (optional): Model type (e.g., 'products') (uses config default if not provided)

#### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output-dir` | `-o` | Output directory for downloaded files | Uses config default |
| `--credentials` | `-c` | Path to Google Drive API credentials file | Uses config default |
| `--verbose` | `-v` | Enable verbose output | Uses config default |
| `--yes` | `-y` | Skip confirmation and download all suppliers automatically | `False` |

#### Examples

**Basic download using config defaults:**
```bash
python cli.py download
```

**Basic download with specific folder and model:**
```bash
python cli.py download 1MYjcWKn-agKMhVBNTqzrFOvzsU1-ygNp products
```

**Download with custom output directory:**
```bash
python cli.py download 1MYjcWKn-agKMhVBNTqzrFOvzsU1-ygNp products --output-dir ./my-photos
```

**Download with verbose output:**
```bash
python cli.py download 1MYjcWKn-agKMhVBNTqzrFOvzsU1-ygNp products --verbose
```

**Download without confirmation (automated):**
```bash
python cli.py download 1MYjcWKn-agKMhVBNTqzrFOvzsU1-ygNp products --yes
```

**Download with custom credentials file:**
```bash
python cli.py download 1MYjcWKn-agKMhVBNTqzrFOvzsU1-ygNp products --credentials ./my-credentials.json
```

**Combined options:**
```bash
python cli.py download 1MYjcWKn-agKMhVBNTqzrFOvzsU1-ygNp products --output-dir ./downloads --verbose --yes
```

#### Output Structure

The download command creates the following directory structure:

```
{output_dir}/
├── {supplier_name_1}/
│   ├── {sku_1}/
│   │   ├── image1.jpg
│   │   ├── image2.png
│   │   └── ...
│   ├── {sku_2}/
│   │   └── ...
│   └── ...
├── {supplier_name_2}/
│   └── ...
└── ...
```

#### Prerequisites

1. **Google Drive API Credentials**: You need a `credentials.json` file with Google Drive API credentials. This file should be placed in the project root or specify the path using the `--credentials` option.

2. **Google Drive Folder Access**: The folder ID you provide must be accessible with your Google Drive API credentials.

#### Error Handling

- If the credentials file is not found, the command will exit with an error message
- If authentication fails, the command will display the error and exit
- If no suppliers are found in the specified folder, the command will inform you and exit
- If you cancel the confirmation prompt, the command will exit gracefully

### `config`

Show current configuration settings loaded from `config.yaml`.

#### Usage

```bash
python cli.py config
```

#### Description

This command displays the current configuration settings, including:
- Google Drive folder IDs and credentials file
- Output directories for different operations
- Download settings and behavior
- Logging configuration

#### Output

```
Current Configuration:
==================================================
Google Drive:
  Credentials file: credentials.json
  Folder IDs:
    product_photos: 1MYjcWKn-agKMhVBNTqzrFOvzsU1-ygNp

Output Directories:
  Base: ./output
  Product Photos: ./photos/products
  Category Images: ./photos/categories
  Models: ./models
  Reports: ./reports

Download Settings:
  Default Model: products
  Convert to JPG: false
  Ask Confirmation: true

Logging:
  Level: INFO
  Verbose: false
```

### `list`

List available commands and their descriptions.

#### Usage

```bash
python cli.py list
```

#### Description

This command displays all available commands in the CLI with brief descriptions.

#### Output

```
Available commands:
  download  - Download photos from Google Drive
  download-fast - Fast parallel download with threading
  download-categories - Download photos for categories and subcategories
  report    - Generate comprehensive photo analysis report
  convert   - Convert non-JPEG photos to JPEG format
  rename    - Rename photos to sequential format
  config    - Show current configuration settings
  list      - List available commands
  help      - Show help for a specific command
```

### `help`

Show help for a specific command.

#### Usage

```bash
python cli.py help <command>
```

#### Examples

```bash
python cli.py help download
python cli.py help list
```

## Global Options

All commands support these global options:

| Option | Description |
|--------|-------------|
| `--help` | Show help message and exit |
| `--version` | Show version and exit (if available) |

## Getting Help

- Use `python cli.py --help` to see all available commands
- Use `python cli.py <command> --help` to see help for a specific command
- Use `python cli.py list` to see a quick overview of commands

## Configuration

The CLI uses a `config.yaml` file for default settings. This allows you to set up your preferred folder IDs, output directories, and other settings once, then use the CLI without specifying them every time.

### Configuration File

The `config.yaml` file contains settings for:

- **Google Drive**: Folder IDs for different operations and credentials file path
- **Output Directories**: Default paths for different types of downloads
- **Download Settings**: Default model, image processing options, and behavior
- **Logging**: Log level and verbose output settings
- **Processing**: Batch sizes, retry settings, and concurrency limits
- **File Organization**: Directory structure templates and naming patterns
- **Validation**: Allowed file types, size limits, and integrity checks

### Google Drive API Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API
4. Create credentials (OAuth 2.0 Client ID)
5. Download the credentials JSON file
6. Update the `google_drive.credentials_file` path in `config.yaml`

### Using Configuration

**With config file (recommended):**
```bash
# Uses settings from config.yaml
python cli.py download

# Override specific settings
python cli.py download --output-dir ./custom-output
```

**Without config file:**
```bash
# Specify all required parameters
python cli.py download 1MYjcWKn-agKMhVBNTqzrFOvzsU1-ygNp products --output-dir ./photos/products
```

### Environment Variables

You can set these environment variables to customize behavior:

- `TORUS_CONFIG_FILE`: Path to custom config file (default: `config.yaml`)
- `TORUS_CREDENTIALS_FILE`: Override credentials file path
- `TORUS_OUTPUT_DIR`: Override default output directory

## Troubleshooting

### Common Issues

1. **"Credentials file not found"**
   - Ensure `credentials.json` exists in the project root
   - Or specify the correct path with `--credentials`

2. **"Authentication failed"**
   - Check that your credentials file is valid
   - Ensure the Google Drive API is enabled in your Google Cloud project

3. **"No suppliers found"**
   - Verify the folder ID is correct
   - Check that the folder contains subfolders (suppliers)
   - Ensure you have access to the folder

4. **"Permission denied"**
   - Check file system permissions for the output directory
   - Ensure you have write access to the specified location

### Debug Mode

Use the `--verbose` flag to get detailed output about the download process:

```bash
python cli.py download <FOLDER_ID> <MODEL> --verbose
```

This will show:
- Detailed progress information
- File-by-file download status
- SKU processing details
- Error messages with more context

## Future Commands

Additional commands are planned for future releases:

- `organize` - Organize downloaded photos
- `convert` - Convert images to different formats
- `rename` - Rename files according to patterns
- `report` - Generate reports on downloaded assets
- `upload` - Upload processed assets to cloud storage

## Contributing

To add new commands to the CLI:

1. Create a new function in `cli.py` with the `@app.command()` decorator
2. Add the command to the `list` command output
3. Update this documentation
4. Test the command thoroughly

## download-categories

Download photos for categories and subcategories from Google Drive lifestyle photos.

### Usage
```bash
python cli.py download-categories <action> [target] [OPTIONS]
```

### Arguments
- `action`: Action to perform - 'subcategories', 'categories', 'subcategories-all', 'categories-all', 'all', or 'list'
- `target`: Specific subcategory or category name (required for subcategories/categories actions)

### Options
- `--lifestyle-folder`, `-l`: Google Drive lifestyle photos folder ID
- `--output-dir`, `-o`: Output directory for downloaded files
- `--credentials`, `-c`: Path to Google Drive API credentials file
- `--categories`: Path to categories CSV file (default: categories.csv)
- `--verbose`, `-v`: Enable verbose output

### Examples

#### List all categories and subcategories
```bash
python cli.py download-categories list
```

#### Download specific subcategory
```bash
python cli.py download-categories subcategories sfa4 --lifestyle-folder YOUR_FOLDER_ID
```

#### Process specific category
```bash
python cli.py download-categories categories soft-seating
```

#### Process all categories (copy from subcategories)
```bash
python cli.py download-categories categories-all --output-dir ./photos
```

#### Download all subcategories and categories
```bash
python cli.py download-categories all --lifestyle-folder YOUR_FOLDER_ID
```

### How It Works

1. **Subcategories**: Downloads photos from lifestyle folder where SKUs start with subcategory code (e.g., "sfa4-SKU001")
2. **Categories**: Copies photos from all subcategories belonging to that category
3. **Directory Structure**:
   ```
   photos/
   ├── subcategories/
   │   ├── sfa4/
   │   │   ├── sfa4-SKU001_photo1.jpg
   │   │   ├── sfa4-SKU001_photo2.jpg
   │   │   ├── sfa4-SKU002_photo1.jpg
   │   │   └── sfa4-SKU002_photo2.jpg
   │   └── sfa3/
   │       ├── sfa3-SKU001_photo1.jpg
   │       └── sfa3-SKU001_photo2.jpg
   └── categories/
       ├── soft-seating/
       │   ├── sfa4-SKU001_photo1.jpg
       │   ├── sfa4-SKU001_photo2.jpg
       │   ├── sfa4-SKU002_photo1.jpg
       │   ├── sfa4-SKU002_photo2.jpg
       │   ├── sfa3-SKU001_photo1.jpg
       │   └── sfa3-SKU001_photo2.jpg
       └── seating/
           ├── dchr-SKU001_photo1.jpg
           └── dchr-SKU001_photo2.jpg
   ```

### Configuration

Set the lifestyle photos folder ID in `config.yaml`:
```yaml
google_drive:
  folder_ids:
    lifestyle_photos: "YOUR_LIFESTYLE_PHOTOS_FOLDER_ID"
```

## report

Generate comprehensive photo analysis reports with various checks and validations.

### Usage
```bash
python cli.py report <photos_dir> [OPTIONS]
```

### Arguments
- `photos_dir`: Path to photos directory to analyze (required)

### Options
- `--csv`, `-c`: Path to CSV file with SKU data for missing SKU detection
- `--min-photos`, `-m`: Minimum number of photos required per SKU (default: 3)
- `--max-size`: Maximum file size in MB (default: 20.0)
- `--min-size`: Minimum file size in MB (default: 0.1)
- `--min-width`: Minimum image width in pixels (default: 200)
- `--min-height`: Minimum image height in pixels (default: 200)
- `--min-quality`: Minimum quality score 0-1 (default: 0.3)
- `--background-threshold`: Background detection threshold 0-1 (default: 0.8) - *Note: Uses improved algorithm that analyzes edge uniformity, contrast, and center-edge differences*

### Detail Shot Detection

The report can identify product detail shots (close-up photos focused on specific parts of the product).

#### Usage
```bash
python cli.py report --show-detail-shots
```

#### What it detects
- **High contrast images** with focused detail
- **High edge density** indicating lots of detail/edges
- **Center-focused composition** (center has higher contrast than edges)
- **Clean backgrounds** (uniform, not cluttered)
- **Product close-ups** that show specific features or textures
- `--export`, `-e`: Export comprehensive report to CSV file
- `--non-jpeg/--no-non-jpeg`: Show non-JPEG files (default: true)
- `--oversized/--no-oversized`: Show oversized files (default: true)
- `--undersized/--no-undersized`: Show undersized files (default: true)
- `--background/--no-background`: Show files with background (default: true)
- `--detail-shots/--no-detail-shots`: Show SKUs with detail shots (default: true)
- `--low-quality/--no-low-quality`: Show low quality files (default: true)
- `--few-photos/--no-few-photos`: Show SKUs with too few photos (default: true)
- `--missing/--no-missing`: Show missing SKUs (default: true)
- `--verbose`, `-v`: Enable verbose output

### Examples

#### Basic report
```bash
python cli.py report ./photos/products
```

#### Reorganize existing downloads
```bash
# Reorganize photos from supplier/sku structure to flat sku structure
./reorganize_photos.sh ./photos/products

# Dry run to see what would be moved
./reorganize_photos.sh ./photos/products --dry-run

# Python version with auto-merge
python reorganize_photos.py ./photos/products --auto-merge
```

#### Report with missing SKU detection
```bash
python cli.py report ./photos/products --csv ./data/products.csv
```

#### Custom thresholds
```bash
python cli.py report ./photos/products \
  --min-photos 5 \
  --max-size 10.0 \
  --min-quality 0.5
```

#### Export to CSV
```bash
python cli.py report ./photos/products \
  --csv ./data/products.csv \
  --export ./reports/photo_analysis.csv
```

#### Show only specific issues
```bash
python cli.py report ./photos/products \
  --no-background \
  --no-low-quality \
  --few-photos
```

### Report Types

The report command analyzes photos and generates reports for:

1. **Non-JPEG Files**: Files that are not in JPEG format
2. **Oversized Files**: Files exceeding the maximum size threshold
3. **Undersized Files**: Files below the minimum size threshold
4. **Background Files**: Files detected to have backgrounds
5. **Low Quality Files**: Files with quality scores below threshold
6. **Few Photos**: SKUs with fewer than the minimum required photos
7. **Missing SKUs**: SKUs present in CSV but missing from photos directory

### CSV Export

When using `--export`, the command generates a comprehensive CSV report with columns:
- `sku`: SKU identifier
- `total_photos`: Total number of photos
- `valid_photos`: Number of valid photos
- `invalid_photos`: Number of invalid photos
- `non_jpeg_count`: Number of non-JPEG files
- `oversized_count`: Number of oversized files
- `undersized_count`: Number of undersized files
- `background_count`: Number of files with background
- `low_quality_count`: Number of low quality files
- `issues`: Semicolon-separated list of issues
- `status`: Overall status (OK, ISSUES, MISSING)

### Configuration

The analyzer can be configured through command-line options or by modifying the `PhotoAnalyzer` class settings in `modules/photo_analyzer.py`.

## Reorganization Tools

### reorganize_photos.sh

Shell script to reorganize photos from supplier/sku structure to flat sku structure.

**Usage:**
```bash
./reorganize_photos.sh <photos_directory> [--dry-run]
```

**Features:**
- Moves SKU folders from `supplier/sku/` to `sku/`
- Handles conflicts by merging contents
- Removes empty supplier directories
- Dry-run mode to preview changes
- Colored output and progress tracking

### reorganize_photos.py

Python script with the same functionality as the shell script but with additional features.

**Usage:**
```bash
python reorganize_photos.py <photos_directory> [--dry-run] [--auto-merge]
```

**Additional Features:**
- `--auto-merge`: Automatically merge conflicting SKUs without prompting
- Rich console output with progress bars
- Better error handling and reporting

## `convert`

Convert all non-JPEG photos to JPEG format.

### Usage

```bash
python cli.py convert [OPTIONS]
```

### Arguments

- `--photos-dir, -p`: Directory containing photos to convert (default: from config)
- `--quality, -q`: JPEG quality (1-100, default: 85)
- `--verbose, -v`: Enable verbose output

### Examples

#### Convert photos with default settings
```bash
python cli.py convert
```

#### Convert photos in specific directory with high quality
```bash
python cli.py convert --photos-dir ./photos/products --quality 95
```

#### Convert with verbose output
```bash
python cli.py convert --verbose
```

### How it works

1. **Scans directory** for SKU folders
2. **Identifies non-JPEG files** (PNG, GIF, BMP, TIFF, WebP)
3. **Converts to JPEG** with specified quality
4. **Removes original files** after successful conversion
5. **Handles duplicates** by adding suffixes (_1, _2, etc.)

### Supported formats

**Input formats:**
- PNG (with transparency support)
- GIF
- BMP
- TIFF/TIF
- WebP

**Output format:**
- JPEG (with white background for transparent images)

## `rename`

Rename photos in various formats.

### Usage

```bash
python cli.py rename [OPTIONS]
```

### Arguments

- `--photos-dir, -p`: Directory containing photos to rename (default: from config)
- `--sequential, -s`: Rename photos to sequential format (1.jpg, 2.jpg, etc.)
- `--verbose, -v`: Enable verbose output

### Examples

#### Rename photos to sequential format
```bash
python cli.py rename --sequential
```

#### Rename with verbose output
```bash
python cli.py rename --sequential --verbose
```

#### Rename photos in specific directory
```bash
python cli.py rename --sequential --photos-dir ./photos/products
```

### How it works

1. **Scans directory** for SKU folders
2. **Finds JPEG files** in each SKU folder
3. **Sorts files** alphabetically for consistent ordering
4. **Renames sequentially** (1.jpg, 2.jpg, 3.jpg, etc.)
5. **Handles conflicts** by skipping existing target filenames

### Requirements

- **All photos must be JPEG format** before sequential renaming
- Use `convert` command first if you have non-JPEG files
- Photos are sorted alphabetically before renaming

### Error handling

- **Non-JPEG files found**: Suggests running `convert` command first
- **Target filename exists**: Skips renaming and reports conflict
- **Permission errors**: Reports specific file access issues

## Support

For issues or questions:

1. Check this documentation first
2. Use the `--help` flags for command-specific help
3. Check the project README for general information
4. Review the source code in the `modules/` directory
