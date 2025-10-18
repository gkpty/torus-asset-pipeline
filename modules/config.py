"""
Configuration management module for Torus Asset Pipeline
Handles loading and accessing YAML configuration files
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class GoogleDriveConfig:
    """Google Drive configuration settings"""
    folder_ids: Dict[str, str]
    credentials_file: str


@dataclass
class OutputDirectoriesConfig:
    """Output directories configuration"""
    base: str
    product_photos: str
    category_images: str
    models: str
    reports: str
    temp: str


@dataclass
class DownloadConfig:
    """Download configuration settings"""
    default_model: str
    image_processing: Dict[str, Any]
    behavior: Dict[str, Any]


@dataclass
class LoggingConfig:
    """Logging configuration settings"""
    level: str
    verbose: bool
    log_file: Optional[str]


@dataclass
class ProcessingConfig:
    """Processing configuration settings"""
    batch_size: int
    max_concurrent_downloads: int
    retry: Dict[str, int]


@dataclass
class FileOrganizationConfig:
    """File organization configuration"""
    structure: str
    include_date: bool
    date_format: str


@dataclass
class ValidationConfig:
    """Validation configuration settings"""
    allowed_image_extensions: list
    max_file_size_mb: int
    validate_integrity: bool


@dataclass
class Config:
    """Main configuration class"""
    google_drive: GoogleDriveConfig
    output_directories: OutputDirectoriesConfig
    download: DownloadConfig
    logging: LoggingConfig
    processing: ProcessingConfig
    file_organization: FileOrganizationConfig
    validation: ValidationConfig


class ConfigManager:
    """Manages configuration loading and access"""
    
    def __init__(self, config_file: str = "config.yaml"):
        self.config_file = config_file
        self._config: Optional[Config] = None
    
    def load_config(self) -> Config:
        """Load configuration from YAML file"""
        if self._config is not None:
            return self._config
        
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
            
            # Parse configuration into dataclasses
            self._config = self._parse_config(config_data)
            return self._config
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration file: {e}")
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")
    
    def _parse_config(self, config_data: Dict[str, Any]) -> Config:
        """Parse configuration data into dataclasses"""
        return Config(
            google_drive=GoogleDriveConfig(**config_data.get('google_drive', {})),
            output_directories=OutputDirectoriesConfig(**config_data.get('output_directories', {})),
            download=DownloadConfig(**config_data.get('download', {})),
            logging=LoggingConfig(**config_data.get('logging', {})),
            processing=ProcessingConfig(**config_data.get('processing', {})),
            file_organization=FileOrganizationConfig(**config_data.get('file_organization', {})),
            validation=ValidationConfig(**config_data.get('validation', {}))
        )
    
    def get_folder_id(self, operation: str) -> str:
        """Get folder ID for a specific operation"""
        config = self.load_config()
        return config.google_drive.folder_ids.get(operation, "")
    
    def get_output_dir(self, operation: str) -> str:
        """Get output directory for a specific operation"""
        config = self.load_config()
        output_dirs = config.output_directories
        
        if operation == "product_photos":
            return output_dirs.product_photos
        elif operation == "category_images":
            return output_dirs.category_images
        elif operation == "models":
            return output_dirs.models
        elif operation == "reports":
            return output_dirs.reports
        elif operation == "temp":
            return output_dirs.temp
        else:
            return output_dirs.base
    
    def get_credentials_file(self) -> str:
        """Get credentials file path"""
        config = self.load_config()
        return config.google_drive.credentials_file
    
    def get_download_config(self) -> DownloadConfig:
        """Get download configuration"""
        config = self.load_config()
        return config.download
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        config = self.load_config()
        return config.logging
    
    def get_validation_config(self) -> ValidationConfig:
        """Get validation configuration"""
        config = self.load_config()
        return config.validation
    
    def reload_config(self) -> Config:
        """Reload configuration from file"""
        self._config = None
        return self.load_config()


# Global config manager instance
config_manager = ConfigManager()


def get_config() -> Config:
    """Get the global configuration instance"""
    return config_manager.load_config()


def get_folder_id(operation: str) -> str:
    """Get folder ID for a specific operation"""
    return config_manager.get_folder_id(operation)


def get_output_dir(operation: str) -> str:
    """Get output directory for a specific operation"""
    return config_manager.get_output_dir(operation)


def get_credentials_file() -> str:
    """Get credentials file path"""
    return config_manager.get_credentials_file()


def get_download_config() -> DownloadConfig:
    """Get download configuration"""
    return config_manager.get_download_config()


def get_logging_config() -> LoggingConfig:
    """Get logging configuration"""
    return config_manager.get_logging_config()


def get_validation_config() -> ValidationConfig:
    """Get validation configuration"""
    return config_manager.get_validation_config()
