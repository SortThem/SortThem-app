import configparser
from pathlib import Path
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, app_name: str = "sortthem"):
        self.app_name = app_name
        self.config = configparser.ConfigParser()
        self.config_path = self._get_config_path()
    
    def _get_config_path(self) -> Path:
        """Get the standard user config directory path"""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', Path.home() / 'AppData/Roaming'))
        else:  # Linux, macOS
            config_dir = Path.home() / '.config'
        
        app_config_dir = config_dir / self.app_name
        app_config_dir.mkdir(parents=True, exist_ok=True)
        return app_config_dir / 'config.ini'
    
    def load(self) -> configparser.ConfigParser:
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                self.config.read(self.config_path)
                logger.info(f"Config loaded from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        else:
            logger.info(f"No existing config found at {self.config_path}")
        
        return self.config
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                self.config.write(f)
            logger.info(f"Config saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get_bindings(self) -> Dict[str, str]:
        """Get key bindings from config"""
        bindings = {}
        if self.config.has_section('KeyBindings'):
            for key, value in self.config.items('KeyBindings'):
                bindings[key] = value
        return bindings
    
    def set_bindings(self, bindings: Dict[str, Optional[str]]):
        """Set key bindings in config"""
        if not self.config.has_section('KeyBindings'):
            self.config.add_section('KeyBindings')
        
        for key, value in bindings.items():
            if value:
                self.config.set('KeyBindings', key, value)
            else:
                if self.config.has_option('KeyBindings', key):
                    self.config.remove_option('KeyBindings', key)
