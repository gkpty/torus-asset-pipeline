"""
Category Download Module

This module handles downloading photos for categories and subcategories from Google Drive.
It works with lifestyle photos folder structure where SKUs begin with subcategory codes.
"""

import os
import csv
import shutil
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, TaskID
from rich.table import Table
from rich.panel import Panel

from .download import GoogleDriveDownloaderSimple


@dataclass
class CategoryInfo:
    """Information about a category or subcategory"""
    name: str
    type: str  # 'category' or 'subcategory'
    parent: Optional[str] = None  # For subcategories, the parent category


class CategoryDownloader:
    """Downloads photos for categories and subcategories"""
    
    def __init__(self, credentials_file: str = "credentials.json", console: Optional[Console] = None):
        self.console = console or Console()
        self.downloader = GoogleDriveDownloaderSimple(credentials_file)
        self.categories_data = {}
        self.lifestyle_folder_id = None
        
    def load_categories(self, csv_file: str = "categories.csv") -> Dict[str, CategoryInfo]:
        """Load category and subcategory data from CSV file"""
        categories = {}
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    subcategory = row['subcategory'].strip()
                    category = row['category'].strip()
                    
                    # Store subcategory info
                    categories[subcategory] = CategoryInfo(
                        name=subcategory,
                        type='subcategory',
                        parent=category
                    )
                    
                    # Always create category info for any parent category mentioned
                    if category not in categories:
                        categories[category] = CategoryInfo(
                            name=category,
                            type='category'
                        )
            
            self.categories_data = categories
            self.console.print(f"[green]Loaded {len(categories)} categories and subcategories[/green]")
            return categories
            
        except FileNotFoundError:
            self.console.print(f"[red]Error: Categories CSV file not found: {csv_file}[/red]")
            return {}
        except Exception as e:
            self.console.print(f"[red]Error loading categories: {e}[/red]")
            return {}
    
    def find_lifestyle_folder(self, root_folder_id: str) -> Optional[str]:
        """Find the lifestyle photos folder in Google Drive"""
        try:
            if not self.downloader.service:
                self.downloader.authenticate()
            
            # Look for lifestyle folder
            folders = self.downloader.get_folder_contents(root_folder_id)
            lifestyle_folder = None
            
            for folder in folders:
                if folder['mimeType'] == 'application/vnd.google-apps.folder':
                    folder_name = folder['name'].lower()
                    if 'lifestyle' in folder_name or 'photos' in folder_name:
                        lifestyle_folder = folder
                        break
            
            if lifestyle_folder:
                self.lifestyle_folder_id = lifestyle_folder['id']
                self.console.print(f"[green]Found lifestyle folder: {lifestyle_folder['name']}[/green]")
                return lifestyle_folder['id']
            else:
                self.console.print("[red]Lifestyle photos folder not found![/red]")
                return None
                
        except Exception as e:
            self.console.print(f"[red]Error finding lifestyle folder: {e}[/red]")
            return None
    
    def get_skus_for_subcategory(self, subcategory: str) -> List[Dict[str, Any]]:
        """Get all SKUs that belong to a subcategory"""
        if not self.lifestyle_folder_id:
            self.console.print("[red]Lifestyle folder not found. Call find_lifestyle_folder first.[/red]")
            return []
        
        try:
            skus = []
            folders = self.downloader.get_folder_contents(self.lifestyle_folder_id)
            
            for folder in folders:
                if folder['mimeType'] == 'application/vnd.google-apps.folder':
                    folder_name = folder['name']
                    
                    # Check if SKU starts with subcategory code
                    if folder_name.startswith(f"{subcategory}-"):
                        skus.append({
                            'name': folder_name,
                            'id': folder['id'],
                            'subcategory': subcategory
                        })
            
            self.console.print(f"[blue]Found {len(skus)} SKUs for subcategory: {subcategory}[/blue]")
            return skus
            
        except Exception as e:
            self.console.print(f"[red]Error getting SKUs for subcategory {subcategory}: {e}[/red]")
            return []
    
    def download_photos_parallel(self, image_files: List[Dict[str, Any]], 
                                subcategory_dir: str, sku_name: str, 
                                max_workers: int = 5) -> tuple[int, int]:
        """Download photos in parallel for a single SKU"""
        def download_single_photo(image_file: Dict[str, Any]) -> Dict[str, Any]:
            """Download a single photo file using the same approach as working parallel download"""
            filename = f"{sku_name}_{image_file['name']}"
            file_path = os.path.join(subcategory_dir, filename)
            
            try:
                # Use the same approach as the working download_file_threaded method
                from google_auth_oauthlib.flow import InstalledAppFlow
                from googleapiclient.discovery import build
                from googleapiclient.http import MediaIoBaseDownload
                import io
                
                # Create a new service instance for this thread using stored credentials
                if hasattr(self.downloader, '_creds') and self.downloader._creds:
                    service = build('drive', 'v3', credentials=self.downloader._creds)
                else:
                    # Fallback: create new credentials
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.downloader.credentials_file, 
                        self.downloader.scopes
                    )
                    creds = flow.run_local_server(port=0)
                    service = build('drive', 'v3', credentials=creds)
                
                # Download the file
                request = service.files().get_media(fileId=image_file['id'])
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
                    'filename': image_file['name'],
                    'sku_name': sku_name,
                    'error': None
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'filename': image_file['name'],
                    'sku_name': sku_name,
                    'error': str(e)
                }
        
        downloaded = 0
        failed = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_file = {
                executor.submit(download_single_photo, image_file): image_file 
                for image_file in image_files
            }
            
            # Process completed downloads
            for future in as_completed(future_to_file):
                result = future.result()
                if result['success']:
                    downloaded += 1
                else:
                    failed += 1
                    if result['error']:
                        self.console.print(f"    [red]Error downloading {result['filename']}: {result['error']}[/red]")
        
        return downloaded, failed

    def download_subcategory_photos(self, subcategory: str, output_dir: str, 
                                  lifestyle_folder_id: str, max_workers: int = 5) -> bool:
        """Download photos for a specific subcategory"""
        try:
            # Authenticate if not already done
            if not self.downloader.service:
                self.downloader.authenticate()
            
            # Use the provided lifestyle folder ID directly
            if not self.lifestyle_folder_id:
                self.lifestyle_folder_id = lifestyle_folder_id
                self.console.print(f"[green]Using lifestyle folder ID: {lifestyle_folder_id}[/green]")
            
            # Get SKUs for this subcategory
            skus = self.get_skus_for_subcategory(subcategory)
            if not skus:
                self.console.print(f"[yellow]No SKUs found for subcategory: {subcategory}[/yellow]")
                return True
            
            # Create output directory for subcategory
            subcategory_dir = os.path.join(output_dir, "subcategories", subcategory)
            os.makedirs(subcategory_dir, exist_ok=True)
            
            total_downloaded = 0
            total_failed = 0
            
            self.console.print(f"[cyan]Downloading photos for subcategory: {subcategory}[/cyan]")
            
            with Progress() as progress:
                task = progress.add_task(f"Downloading {subcategory}...", total=len(skus))
                
                for sku in skus:
                    sku_name = sku['name']
                    sku_id = sku['id']
                    
                    # Get photos from this SKU folder
                    photos = self.downloader.get_folder_contents(sku_id)
                    image_files = [f for f in photos if self.downloader.is_image_file(f['name'])]
                    
                    if not image_files:
                        self.console.print(f"  [dim]No photos found for SKU: {sku_name}[/dim]")
                        progress.update(task, advance=1)
                        continue
                    
                    # Download photos in parallel for this SKU
                    sku_downloaded, sku_failed = self.download_photos_parallel(
                        image_files, subcategory_dir, sku_name, max_workers
                    )
                    
                    total_downloaded += sku_downloaded
                    total_failed += sku_failed
                    
                    self.console.print(f"  [green]✓ {sku_name}: {sku_downloaded} photos downloaded[/green]")
                    if sku_failed > 0:
                        self.console.print(f"    [yellow]⚠ {sku_failed} photos failed[/yellow]")
                    
                    progress.update(task, advance=1)
            
            self.console.print(f"[green]Subcategory {subcategory} completed: {total_downloaded} downloaded, {total_failed} failed[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error downloading subcategory {subcategory}: {e}[/red]")
            return False
    
    def download_category_photos(self, category: str, output_dir: str, subcategories_dir: Optional[str] = None) -> bool:
        """Download photos for a category by copying from all its subcategories"""
        try:
            # Find all subcategories for this category
            subcategories = [name for name, info in self.categories_data.items() 
                           if info.type == 'subcategory' and info.parent == category]
            
            if not subcategories:
                self.console.print(f"[yellow]No subcategories found for category: {category}[/yellow]")
                return True
            
            # Create output directory for category
            category_dir = os.path.join(output_dir, "categories", category)
            os.makedirs(category_dir, exist_ok=True)
            
            # Use provided subcategories_dir or default to output_dir/subcategories
            if subcategories_dir is None:
                subcategories_dir = os.path.join(output_dir, "subcategories")
            
            self.console.print(f"[cyan]Copying photos for category: {category}[/cyan]")
            self.console.print(f"[blue]Found subcategories: {', '.join(subcategories)}[/blue]")
            
            total_copied = 0
            total_failed = 0
            
            with Progress() as progress:
                task = progress.add_task(f"Copying {category}...", total=len(subcategories))
                
                for subcategory in subcategories:
                    subcategory_dir = os.path.join(subcategories_dir, subcategory)
                    
                    if not os.path.exists(subcategory_dir):
                        self.console.print(f"  [yellow]Subcategory directory not found: {subcategory}[/yellow]")
                        progress.update(task, advance=1)
                        continue
                    
                    # Copy all files from subcategory to category (flat structure)
                    files = [f for f in os.listdir(subcategory_dir) 
                           if os.path.isfile(os.path.join(subcategory_dir, f))]
                    
                    subcategory_copied = 0
                    subcategory_failed = 0
                    
                    for file in files:
                        source_file = os.path.join(subcategory_dir, file)
                        target_file = os.path.join(category_dir, file)
                        
                        try:
                            if os.path.exists(target_file):
                                # Handle file conflicts by adding a suffix
                                name, ext = os.path.splitext(file)
                                counter = 1
                                while os.path.exists(target_file):
                                    target_file = os.path.join(category_dir, f"{name}_{counter}{ext}")
                                    counter += 1
                            
                            shutil.copy2(source_file, target_file)
                            subcategory_copied += 1
                            
                        except Exception as e:
                            self.console.print(f"    [red]Error copying {file}: {e}[/red]")
                            subcategory_failed += 1
                    
                    self.console.print(f"  [green]✓ {subcategory}: {subcategory_copied} photos copied[/green]")
                    if subcategory_failed > 0:
                        self.console.print(f"    [yellow]⚠ {subcategory_failed} files failed[/yellow]")
                    
                    total_copied += subcategory_copied
                    total_failed += subcategory_failed
                    progress.update(task, advance=1)
            
            self.console.print(f"[green]Category {category} completed: {total_copied} photos copied, {total_failed} failed[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error downloading category {category}: {e}[/red]")
            return False
    
    def _merge_directories(self, source_dir: str, target_dir: str) -> None:
        """Merge contents from source directory to target directory"""
        for item in os.listdir(source_dir):
            source_item = os.path.join(source_dir, item)
            target_item = os.path.join(target_dir, item)
            
            if os.path.isdir(source_item):
                if os.path.exists(target_item):
                    self._merge_directories(source_item, target_item)
                else:
                    shutil.copytree(source_item, target_item)
            else:
                if os.path.exists(target_item):
                    # Handle file conflicts by adding a suffix
                    name, ext = os.path.splitext(item)
                    counter = 1
                    while os.path.exists(target_item):
                        target_item = os.path.join(target_dir, f"{name}_{counter}{ext}")
                        counter += 1
                
                shutil.copy2(source_item, target_item)
    
    def list_categories(self) -> None:
        """Display all available categories and subcategories"""
        if not self.categories_data:
            self.console.print("[yellow]No categories loaded. Call load_categories first.[/yellow]")
            return
        
        # Group subcategories by their parent category
        categories = {}
        
        for name, info in self.categories_data.items():
            if info.type == 'subcategory' and info.parent:
                if info.parent not in categories:
                    categories[info.parent] = []
                categories[info.parent].append(name)
        
        # Display in a table
        table = Table(title="📁 Available Categories and Subcategories", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan", width=20)
        table.add_column("Subcategories", style="green")
        
        for category, subcategories in sorted(categories.items()):
            subcategory_list = ", ".join(sorted(subcategories)) if subcategories else "None"
            table.add_row(category, subcategory_list)
        
        self.console.print(table)
    
    def download_all_subcategories(self, output_dir: str, lifestyle_folder_id: str, max_workers: int = 5) -> bool:
        """Download photos for all subcategories"""
        if not self.categories_data:
            self.console.print("[red]No categories loaded. Call load_categories first.[/red]")
            return False
        
        subcategories = [name for name, info in self.categories_data.items() 
                        if info.type == 'subcategory']
        
        if not subcategories:
            self.console.print("[yellow]No subcategories found.[/yellow]")
            return True
        
        self.console.print(f"[cyan]Downloading photos for {len(subcategories)} subcategories...[/cyan]")
        
        success_count = 0
        for subcategory in subcategories:
            if self.download_subcategory_photos(subcategory, output_dir, lifestyle_folder_id, max_workers):
                success_count += 1
        
        self.console.print(f"[green]Completed: {success_count}/{len(subcategories)} subcategories downloaded[/green]")
        return success_count == len(subcategories)
    
    def download_all_categories(self, output_dir: str, subcategories_dir: Optional[str] = None) -> bool:
        """Download photos for all categories"""
        if not self.categories_data:
            self.console.print("[red]No categories loaded. Call load_categories first.[/red]")
            return False
        
        categories = [name for name, info in self.categories_data.items() 
                     if info.type == 'category']
        
        if not categories:
            self.console.print("[yellow]No categories found.[/yellow]")
            return True
        
        self.console.print(f"[cyan]Copying photos for {len(categories)} categories...[/cyan]")
        
        success_count = 0
        for category in categories:
            if self.download_category_photos(category, output_dir, subcategories_dir):
                success_count += 1
        
        self.console.print(f"[green]Completed: {success_count}/{len(categories)} categories processed[/green]")
        return success_count == len(categories)
