"""
Simple download module without complex progress bars - for debugging
"""

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload
import re
from typing import Optional, List, Dict, Any
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue

# Try to import Pillow for image conversion
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class GoogleDriveDownloaderSimple:
    """Simple Google Drive photo downloader for debugging"""
    
    def __init__(self, credentials_file: str = "credentials.json"):
        self.credentials_file = credentials_file
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.service = None
        self.console = Console()
        self._creds = None  # Store credentials for thread access
    
    def authenticate(self):
        """Authenticate with Google Drive API"""
        try:
            self.console.print("[yellow]🔐 Starting Google Drive authentication...[/yellow]")
            self.console.print("[dim]This will open a browser window for authentication.[/dim]")
            
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
            creds = flow.run_local_server(port=8080, open_browser=True)
            
            self.console.print("[green]✅ Authentication successful![/green]")
            self.service = build('drive', 'v3', credentials=creds)
            self._creds = creds  # Store credentials for thread access
            return self.service
            
        except FileNotFoundError:
            self.console.print(f"[red]❌ Credentials file not found: {self.credentials_file}[/red]")
            raise
        except Exception as e:
            self.console.print(f"[red]❌ Authentication failed: {e}[/red]")
            raise
    
    def get_folder_contents(self, folder_id: str) -> List[Dict[str, Any]]:
        """Get all files and folders within a Google Drive folder"""
        try:
            results = self.service.files().list(
                q=f"'{folder_id}' in parents",
                fields="nextPageToken, files(id, name, mimeType)",
                orderBy="name"
            ).execute()
            return results.get('files', [])
        except HttpError as error:
            self.console.print(f'[red]Error accessing folder {folder_id}: {error}[/red]')
            return []
    
    def is_image_file(self, filename: str) -> bool:
        """Check if file is an image based on extension"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    def download_file(self, file_id: str, file_path: str) -> bool:
        """Download a file from Google Drive without conversion"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # Show simple progress
                self.console.print(f"[dim]Download progress: {int(status.progress() * 100)}%[/dim]", end="\r")
            
            # Write file directly
            with open(file_path, 'wb') as f:
                f.write(fh.getvalue())
            return True
                    
        except HttpError as error:
            self.console.print(f'[red]Error downloading file {file_id}: {error}[/red]')
            return False
    
    def download_file_threaded(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Thread-safe download function for parallel processing"""
        file_id = file_info['file_id']
        file_path = file_info['file_path']
        original_name = file_info['original_name']
        sku_name = file_info['sku_name']
        supplier_name = file_info['supplier_name']
        index = file_info['index']
        total = file_info['total']
        
        try:
            # Create a new service instance for this thread to avoid thread safety issues
            # This is the proper way to handle Google Drive API with threading
            flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
            
            # Try to use existing credentials if available
            if hasattr(self, '_creds') and self._creds:
                service = build('drive', 'v3', credentials=self._creds)
            else:
                # Fallback: this will require re-authentication
                return {
                    'success': False,
                    'file_name': original_name,
                    'sku_name': sku_name,
                    'supplier_name': supplier_name,
                    'index': index,
                    'total': total,
                    'error': 'No credentials available for thread'
                }
            
            # Make API call with thread's own service instance
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(fh.getvalue())
            
            return {
                'success': True,
                'file_name': original_name,
                'sku_name': sku_name,
                'supplier_name': supplier_name,
                'index': index,
                'total': total
            }
                    
        except Exception as error:
            return {
                'success': False,
                'file_name': original_name,
                'sku_name': sku_name,
                'supplier_name': supplier_name,
                'index': index,
                'total': total,
                'error': str(error)
            }
    
    def download_photos_parallel(self, folder_id: str, output_dir: str, model: str = "products", verbose: bool = False, confirm_all: bool = False, max_workers: int = 5) -> bool:
        """Parallel download function - processes suppliers sequentially, SKUs in parallel"""
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Authenticate
            if not self.service:
                self.authenticate()
            
            # Get all suppliers
            self.console.print(f"[yellow]📂 Accessing Google Drive folder: {folder_id}[/yellow]")
            suppliers = self.get_folder_contents(folder_id)
            suppliers = [s for s in suppliers if s['mimeType'] == 'application/vnd.google-apps.folder']
            
            if not suppliers:
                self.console.print("[red]❌ No suppliers found in the specified folder![/red]")
                return False
            
            # Show suppliers
            self.console.print(f"[green]Found {len(suppliers)} suppliers:[/green]")
            for i, supplier in enumerate(suppliers, 1):
                self.console.print(f"  {i}. {supplier['name']}")
            
            if not confirm_all:
                response = self.console.input("[bold]Want to continue downloading all of the photos?[/bold] [dim](y/N):[/dim] ").lower().strip()
                if response not in ['y', 'yes']:
                    self.console.print("[yellow]Download cancelled by user.[/yellow]")
                    return False
            
            # Process each supplier sequentially
            total_downloaded = 0
            total_failed = 0
            
            for supplier_idx, supplier in enumerate(suppliers, 1):
                supplier_name = supplier['name']
                self.console.print(f"\n[cyan]📦 Processing supplier {supplier_idx}/{len(suppliers)}: {supplier_name}[/cyan]")
                
                # Collect all files for this supplier
                supplier_files = []
                sku_info = []
                
                # Get SKUs for this supplier
                skus = self.get_folder_contents(supplier['id'])
                skus = [s for s in skus if s['mimeType'] == 'application/vnd.google-apps.folder']
                
                for sku in skus:
                    sku_name = sku['name']
                    
                    # Get photos folder
                    photos_folders = self.get_folder_contents(sku['id'])
                    photos_folder = None
                    for folder in photos_folders:
                        if folder['mimeType'] == 'application/vnd.google-apps.folder' and folder['name'].lower() == 'photos':
                            photos_folder = folder
                            break
                    
                    if not photos_folder:
                        if verbose:
                            self.console.print(f"    [dim]No photos folder found for SKU: {sku_name}[/dim]")
                        continue
                    
                    # Get image files
                    image_files = self.get_folder_contents(photos_folder['id'])
                    image_files = [f for f in image_files if self.is_image_file(f['name'])]
                    
                    if not image_files:
                        if verbose:
                            self.console.print(f"    [dim]No image files found for SKU: {sku_name}[/dim]")
                        continue
                    
                    # Create SKU directory
                    sku_dir = os.path.join(output_dir, sku_name)
                    os.makedirs(sku_dir, exist_ok=True)
                    
                    # Log SKU collection
                    self.console.print(f"    [green]✓ Collected SKU: {sku_name} ({len(image_files)} images)[/green]")
                    sku_info.append({'name': sku_name, 'count': len(image_files)})
                    
                    # Add files to download list for this supplier
                    for i, image_file in enumerate(image_files, 1):
                        supplier_files.append({
                            'file_id': image_file['id'],
                            'file_path': os.path.join(sku_dir, image_file['name']),
                            'original_name': image_file['name'],
                            'sku_name': sku_name,
                            'supplier_name': supplier_name,
                            'index': i,
                            'total': len(image_files)
                        })
                
                if not supplier_files:
                    self.console.print(f"    [yellow]⚠️ No files found for supplier: {supplier_name}[/yellow]")
                    continue
                
                # Download all files for this supplier in parallel
                self.console.print(f"    [yellow]🚀 Downloading {len(supplier_files)} images from {len(sku_info)} SKUs with {max_workers} workers...[/yellow]")
                
                supplier_downloaded = 0
                supplier_failed = 0
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    # Submit all download tasks for this supplier
                    future_to_file = {
                        executor.submit(self.download_file_threaded, file_info): file_info 
                        for file_info in supplier_files
                    }
                    
                    # Process completed downloads
                    for future in as_completed(future_to_file):
                        result = future.result()
                        
                        if result['success']:
                            supplier_downloaded += 1
                            total_downloaded += 1
                            if verbose:
                                self.console.print(f"      [green]✓ {result['file_name']} ({result['index']}/{result['total']}) - {result['sku_name']}[/green]")
                        else:
                            supplier_failed += 1
                            total_failed += 1
                            self.console.print(f"      [red]✗ {result['file_name']} - {result.get('error', 'Unknown error')}[/red]")
                        
                        # Show progress for this supplier
                        completed = supplier_downloaded + supplier_failed
                        self.console.print(f"      [dim]Progress: {completed}/{len(supplier_files)} files processed[/dim]", end="\r")
                
                # Summary for this supplier
                self.console.print(f"\n    [green]✅ Supplier {supplier_name} completed: {supplier_downloaded} downloaded, {supplier_failed} failed[/green]")
            
            # Final success message
            self.console.print(f"\n[green]🎉 All suppliers processed![/green]")
            self.console.print(f"[green]✅ Total downloaded: {total_downloaded} images[/green]")
            if total_failed > 0:
                self.console.print(f"[yellow]⚠️ Total failed: {total_failed} files[/yellow]")
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error during photo download: {e}[/red]")
            return False

    def download_photos(self, folder_id: str, output_dir: str, model: str = "products", verbose: bool = False, confirm_all: bool = False) -> bool:
        """Simple download function without complex progress bars"""
        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Authenticate
            if not self.service:
                self.authenticate()
            
            # Get all suppliers
            self.console.print(f"[yellow]📂 Accessing Google Drive folder: {folder_id}[/yellow]")
            suppliers = self.get_folder_contents(folder_id)
            suppliers = [s for s in suppliers if s['mimeType'] == 'application/vnd.google-apps.folder']
            
            if not suppliers:
                self.console.print("[red]❌ No suppliers found in the specified folder![/red]")
                return False
            
            # Show suppliers
            self.console.print(f"[green]Found {len(suppliers)} suppliers:[/green]")
            for i, supplier in enumerate(suppliers, 1):
                self.console.print(f"  {i}. {supplier['name']}")
            
            if not confirm_all:
                response = self.console.input("[bold]Want to continue downloading all of the photos?[/bold] [dim](y/N):[/dim] ").lower().strip()
                if response not in ['y', 'yes']:
                    self.console.print("[yellow]Download cancelled by user.[/yellow]")
                    return False
            
            # Download from all suppliers
            total_downloaded = 0
            for supplier in suppliers:
                supplier_name = supplier['name']
                self.console.print(f"\n[cyan]Processing supplier: {supplier_name}[/cyan]")
                
                # Get SKUs for this supplier
                skus = self.get_folder_contents(supplier['id'])
                skus = [s for s in skus if s['mimeType'] == 'application/vnd.google-apps.folder']
                
                for sku in skus:
                    sku_name = sku['name']
                    self.console.print(f"  [yellow]Processing SKU: {sku_name}[/yellow]")
                    
                    # Get photos folder
                    photos_folders = self.get_folder_contents(sku['id'])
                    photos_folder = None
                    for folder in photos_folders:
                        if folder['mimeType'] == 'application/vnd.google-apps.folder' and folder['name'].lower() == 'photos':
                            photos_folder = folder
                            break
                    
                    if not photos_folder:
                        self.console.print(f"    [dim]No photos folder found[/dim]")
                        continue
                    
                    # Get image files
                    image_files = self.get_folder_contents(photos_folder['id'])
                    image_files = [f for f in image_files if self.is_image_file(f['name'])]
                    
                    if not image_files:
                        self.console.print(f"    [dim]No image files found[/dim]")
                        continue
                    
                    # Create SKU directory
                    sku_dir = os.path.join(output_dir, sku_name)
                    os.makedirs(sku_dir, exist_ok=True)
                    
                    self.console.print(f"    [green]Found {len(image_files)} images[/green]")
                    
                    # Download images
                    for i, image_file in enumerate(image_files, 1):
                        original_name = image_file['name']
                        output_path = os.path.join(sku_dir, original_name)
                        
                        self.console.print(f"    [{i}/{len(image_files)}] Downloading: {original_name}")
                        
                        if self.download_file(image_file['id'], output_path):
                            self.console.print(f"    [green]✓ Downloaded: {original_name}[/green]")
                            total_downloaded += 1
                        else:
                            self.console.print(f"    [red]✗ Failed: {original_name}[/red]")
            
            # Success message
            self.console.print(f"\n[green]✅ Successfully downloaded {total_downloaded} images![/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error during photo download: {e}[/red]")
            return False


def download_photos_from_drive(
    folder_id: str, 
    output_dir: str, 
    model: str = "products", 
    credentials_file: str = "credentials.json",
    verbose: bool = False,
    confirm_all: bool = False
) -> bool:
    """Simple download function for debugging"""
    downloader = GoogleDriveDownloaderSimple(credentials_file)
    return downloader.download_photos(folder_id, output_dir, model, verbose, confirm_all)

def download_photos_from_drive_parallel(
    folder_id: str, 
    output_dir: str, 
    model: str = "products", 
    credentials_file: str = "credentials.json",
    verbose: bool = False,
    confirm_all: bool = False,
    max_workers: int = 5
) -> bool:
    """Parallel download function for faster downloads"""
    downloader = GoogleDriveDownloaderSimple(credentials_file)
    return downloader.download_photos_parallel(folder_id, output_dir, model, verbose, confirm_all, max_workers)
