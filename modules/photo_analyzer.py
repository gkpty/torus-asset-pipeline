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
    is_detail_shot: bool
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
    detail_shot_count: int
    low_quality_count: int
    issues: List[str]
    photo_details: List[PhotoAnalysisResult]


class PhotoAnalyzer:
    """Comprehensive photo analysis tool"""
    
    def __init__(self, console: Optional[Console] = None, debug: bool = False):
        self.console = console or Console()
        self.debug = debug
        
        # Configuration
        self.max_file_size_mb = 20.0  # Maximum file size in MB
        self.min_file_size_mb = 0.1   # Minimum file size in MB
        self.min_dimensions = (200, 200)  # Minimum width, height
        self.max_dimensions = (8000, 8000)  # Maximum width, height
        self.min_quality_score = 0.3  # Minimum quality score (0-1)
        self.background_threshold = 0.8  # Threshold for background detection (legacy, not used in new algorithm)
        
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
        is_detail_shot = False
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
                    
                    # Check for background (improved detection)
                    has_background = self._detect_background(img)
                    if has_background:
                        issues.append("Has background")
                    
                    # Check for detail shot
                    is_detail_shot = self._detect_detail_shot(img)
                    
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
            is_detail_shot=is_detail_shot,
            quality_score=quality_score,
            is_valid=is_valid,
            issues=issues
        )
    
    def _detect_background(self, image: Image.Image) -> bool:
        """Detect if image has a background using improved algorithm"""
        try:
            if not PILLOW_AVAILABLE:
                return False
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for faster processing
            image.thumbnail((200, 200), Image.Resampling.LANCZOS)
            img_array = np.array(image)
            
            # Method 1: Check for uniform white/light background
            # Look for areas that are consistently white/light around the edges
            height, width = img_array.shape[:2]
            
            # Sample edge pixels (border of the image)
            edge_pixels = []
            edge_pixels.extend(img_array[0, :])  # Top edge
            edge_pixels.extend(img_array[-1, :])  # Bottom edge
            edge_pixels.extend(img_array[:, 0])  # Left edge
            edge_pixels.extend(img_array[:, -1])  # Right edge
            
            edge_pixels = np.array(edge_pixels)
            
            # Check if edge pixels are predominantly white/light
            white_edge_pixels = np.sum(np.all(edge_pixels > 220, axis=1))
            edge_white_ratio = white_edge_pixels / len(edge_pixels)
            
            # Method 2: Check for low contrast (indicating uniform background)
            # Calculate standard deviation of pixel values
            gray = np.mean(img_array, axis=2)
            contrast = np.std(gray)
            
            # Method 3: Check for corner uniformity
            # Sample corners to see if they're similar (indicating background)
            corner_size = min(20, height//4, width//4)
            corners = [
                img_array[:corner_size, :corner_size],  # Top-left
                img_array[:corner_size, -corner_size:],  # Top-right
                img_array[-corner_size:, :corner_size],  # Bottom-left
                img_array[-corner_size:, -corner_size:]  # Bottom-right
            ]
            
            corner_means = [np.mean(corner) for corner in corners]
            corner_std = np.std(corner_means)
            
            # Method 4: Check for center vs edge difference
            # If center is very different from edges, it's likely a product shot
            center_h, center_w = height//2, width//2
            center_size = min(40, height//3, width//3)
            center_region = img_array[center_h-center_size//2:center_h+center_size//2,
                                    center_w-center_size//2:center_w+center_size//2]
            
            center_mean = np.mean(center_region)
            edge_mean = np.mean(edge_pixels)
            center_edge_diff = abs(center_mean - edge_mean)
            
            # Decision logic - be more conservative about background detection
            # Only flag as background if it's clearly a problematic background, not clean product photos
            
            has_uniform_edges = edge_white_ratio > 0.8  # Higher threshold for edge uniformity
            has_low_contrast = contrast < 25  # Lower contrast threshold
            has_uniform_corners = corner_std < 15  # More strict corner uniformity
            has_low_center_edge_diff = center_edge_diff < 20  # Lower center-edge difference
            
            # Only consider it a background if:
            # 1. Edges are very uniform (high white ratio) AND
            # 2. Very low contrast (indicating no clear subject) AND
            # 3. Very uniform corners AND
            # 4. Very low center-edge difference (indicating no focused subject)
            # This should catch cluttered/problematic backgrounds but not clean product photos
            
            is_background = (has_uniform_edges and has_low_contrast and 
                           has_uniform_corners and has_low_center_edge_diff)
            
            # Additional check: if there's any significant contrast, it's likely a product photo
            if contrast > 40:
                is_background = False
            
            # Debug output
            if self.debug:
                filename = os.path.basename(image.filename) if hasattr(image, 'filename') else 'unknown'
                self.console.print(f"[dim]Background detection for {filename}:[/dim]")
                self.console.print(f"  [dim]Edge white ratio: {edge_white_ratio:.2f} (uniform: {has_uniform_edges})[/dim]")
                self.console.print(f"  [dim]Contrast: {contrast:.2f} (low: {has_low_contrast})[/dim]")
                self.console.print(f"  [dim]Corner std: {corner_std:.2f} (uniform: {has_uniform_corners})[/dim]")
                self.console.print(f"  [dim]Center-edge diff: {center_edge_diff:.2f} (low: {has_low_center_edge_diff})[/dim]")
                self.console.print(f"  [dim]Result: {'BACKGROUND' if is_background else 'NO BACKGROUND'}[/dim]")
            
            return is_background
            
        except Exception:
            return False
    
    def _detect_detail_shot(self, image: Image.Image) -> bool:
        """Detect if image is a product detail shot (close-up, focused on specific part)"""
        try:
            if not PILLOW_AVAILABLE:
                return False
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for faster processing
            image.thumbnail((200, 200), Image.Resampling.LANCZOS)
            img_array = np.array(image)
            height, width = img_array.shape[:2]
            
            # Method 1: Check for high contrast (detail shots usually have high contrast)
            gray = np.mean(img_array, axis=2)
            contrast = np.std(gray)
            
            # Method 2: Check for edge density (detail shots often have many edges)
            # Convert to grayscale and apply edge detection
            from PIL import ImageFilter
            gray_image = image.convert('L')
            edges = gray_image.filter(ImageFilter.FIND_EDGES)
            edge_array = np.array(edges)
            edge_density = np.sum(edge_array > 50) / edge_array.size
            
            # Method 3: Check for center focus (detail shots usually focus on center)
            center_h, center_w = height//2, width//2
            center_size = min(60, height//2, width//2)
            center_region = img_array[center_h-center_size//2:center_h+center_size//2,
                                    center_w-center_size//2:center_w+center_size//2]
            
            # Check if center has higher contrast than edges
            center_gray = np.mean(center_region, axis=2)
            center_contrast = np.std(center_gray)
            
            # Sample edge regions
            edge_pixels = []
            edge_pixels.extend(img_array[0, :])  # Top edge
            edge_pixels.extend(img_array[-1, :])  # Bottom edge
            edge_pixels.extend(img_array[:, 0])  # Left edge
            edge_pixels.extend(img_array[:, -1])  # Right edge
            edge_pixels = np.array(edge_pixels)
            edge_gray = np.mean(edge_pixels, axis=1)
            edge_contrast = np.std(edge_gray)
            
            # Method 4: Check for uniform background (detail shots often have clean backgrounds)
            # Sample edge pixels for background detection
            white_edge_pixels = np.sum(np.all(edge_pixels > 220, axis=1))
            edge_white_ratio = white_edge_pixels / len(edge_pixels)
            
            # Decision logic for detail shots:
            # 1. High overall contrast (indicating focused detail)
            # 2. High edge density (lots of detail/edges)
            # 3. Center has higher contrast than edges (focused on center)
            # 4. Clean background (uniform edges)
            
            has_high_contrast = contrast > 40
            has_high_edge_density = edge_density > 0.15
            has_center_focus = center_contrast > edge_contrast * 1.2
            has_clean_background = edge_white_ratio > 0.6
            
            # Consider it a detail shot if:
            # - High contrast AND (high edge density OR center focus)
            # - AND has clean background (not cluttered)
            is_detail_shot = (has_high_contrast and (has_high_edge_density or has_center_focus)) and has_clean_background
            
            # Debug output
            if self.debug:
                filename = os.path.basename(image.filename) if hasattr(image, 'filename') else 'unknown'
                self.console.print(f"[dim]Detail shot detection for {filename}:[/dim]")
                self.console.print(f"  [dim]Contrast: {contrast:.2f} (high: {has_high_contrast})[/dim]")
                self.console.print(f"  [dim]Edge density: {edge_density:.3f} (high: {has_high_edge_density})[/dim]")
                self.console.print(f"  [dim]Center focus: {center_contrast:.2f} vs {edge_contrast:.2f} (focused: {has_center_focus})[/dim]")
                self.console.print(f"  [dim]Clean background: {edge_white_ratio:.2f} (clean: {has_clean_background})[/dim]")
                self.console.print(f"  [dim]Result: {'DETAIL SHOT' if is_detail_shot else 'NOT DETAIL SHOT'}[/dim]")
            
            return is_detail_shot
            
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
        detail_shot_count = sum(1 for p in photo_details if p.is_detail_shot)
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
            detail_shot_count=detail_shot_count,
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
                       min_photos: int = 3, export_csv: Optional[str] = None, 
                       show_detail_shots: bool = True) -> None:
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
            table.add_column("Detail Shot Count", style="blue")
            
            for result in background_skus:
                table.add_row(result.sku, str(result.background_count), str(result.detail_shot_count))
            
            self.console.print(table)
        
        # Detail shots
        if show_detail_shots:
            detail_shot_skus = [r for r in results if r.detail_shot_count > 0]
            if detail_shot_skus:
                self.console.print(f"\n[blue]SKUs with detail shots ({len(detail_shot_skus)}):[/blue]")
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("SKU", style="cyan")
                table.add_column("Detail Shot Count", style="blue")
                
                for result in detail_shot_skus:
                    table.add_row(result.sku, str(result.detail_shot_count))
                
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
                    'background_count', 'detail_shot_count', 'low_quality_count', 'issues', 'status'
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
                        'detail_shot_count': result.detail_shot_count,
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
