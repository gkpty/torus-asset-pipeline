"""
Photo processing utilities for converting and renaming photos.
"""

import os
from typing import List, Dict, Any, Optional
from rich.console import Console

# Try to import Pillow for image conversion
try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class PhotoProcessor:
    """Handles photo conversion and renaming operations."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
    
    def convert_to_jpeg(self, input_path: str, output_path: str, quality: int = 85) -> bool:
        """Convert an image to JPEG format using Pillow."""
        if not PILLOW_AVAILABLE:
            self.console.print("[red]Error: Pillow library not available for image conversion.[/red]")
            self.console.print("[yellow]Install with: pip install Pillow[/yellow]")
            return False
            
        try:
            with Image.open(input_path) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create a white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as JPEG
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                return True
        except Exception as e:
            self.console.print(f"[red]Error converting {input_path}: {e}[/red]")
            return False
    
    def convert_photos_to_jpeg(self, output_dir: str, quality: int = 85, verbose: bool = False) -> Dict[str, Any]:
        """Convert all non-JPEG photos to JPEG format."""
        self.console.print(f"[cyan]Converting photos to JPEG format in: {output_dir}[/cyan]")
        
        if not os.path.exists(output_dir):
            self.console.print(f"[red]Error: {output_dir} directory not found[/red]")
            return {'error': 'Directory not found'}
        
        if not PILLOW_AVAILABLE:
            self.console.print("[red]Error: Pillow library not available for image conversion.[/red]")
            self.console.print("[yellow]Install with: pip install Pillow[/yellow]")
            return {'error': 'Pillow not available'}
        
        # Get all SKU directories
        sku_dirs = []
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isdir(item_path):
                sku_dirs.append(item)
        
        if not sku_dirs:
            self.console.print("[yellow]No SKU directories found in output directory[/yellow]")
            return {'total_converted': 0, 'total_skus_processed': 0, 'errors': []}
        
        # Track conversion results
        total_converted = 0
        total_skus_processed = 0
        conversion_errors = []
        non_jpeg_files = []
        
        for sku in sku_dirs:
            sku_path = os.path.join(output_dir, sku)
            sku_converted = 0
            
            if verbose:
                self.console.print(f"[dim]Processing {sku}...[/dim]")
            
            # Check all files in the SKU directory
            for file in os.listdir(sku_path):
                file_path = os.path.join(sku_path, file)
                if os.path.isfile(file_path):
                    file_lower = file.lower()
                    
                    # Check if it's a non-JPEG image file
                    if file_lower.endswith(('.png', '.gif', '.bmp', '.tiff', '.tif', '.webp')):
                        non_jpeg_files.append({
                            'sku': sku,
                            'filename': file,
                            'extension': os.path.splitext(file)[1].lower(),
                            'filepath': file_path
                        })
                        
                        # Create new filename with .jpg extension
                        base_name = os.path.splitext(file)[0]
                        new_filename = f"{base_name}.jpg"
                        new_filepath = os.path.join(sku_path, new_filename)
                        
                        # Handle duplicate filenames
                        counter = 1
                        while os.path.exists(new_filepath):
                            new_filename = f"{base_name}_{counter}.jpg"
                            new_filepath = os.path.join(sku_path, new_filename)
                            counter += 1
                        
                        # Convert the image
                        if self.convert_to_jpeg(file_path, new_filepath, quality):
                            if verbose:
                                self.console.print(f"  [green]Converted: {file} -> {new_filename}[/green]")
                            
                            # Remove original file
                            try:
                                os.remove(file_path)
                                if verbose:
                                    self.console.print(f"  [dim]Removed original: {file}[/dim]")
                            except Exception as e:
                                self.console.print(f"  [yellow]Warning: Could not remove original file {file}: {e}[/yellow]")
                            
                            sku_converted += 1
                            total_converted += 1
                        else:
                            conversion_errors.append({
                                'sku': sku,
                                'filename': file,
                                'error': 'Conversion failed'
                            })
            
            if sku_converted > 0:
                total_skus_processed += 1
                if verbose:
                    self.console.print(f"  [green]Converted {sku_converted} files in {sku}[/green]")
        
        # Print summary
        self.console.print(f"\n[cyan]Conversion Summary:[/cyan]")
        self.console.print(f"  [green]Total files converted: {total_converted}[/green]")
        self.console.print(f"  [blue]SKUs processed: {total_skus_processed}[/blue]")
        self.console.print(f"  [yellow]Non-JPEG files found: {len(non_jpeg_files)}[/yellow]")
        
        if conversion_errors:
            self.console.print(f"  [red]Conversion errors: {len(conversion_errors)}[/red]")
            if verbose:
                for error in conversion_errors:
                    self.console.print(f"    [red]{error['sku']}/{error['filename']}: {error['error']}[/red]")
        
        return {
            'total_converted': total_converted,
            'total_skus_processed': total_skus_processed,
            'non_jpeg_files': non_jpeg_files,
            'errors': conversion_errors
        }
    
    def rename_photos_sequential(self, output_dir: str, verbose: bool = False) -> Dict[str, Any]:
        """Rename all photos to be sequential (1.jpg, 2.jpg, 3.jpg) for each SKU."""
        self.console.print(f"[cyan]Renaming photos to sequential format in: {output_dir}[/cyan]")
        
        if not os.path.exists(output_dir):
            self.console.print(f"[red]Error: {output_dir} directory not found[/red]")
            return {'error': 'Directory not found'}
        
        # Get all SKU directories
        sku_dirs = []
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isdir(item_path):
                sku_dirs.append(item)
        
        if not sku_dirs:
            self.console.print("[yellow]No SKU directories found in output directory[/yellow]")
            return {'total_renamed': 0, 'total_skus_processed': 0, 'errors': []}
        
        total_renamed = 0
        total_skus_processed = 0
        renaming_errors = []
        non_jpeg_files = []
        
        for sku in sku_dirs:
            sku_path = os.path.join(output_dir, sku)
            photo_files = []
            
            if verbose:
                self.console.print(f"[dim]Processing {sku}...[/dim]")
            
            # Get all photo files in the SKU directory
            for file in os.listdir(sku_path):
                file_path = os.path.join(sku_path, file)
                if os.path.isfile(file_path):
                    if file.lower().endswith(('.jpg', '.jpeg')):
                        photo_files.append(file)
                    elif file.lower().endswith(('.png', '.gif', '.bmp', '.tiff', '.tif', '.webp')):
                        # Found non-JPEG file - collect for error reporting
                        non_jpeg_files.append({
                            'sku': sku,
                            'filename': file,
                            'extension': os.path.splitext(file)[1].lower(),
                            'filepath': file_path
                        })
            
            if not photo_files:
                if verbose:
                    self.console.print(f"  [yellow]No JPEG photos found in {sku}[/yellow]")
                continue
            
            # Sort files to ensure consistent ordering
            photo_files.sort()
            
            if verbose:
                self.console.print(f"  [blue]Found {len(photo_files)} JPEG photos in {sku}[/blue]")
            
            # Rename files sequentially
            for i, old_filename in enumerate(photo_files, 1):
                old_filepath = os.path.join(sku_path, old_filename)
                new_filename = f"{i}.jpg"
                new_filepath = os.path.join(sku_path, new_filename)
                
                try:
                    # Check if target filename already exists
                    if os.path.exists(new_filepath) and old_filepath != new_filepath:
                        if verbose:
                            self.console.print(f"  [yellow]Warning: {new_filename} already exists in {sku}, skipping {old_filename}[/yellow]")
                        renaming_errors.append({
                            'sku': sku,
                            'old_filename': old_filename,
                            'new_filename': new_filename,
                            'error': 'Target filename already exists'
                        })
                        continue
                    
                    # Rename the file
                    if old_filepath != new_filepath:
                        os.rename(old_filepath, new_filepath)
                        if verbose:
                            self.console.print(f"  [green]Renamed: {old_filename} -> {new_filename}[/green]")
                        total_renamed += 1
                    else:
                        if verbose:
                            self.console.print(f"  [dim]Already correct: {old_filename}[/dim]")
                        
                except Exception as e:
                    error_msg = f"Error renaming {old_filename}: {e}"
                    if verbose:
                        self.console.print(f"  [red]{error_msg}[/red]")
                    renaming_errors.append({
                        'sku': sku,
                        'old_filename': old_filename,
                        'new_filename': new_filename,
                        'error': str(e)
                    })
            
            total_skus_processed += 1
        
        # Check for non-JPEG files and warn if found
        if non_jpeg_files:
            self.console.print(f"\n[yellow]Warning: Found {len(non_jpeg_files)} non-JPEG files![/yellow]")
            self.console.print("[yellow]All photos must be in JPEG format before sequential renaming.[/yellow]")
            if verbose:
                self.console.print("\n[red]Non-JPEG files found:[/red]")
                for item in non_jpeg_files:
                    self.console.print(f"  [red]{item['sku']}/{item['filename']} ({item['extension']})[/red]")
            
            self.console.print(f"\n[yellow]💡 Please convert these files to JPEG format first using the 'convert' command.[/yellow]")
            
            return {
                'total_skus_processed': 0,
                'total_renamed': 0,
                'renaming_errors': [],
                'non_jpeg_files': non_jpeg_files,
                'error': 'Non-JPEG files found'
            }
        
        # Print summary
        self.console.print(f"\n[cyan]Renaming Summary:[/cyan]")
        self.console.print(f"  [green]Total files renamed: {total_renamed}[/green]")
        self.console.print(f"  [blue]SKUs processed: {total_skus_processed}[/blue]")
        
        if renaming_errors:
            self.console.print(f"  [red]Renaming errors: {len(renaming_errors)}[/red]")
            if verbose:
                for error in renaming_errors:
                    self.console.print(f"    [red]{error['sku']}/{error['old_filename']}: {error['error']}[/red]")
        
        return {
            'total_renamed': total_renamed,
            'total_skus_processed': total_skus_processed,
            'renaming_errors': renaming_errors,
            'non_jpeg_files': non_jpeg_files
        }
