#!/usr/bin/env python3
"""
Torus Asset Pipeline CLI
A command-line interface for managing asset pipeline operations.
"""

import typer
from typing import Optional
from pathlib import Path
from modules.download import download_photos_from_drive, download_photos_from_drive_parallel
from modules.config import get_folder_id, get_output_dir, get_credentials_file, get_download_config, get_logging_config
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

# Create the main Typer app
app = typer.Typer(
    name="torus-asset-pipeline",
    help="Torus Asset Pipeline - Manage your asset pipeline operations",
    add_completion=False,
)

# Create Rich console for beautiful output
console = Console()

@app.command()
def download(
    folder_id: Optional[str] = typer.Argument(None, help="Google Drive folder ID to download from (uses config default if not provided)"),
    model: Optional[str] = typer.Argument(None, help="Model type (e.g., 'products') (uses config default if not provided)"),
    output_dir: Optional[str] = typer.Option(
        None, 
        "--output-dir", 
        "-o", 
        help="Output directory for downloaded files (uses config default if not provided)"
    ),
    credentials_file: Optional[str] = typer.Option(
        None,
        "--credentials",
        "-c",
        help="Path to Google Drive API credentials file (uses config default if not provided)"
    ),
    verbose: bool = typer.Option(
        None,
        "--verbose",
        "-v",
        help="Enable verbose output (uses config default if not provided)"
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation and download all suppliers automatically"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode with detailed logging"
    )
):
    """
    Download photos from a Google Drive folder and organize them by supplier and SKU.
    
    This command will:
    1. Authenticate with Google Drive API
    2. List all suppliers found in the folder
    3. Ask for confirmation (unless --yes flag is used)
    4. Download all images from all suppliers
    5. Organize them by supplier/SKU structure
    6. Keep original file formats (no conversion)
    
    If folder_id and model are not provided, they will be loaded from config.yaml
    """
    try:
        # Load configuration
        download_config = get_download_config()
        logging_config = get_logging_config()
        
        # Use provided values or fall back to config defaults
        if folder_id is None:
            folder_id = get_folder_id("product_photos")
            if not folder_id:
                typer.echo("Error: No folder ID provided and no default found in config.yaml")
                typer.echo("Please provide a folder ID or set 'google_drive.folder_ids.product_photos' in config.yaml")
                raise typer.Exit(1)
        
        if model is None:
            model = download_config.default_model
        
        if output_dir is None:
            output_dir = get_output_dir("product_photos")
        
        if credentials_file is None:
            credentials_file = get_credentials_file()
        
        if verbose is None:
            verbose = logging_config.verbose
        
        # Display download information in a beautiful panel
        console.print(Panel(
            f"[bold blue]📁 Folder ID:[/bold blue] {folder_id}\n"
            f"[bold blue]📂 Output Directory:[/bold blue] {output_dir}\n"
            f"[bold blue]🔑 Credentials File:[/bold blue] {credentials_file}\n"
            f"[bold blue]📊 Model:[/bold blue] {model}\n"
            f"[bold blue]🔍 Verbose:[/bold blue] {'Yes' if verbose else 'No'}",
            title="🚀 Download Configuration",
            border_style="blue"
        ))
        
        # Check if credentials file exists
        if not Path(credentials_file).exists():
            console.print(f"[red]❌ Error: Credentials file '{credentials_file}' not found![/red]")
            console.print("Please ensure you have a valid Google Drive API credentials file.")
            console.print("You can set the path in config.yaml under 'google_drive.credentials_file'")
            raise typer.Exit(1)
        
        # Call the download functionality
        if debug:
            console.print("[yellow]🐛 Debug mode enabled - detailed logging will be shown[/yellow]")
        
        success = download_photos_from_drive(
            folder_id=folder_id,
            output_dir=output_dir,
            model=model,
            credentials_file=credentials_file,
            verbose=verbose or debug,  # Enable verbose if debug is on
            confirm_all=yes
        )
        
        if not success:
            console.print("[red]❌ Download failed![/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def config():
    """Show current configuration settings."""
    try:
        from modules.config import get_config
        config = get_config()
        
        # Create a beautiful configuration display
        console.print(Panel.fit("⚙️  Torus Asset Pipeline Configuration", style="bold magenta"))
        
        # Google Drive section
        drive_table = Table(title="🔑 Google Drive Settings", show_header=True, header_style="bold cyan")
        drive_table.add_column("Setting", style="cyan")
        drive_table.add_column("Value", style="white")
        
        drive_table.add_row("Credentials File", config.google_drive.credentials_file)
        for operation, folder_id in config.google_drive.folder_ids.items():
            drive_table.add_row(f"Folder ID ({operation})", folder_id)
        
        console.print(drive_table)
        
        # Output directories section
        output_table = Table(title="📁 Output Directories", show_header=True, header_style="bold green")
        output_table.add_column("Directory Type", style="green")
        output_table.add_column("Path", style="white")
        
        output_table.add_row("Base", config.output_directories.base)
        output_table.add_row("Product Photos", config.output_directories.product_photos)
        output_table.add_row("Category Images", config.output_directories.category_images)
        output_table.add_row("Models", config.output_directories.models)
        output_table.add_row("Reports", config.output_directories.reports)
        output_table.add_row("Temp", config.output_directories.temp)
        
        console.print(output_table)
        
        # Download settings section
        download_table = Table(title="⚡ Download Settings", show_header=True, header_style="bold yellow")
        download_table.add_column("Setting", style="yellow")
        download_table.add_column("Value", style="white")
        
        download_table.add_row("Default Model", config.download.default_model)
        download_table.add_row("Convert to JPG", str(config.download.image_processing['convert_to_jpg']))
        download_table.add_row("Ask Confirmation", str(config.download.behavior['ask_confirmation']))
        download_table.add_row("Download All Suppliers", str(config.download.behavior['download_all_suppliers']))
        
        console.print(download_table)
        
        # Logging section
        logging_table = Table(title="📝 Logging Settings", show_header=True, header_style="bold blue")
        logging_table.add_column("Setting", style="blue")
        logging_table.add_column("Value", style="white")
        
        logging_table.add_row("Level", config.logging.level)
        logging_table.add_row("Verbose", str(config.logging.verbose))
        logging_table.add_row("Log File", config.logging.log_file or "None")
        
        console.print(logging_table)
        
    except Exception as e:
        console.print(f"[red]❌ Error loading configuration: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def download_simple(
    folder_id: Optional[str] = typer.Argument(None, help="Google Drive folder ID to download from (uses config default if not provided)"),
    model: Optional[str] = typer.Argument(None, help="Model type (e.g., 'products') (uses config default if not provided)"),
    output_dir: Optional[str] = typer.Option(
        None, 
        "--output-dir", 
        "-o", 
        help="Output directory for downloaded files (uses config default if not provided)"
    ),
    credentials_file: Optional[str] = typer.Option(
        None,
        "--credentials",
        "-c",
        help="Path to Google Drive API credentials file (uses config default if not provided)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation and download all suppliers automatically"
    )
):
    """Simple download command without complex progress bars (for debugging)."""
    try:
        from modules.download_simple import download_photos_from_drive_simple
        
        # Load configuration
        download_config = get_download_config()
        logging_config = get_logging_config()
        
        # Use provided values or fall back to config defaults
        if folder_id is None:
            folder_id = get_folder_id("product_photos")
            if not folder_id:
                console.print("Error: No folder ID provided and no default found in config.yaml")
                raise typer.Exit(1)
        
        if model is None:
            model = download_config.default_model
        
        if output_dir is None:
            output_dir = get_output_dir("product_photos")
        
        if credentials_file is None:
            credentials_file = get_credentials_file()
        
        # Display download information
        console.print(Panel(
            f"[bold blue]📁 Folder ID:[/bold blue] {folder_id}\n"
            f"[bold blue]📂 Output Directory:[/bold blue] {output_dir}\n"
            f"[bold blue]🔑 Credentials File:[/bold blue] {credentials_file}\n"
            f"[bold blue]📊 Model:[/bold blue] {model}",
            title="🚀 Simple Download Configuration",
            border_style="blue"
        ))
        
        # Check if credentials file exists
        if not Path(credentials_file).exists():
            console.print(f"[red]❌ Error: Credentials file '{credentials_file}' not found![/red]")
            raise typer.Exit(1)
        
        # Call the simple download functionality
        success = download_photos_from_drive_simple(
            folder_id=folder_id,
            output_dir=output_dir,
            model=model,
            credentials_file=credentials_file,
            verbose=verbose,
            confirm_all=yes
        )
        
        if not success:
            console.print("[red]❌ Download failed![/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def download_fast(
    folder_id: Optional[str] = typer.Argument(None, help="Google Drive folder ID to download from (uses config default if not provided)"),
    model: Optional[str] = typer.Argument(None, help="Model type (e.g., 'products') (uses config default if not provided)"),
    output_dir: Optional[str] = typer.Option(
        None, 
        "--output-dir", 
        "-o", 
        help="Output directory for downloaded files (uses config default if not provided)"
    ),
    credentials_file: Optional[str] = typer.Option(
        None,
        "--credentials",
        "-c",
        help="Path to Google Drive API credentials file (uses config default if not provided)"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output"
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation and download all suppliers automatically"
    ),
    workers: int = typer.Option(
        5,
        "--workers",
        "-w",
        help="Number of parallel download workers (default: 5)"
    )
):
    """Fast parallel download command with threading for much faster downloads."""
    try:
        # Load configuration
        download_config = get_download_config()
        logging_config = get_logging_config()
        
        # Use provided values or fall back to config defaults
        if folder_id is None:
            folder_id = get_folder_id("product_photos")
            if not folder_id:
                console.print("Error: No folder ID provided and no default found in config.yaml")
                raise typer.Exit(1)
        
        if model is None:
            model = download_config.default_model
        
        if output_dir is None:
            output_dir = get_output_dir("product_photos")
        
        if credentials_file is None:
            credentials_file = get_credentials_file()
        
        # Display download information
        console.print(Panel(
            f"[bold blue]📁 Folder ID:[/bold blue] {folder_id}\n"
            f"[bold blue]📂 Output Directory:[/bold blue] {output_dir}\n"
            f"[bold blue]🔑 Credentials File:[/bold blue] {credentials_file}\n"
            f"[bold blue]📊 Model:[/bold blue] {model}\n"
            f"[bold blue]⚡ Workers:[/bold blue] {workers}",
            title="🚀 Fast Download Configuration",
            border_style="green"
        ))
        
        # Check if credentials file exists
        if not Path(credentials_file).exists():
            console.print(f"[red]❌ Error: Credentials file '{credentials_file}' not found![/red]")
            raise typer.Exit(1)
        
        # Call the parallel download functionality
        success = download_photos_from_drive_parallel(
            folder_id=folder_id,
            output_dir=output_dir,
            model=model,
            credentials_file=credentials_file,
            verbose=verbose,
            confirm_all=yes,
            max_workers=workers
        )
        
        if not success:
            console.print("[red]❌ Download failed![/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def list():
    """List available commands and their descriptions."""
    commands_table = Table(title="🚀 Available Commands", show_header=True, header_style="bold magenta")
    commands_table.add_column("Command", style="cyan", width=12)
    commands_table.add_column("Description", style="white")
    commands_table.add_column("Emoji", style="yellow", width=4)
    
    commands_table.add_row("download", "Download photos from Google Drive (sequential)", "📥")
    commands_table.add_row("download-fast", "Fast parallel download with threading (5x faster)", "⚡")
    commands_table.add_row("config", "Show current configuration settings", "⚙️")
    commands_table.add_row("list", "List available commands", "📋")
    commands_table.add_row("help", "Show help for a specific command", "❓")
    
    console.print(commands_table)
    
    console.print("\n[dim]💡 Tip: Use 'python cli.py <command> --help' for detailed help on any command[/dim]")

if __name__ == "__main__":
    app()
