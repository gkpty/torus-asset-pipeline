# Google Drive Photo Download Script

This script downloads photos from a Google Drive folder and organizes them according to the specified structure.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up Google Drive API credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Drive API
   - Create credentials (OAuth 2.0 Client ID)
   - Download the credentials file and save it as `credentials.json` in the project root

3. Update the FOLDER_ID in the script if needed:
   - The current folder ID is: `1MYjcWKn-agKMhVBNTqzrFOvzsU1-ygNp`
   - Replace with your actual Google Drive folder ID

## Usage

Run the script:
```bash
python download_photos.py
```

## Folder Structure

The script expects the following structure in Google Drive:
```
FOLDER_ID/
├── supplier_code_1/
│   ├── sku_1/
│   │   └── photos/
│   │       ├── random_string1.jpg
│   │       ├── random_string2.png
│   │       └── ...
│   └── sku_2/
│       └── photos/
│           └── ...
└── supplier_code_2/
    └── ...
```

The script will download and organize photos as:
```
./photos/products/
├── sku_1/
│   ├── 1.jpg
│   ├── 2.png
│   └── ...
└── sku_2/
    ├── 1.jpg
    └── ...
```

## Features

- Downloads all images from Google Drive folder structure
- Organizes photos by SKU
- Renames files sequentially (1.jpg, 2.jpg, etc.)
- Preserves original file extensions
- Creates necessary directories automatically
- Provides progress feedback during download
