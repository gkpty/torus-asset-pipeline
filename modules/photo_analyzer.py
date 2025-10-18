"""
Photo Analysis Module

This module provides comprehensive photo analysis capabilities including:
- Format detection (non-JPEG files)
- Size analysis (too large/small files)
- Quality assessment
- Background detection
- Photo count analysis
- Missing SKU detection
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID

# Try to import Pillow for image processing
try:
    from PIL import Image
    import numpy as np
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

# Try to import pandas for CSV operations
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Try to import boto3 for S3 operations
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


@dataclass
class PhotoAnalysisResult:
    """Result of photo analysis for a single file"""
    file_path: str
    sku: str
    supplier: str
    filename: str
    format: str
    size_mb: float
    dimensions: Tuple[int, int]
    has_background: bool
    quality_score: float
    is_valid: bool
    issues: List[str]


@dataclass
class SKUAnalysisResult:
    """Result of analysis for a single SKU"""
    sku: str
    supplier: str
    total_photos: int
    valid_photos: int
    invalid_photos: int
    non_jpeg_count: int
    oversized_count: int
    undersized_count: int
    background_count: int
    low_quality_count: int
    issues: List[str]
    photo_details: List[PhotoAnalysisResult]


class PhotoAnalyzer:
    """Comprehensive photo analysis tool"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        
        # Configuration
        self.max_file_size_mb = 20.0  # Maximum file size in MB
        self.min_file_size_mb = 0.1   # Minimum file size in MB
        self.min_dimensions = (200, 200)  # Minimum width, height
        self.max_dimensions = (8000, 8000)  # Maximum width, height
        self.min_quality_score = 0.3  # Minimum quality score (0-1)
        self.background_threshold = 0.8  # Threshold for background detection
        
        # Supported image formats
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        self.jpeg_extensions = {'.jpg', '.jpeg'}
    
    def analyze_photo(self, file_path: str, sku: str, supplier: str) -> PhotoAnalysisResult:
        """Analyze a single photo file"""
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        issues = []
        
        # Get file size
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
        except OSError:
            size_mb = 0
            issues.append("Cannot read file size")
        
        # Check if it's an image file
        if file_ext not in self.image_extensions:
            issues.append("Not an image file")
            return PhotoAnalysisResult(
                file_path=file_path,
                sku=sku,
                supplier=supplier,
                filename=filename,
                format=file_ext,
                size_mb=size_mb,
                dimensions=(0, 0),
                has_background=False,
                quality_score=0.0,
                is_valid=False,
                issues=issues
            )
        
        # Check format
        if file_ext not in self.jpeg_extensions:
            issues.append("Not JPEG format")
        
        # Check file size
        if size_mb > self.max_file_size_mb:
            issues.append(f"File too large ({size_mb:.2f}MB > {self.max_file_size_mb}MB)")
        elif size_mb < self.min_file_size_mb:
            issues.append(f"File too small ({size_mb:.2f}MB < {self.min_file_size_mb}MB)")
        
        # Analyze image if Pillow is available
        dimensions = (0, 0)
        has_background = False
        quality_score = 1.0
        
        if PILLOW_AVAILABLE:
            try:
                with Image.open(file_path) as img:
                    dimensions = img.size
                    
                    # Check dimensions
                    if dimensions[0] < self.min_dimensions[0] or dimensions[1] < self.min_dimensions[1]:
                        issues.append(f"Image too small ({dimensions[0]}x{dimensions[1]} < {self.min_dimensions[0]}x{self.min_dimensions[1]})")
                    elif dimensions[0] > self.max_dimensions[0] or dimensions[1] > self.max_dimensions[1]:
                        issues.append(f"Image too large ({dimensions[0]}x{dimensions[1]} > {self.max_dimensions[0]}x{self.max_dimensions[1]})")
                    
                    # Check for background (simplified detection)
                    has_background = self._detect_background(img)
                    if has_background:
                        issues.append("Has background")
                    
                    # Calculate quality score (simplified)
                    quality_score = self._calculate_quality_score(img, size_mb)
                    if quality_score < self.min_quality_score:
                        issues.append(f"Low quality (score: {quality_score:.2f})")
                        
            except Exception as e:
                issues.append(f"Error analyzing image: {str(e)}")
        else:
            issues.append("Pillow not available for image analysis")
        
        is_valid = len(issues) == 0
        
        return PhotoAnalysisResult(
            file_path=file_path,
            sku=sku,
            supplier=supplier,
            filename=filename,
            format=file_ext,
            size_mb=size_mb,
            dimensions=dimensions,
            has_background=has_background,
            quality_score=quality_score,
            is_valid=is_valid,
            issues=issues
        )
    
    def _detect_background(self, image: Image.Image) -> bool:
        """Detect if image has a background (simplified detection)"""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for faster processing
            image.thumbnail((100, 100), Image.Resampling.LANCZOS)
            img_array = np.array(image)
            
            # Check if image has significant white/light areas (background)
            # This is a simplified detection - in practice, you might want more sophisticated analysis
            white_pixels = np.sum(np.all(img_array > 200, axis=2))
            total_pixels = img_array.size // 3
            white_ratio = white_pixels / total_pixels
            
            return white_ratio > self.background_threshold
            
        except Exception:
            return False
    
    def _calculate_quality_score(self, image: Image.Image, size_mb: float) -> float:
        """Calculate a quality score for the image (0-1)"""
        try:
            # Simple quality score based on size and dimensions
            width, height = image.size
            total_pixels = width * height
            
            # Base score from pixel count
            pixel_score = min(1.0, total_pixels / (2000 * 2000))  # Normalize to 2MP
            
            # Size efficiency score
            if size_mb > 0:
                efficiency = total_pixels / (size_mb * 1024 * 1024)  # pixels per MB
                efficiency_score = min(1.0, efficiency / 1000000)  # Normalize
            else:
                efficiency_score = 0.0
            
            # Combine scores
            quality_score = (pixel_score * 0.7 + efficiency_score * 0.3)
            return min(1.0, max(0.0, quality_score))
            
        except Exception:
            return 0.0
    
    def analyze_sku_directory(self, sku_dir: str, sku: str, supplier: str) -> SKUAnalysisResult:
        """Analyze all photos in a SKU directory"""
        photo_details = []
        issues = []
        
        if not os.path.exists(sku_dir):
            issues.append("Directory does not exist")
            return SKUAnalysisResult(
                sku=sku,
                supplier=supplier,
                total_photos=0,
                valid_photos=0,
                invalid_photos=0,
                non_jpeg_count=0,
                oversized_count=0,
                undersized_count=0,
                background_count=0,
                low_quality_count=0,
                issues=issues,
                photo_details=photo_details
            )
        
        # Find all image files
        image_files = []
        for file in os.listdir(sku_dir):
            file_path = os.path.join(sku_dir, file)
            if os.path.isfile(file_path):
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in self.image_extensions:
                    image_files.append(file_path)
        
        # Analyze each photo
        for file_path in image_files:
            photo_result = self.analyze_photo(file_path, sku, supplier)
            photo_details.append(photo_result)
        
        # Calculate summary statistics
        total_photos = len(photo_details)
        valid_photos = sum(1 for p in photo_details if p.is_valid)
        invalid_photos = total_photos - valid_photos
        non_jpeg_count = sum(1 for p in photo_details if p.format not in self.jpeg_extensions)
        oversized_count = sum(1 for p in photo_details if p.size_mb > self.max_file_size_mb)
        undersized_count = sum(1 for p in photo_details if p.size_mb < self.min_file_size_mb)
        background_count = sum(1 for p in photo_details if p.has_background)
        low_quality_count = sum(1 for p in photo_details if p.quality_score < self.min_quality_score)
        
        # Add SKU-level issues
        if total_photos == 0:
            issues.append("No photos found")
        elif total_photos < 3:  # Assuming minimum 3 photos per SKU
            issues.append(f"Too few photos ({total_photos})")
        
        if non_jpeg_count > 0:
            issues.append(f"Has {non_jpeg_count} non-JPEG files")
        if oversized_count > 0:
            issues.append(f"Has {oversized_count} oversized files")
        if undersized_count > 0:
            issues.append(f"Has {undersized_count} undersized files")
        if background_count > 0:
            issues.append(f"Has {background_count} files with background")
        if low_quality_count > 0:
            issues.append(f"Has {low_quality_count} low quality files")
        
        return SKUAnalysisResult(
            sku=sku,
            supplier=supplier,
            total_photos=total_photos,
            valid_photos=valid_photos,
            invalid_photos=invalid_photos,
            non_jpeg_count=non_jpeg_count,
            oversized_count=oversized_count,
            undersized_count=undersized_count,
            background_count=background_count,
            low_quality_count=low_quality_count,
            issues=issues,
            photo_details=photo_details
        )
    
    def analyze_photos_directory(self, photos_dir: str, min_photos: int = 3) -> List[SKUAnalysisResult]:
        """Analyze all SKUs in a photos directory"""
        results = []
        
        if not os.path.exists(photos_dir):
            self.console.print(f"[red]Error: Photos directory not found: {photos_dir}[/red]")
            return results
        
        # Find all SKU directories
        sku_dirs = []
        for item in os.listdir(photos_dir):
            item_path = os.path.join(photos_dir, item)
            if os.path.isdir(item_path):
                # New flat structure: photos_dir/sku/ (no supplier subdirectories)
                sku = item
                supplier = "Unknown"  # Supplier info not available in flat structure
                
                sku_dirs.append((item_path, sku, supplier))
        
        self.console.print(f"[yellow]Found {len(sku_dirs)} SKU directories to analyze...[/yellow]")
        
        # Analyze each SKU
        with Progress() as progress:
            task = progress.add_task("Analyzing photos...", total=len(sku_dirs))
            
            for sku_dir, sku, supplier in sku_dirs:
                result = self.analyze_sku_directory(sku_dir, sku, supplier)
                results.append(result)
                progress.update(task, advance=1)
        
        return results
    
    def find_missing_skus(self, csv_file: str, photos_dir: str) -> List[Dict[str, Any]]:
        """Find SKUs that are in CSV but missing from photos directory"""
        missing_skus = []
        
        if not PANDAS_AVAILABLE:
            self.console.print("[yellow]Warning: pandas not available, using basic CSV parsing[/yellow]")
            return self._find_missing_skus_basic(csv_file, photos_dir)
        
        try:
            # Load CSV file
            df = pd.read_csv(csv_file)
            csv_skus = set(df['sku'].astype(str).str.strip())
            
            # Get existing SKU directories
            existing_skus = set()
            if os.path.exists(photos_dir):
                for item in os.listdir(photos_dir):
                    item_path = os.path.join(photos_dir, item)
                    if os.path.isdir(item_path):
                        existing_skus.add(item)
            
            # Find missing SKUs
            for sku in csv_skus:
                if sku not in existing_skus:
                    # Find supplier for this SKU
                    supplier = "Unknown"
                    if 'supplier' in df.columns:
                        sku_row = df[df['sku'].astype(str).str.strip() == sku]
                        if not sku_row.empty:
                            supplier = str(sku_row.iloc[0]['supplier']).strip()
                    
                    missing_skus.append({
                        'sku': sku,
                        'supplier': supplier,
                        'reason': 'Missing directory'
                    })
            
        except Exception as e:
            self.console.print(f"[red]Error loading CSV file: {e}[/red]")
        
        return missing_skus
    
    def _find_missing_skus_basic(self, csv_file: str, photos_dir: str) -> List[Dict[str, Any]]:
        """Basic CSV parsing without pandas"""
        missing_skus = []
        
        try:
            # Read CSV file
            csv_skus = set()
            suppliers = {}
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    sku = str(row.get('sku', '')).strip()
                    if sku:
                        csv_skus.add(sku)
                        suppliers[sku] = str(row.get('supplier', 'Unknown')).strip()
            
            # Get existing SKU directories
            existing_skus = set()
            if os.path.exists(photos_dir):
                for item in os.listdir(photos_dir):
                    item_path = os.path.join(photos_dir, item)
                    if os.path.isdir(item_path):
                        existing_skus.add(item)
            
            # Find missing SKUs
            for sku in csv_skus:
                if sku not in existing_skus:
                    missing_skus.append({
                        'sku': sku,
                        'supplier': suppliers.get(sku, 'Unknown'),
                        'reason': 'Missing directory'
                    })
            
        except Exception as e:
            self.console.print(f"[red]Error loading CSV file: {e}[/red]")
        
        return missing_skus
    
    def generate_report(self, results: List[SKUAnalysisResult], missing_skus: List[Dict[str, Any]], 
                       min_photos: int = 3, export_csv: Optional[str] = None) -> None:
        """Generate a comprehensive report"""
        
        # Summary statistics
        total_skus = len(results)
        skus_with_issues = sum(1 for r in results if r.issues)
        total_photos = sum(r.total_photos for r in results)
        valid_photos = sum(r.valid_photos for r in results)
        
        # Display summary
        self.console.print(Panel.fit(
            f"[bold]Photo Analysis Report[/bold]\n\n"
            f"Total SKUs: {total_skus}\n"
            f"SKUs with issues: {skus_with_issues}\n"
            f"Missing SKUs: {len(missing_skus)}\n"
            f"Total photos: {total_photos}\n"
            f"Valid photos: {valid_photos}\n"
            f"Invalid photos: {total_photos - valid_photos}",
            title="Summary"
        ))
        
        # Non-JPEG files
        non_jpeg_skus = [r for r in results if r.non_jpeg_count > 0]
        if non_jpeg_skus:
            self.console.print(f"\n[red]SKUs with non-JPEG files ({len(non_jpeg_skus)}):[/red]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("SKU", style="cyan")
            table.add_column("Non-JPEG Count", style="red")
            
            for result in non_jpeg_skus:
                table.add_row(result.sku, str(result.non_jpeg_count))
            
            self.console.print(table)
        
        # Oversized files
        oversized_skus = [r for r in results if r.oversized_count > 0]
        if oversized_skus:
            self.console.print(f"\n[yellow]SKUs with oversized files ({len(oversized_skus)}):[/yellow]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("SKU", style="cyan")
            table.add_column("Oversized Count", style="yellow")
            
            for result in oversized_skus:
                table.add_row(result.sku, str(result.oversized_count))
            
            self.console.print(table)
        
        # Undersized files
        undersized_skus = [r for r in results if r.undersized_count > 0]
        if undersized_skus:
            self.console.print(f"\n[blue]SKUs with undersized files ({len(undersized_skus)}):[/blue]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("SKU", style="cyan")
            table.add_column("Undersized Count", style="blue")
            
            for result in undersized_skus:
                table.add_row(result.sku, str(result.undersized_count))
            
            self.console.print(table)
        
        # Files with background
        background_skus = [r for r in results if r.background_count > 0]
        if background_skus:
            self.console.print(f"\n[magenta]SKUs with background files ({len(background_skus)}):[/magenta]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("SKU", style="cyan")
            table.add_column("Background Count", style="magenta")
            
            for result in background_skus:
                table.add_row(result.sku, str(result.background_count))
            
            self.console.print(table)
        
        # Low quality files
        low_quality_skus = [r for r in results if r.low_quality_count > 0]
        if low_quality_skus:
            self.console.print(f"\n[red]SKUs with low quality files ({len(low_quality_skus)}):[/red]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("SKU", style="cyan")
            table.add_column("Low Quality Count", style="red")
            
            for result in low_quality_skus:
                table.add_row(result.sku, str(result.low_quality_count))
            
            self.console.print(table)
        
        # SKUs with too few photos
        few_photos_skus = [r for r in results if r.total_photos < min_photos]
        if few_photos_skus:
            self.console.print(f"\n[yellow]SKUs with fewer than {min_photos} photos ({len(few_photos_skus)}):[/yellow]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("SKU", style="cyan")
            table.add_column("Photo Count", style="yellow")
            
            for result in few_photos_skus:
                table.add_row(result.sku, str(result.total_photos))
            
            self.console.print(table)
        
        # Missing SKUs
        if missing_skus:
            self.console.print(f"\n[red]Missing SKUs ({len(missing_skus)}):[/red]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("SKU", style="cyan")
            table.add_column("Reason", style="red")
            
            for sku_info in missing_skus:
                table.add_row(sku_info['sku'], sku_info['reason'])
            
            self.console.print(table)
        
        # Export CSV if requested
        if export_csv:
            self._export_csv_report(results, missing_skus, export_csv)
    
    def _export_csv_report(self, results: List[SKUAnalysisResult], missing_skus: List[Dict[str, Any]], 
                          csv_path: str) -> None:
        """Export comprehensive report to CSV"""
        try:
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'sku', 'total_photos', 'valid_photos', 'invalid_photos',
                    'non_jpeg_count', 'oversized_count', 'undersized_count', 
                    'background_count', 'low_quality_count', 'issues', 'status'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write SKU results
                for result in results:
                    writer.writerow({
                        'sku': result.sku,
                        'total_photos': result.total_photos,
                        'valid_photos': result.valid_photos,
                        'invalid_photos': result.invalid_photos,
                        'non_jpeg_count': result.non_jpeg_count,
                        'oversized_count': result.oversized_count,
                        'undersized_count': result.undersized_count,
                        'background_count': result.background_count,
                        'low_quality_count': result.low_quality_count,
                        'issues': '; '.join(result.issues) if result.issues else '',
                        'status': 'OK' if not result.issues else 'ISSUES'
                    })
                
                # Write missing SKUs
                for sku_info in missing_skus:
                    writer.writerow({
                        'sku': sku_info['sku'],
                        'total_photos': 0,
                        'valid_photos': 0,
                        'invalid_photos': 0,
                        'non_jpeg_count': 0,
                        'oversized_count': 0,
                        'undersized_count': 0,
                        'background_count': 0,
                        'low_quality_count': 0,
                        'issues': sku_info['reason'],
                        'status': 'MISSING'
                    })
            
            self.console.print(f"[green]Report exported to: {csv_path}[/green]")
            
        except Exception as e:
            self.console.print(f"[red]Error exporting CSV: {e}[/red]")
