import logging
from typing import Optional
from pathlib import Path
from utils.logger_setup import setup_logger

logger = setup_logger(__name__)


class ImageList:
    """Manages list of images and file operations"""
    
    def __init__(self, directory: str = "."):
        self.base_directory = Path(directory).resolve()
        self.current_directory = self.base_directory
        self.images: List[Path] = []
        self.current_index = 0
        self.load_images()
        logger.info(f"ImageList initialized with base directory: {self.base_directory}")

    def load_images(self):
        """Load all images from current directory and all subdirectories recursively"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        self.images = []
        
        # Use rglob to search recursively through all subdirectories
        for ext in image_extensions:
            # Search for lowercase extensions
            self.images.extend(self.current_directory.rglob(f'*{ext}'))
            # Search for uppercase extensions
            self.images.extend(self.current_directory.rglob(f'*{ext.upper()}'))
        
        # Remove duplicates (in case same file matches both patterns) and sort
        self.images = sorted(set(self.images))
        self.current_index = 0 if self.images else -1
        
        # Log statistics about found images
        image_count = len(self.images)
        if image_count > 0:
            # Count images in subdirectories vs root
            root_images = sum(1 for img in self.images if img.parent == self.current_directory)
            subdir_images = image_count - root_images
            logger.info(f"Loaded {image_count} images from {self.current_directory} and subdirectories "
                       f"({root_images} in root, {subdir_images} in subdirectories)")
        else:
            logger.info(f"No images found in {self.current_directory} or its subdirectories")
    

    def get_current_image(self) -> Optional[Path]:
        """Get current image path"""
        if 0 <= self.current_index < len(self.images):
            return self.images[self.current_index]
        return None
    
    def next_image(self) -> Optional[Path]:
        """Go to next image"""
        if not self.images:
            return None
        self.current_index = (self.current_index + 1) % len(self.images)
        current = self.get_current_image()
        logger.info(f"Navigation: next image -> {current.name if current else 'None'}")
        return current
    
    def previous_image(self) -> Optional[Path]:
        """Go to previous image"""
        if not self.images:
            return None
        self.current_index = (self.current_index - 1) % len(self.images)
        current = self.get_current_image()
        logger.info(f"Navigation: previous image -> {current.name if current else 'None'}")
        return current
    
    def move_current_image_to_subdir(self, subdir_name: str) -> bool:
        """Move current image to a subdirectory of the current directory"""
        current_image = self.get_current_image()
        if not current_image or not current_image.exists():
            logger.warning(f"Cannot move: no current image or file doesn't exist")
            return False
        
        target_dir = self.current_directory / subdir_name
        target_dir.mkdir(parents=True, exist_ok=True)
        
        new_path = target_dir / current_image.name
        
        # Handle duplicate filenames
        counter = 1
        while new_path.exists():
            stem = current_image.stem
            suffix = current_image.suffix
            new_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        try:
            current_image.rename(new_path)
            logger.info(f"Moved image: {current_image.name} -> {new_path}")
            self.load_images()
            return True
        except Exception as e:
            logger.error(f"Failed to move image: {e}")
            return False
    
    def move_current_image_back(self) -> bool:
        """Move current image back to base directory if it's in a subfolder"""
        current_image = self.get_current_image()
        if not current_image or not current_image.exists():
            logger.warning(f"Cannot move back: no current image or file doesn't exist")
            return False
        
        try:
            relative_path = current_image.relative_to(self.base_directory)
            if len(relative_path.parents) > 0 and str(relative_path.parent) != '.':
                # Image is in a subfolder, move it back
                target_dir = self.base_directory
                new_path = target_dir / current_image.name
                
                counter = 1
                while new_path.exists():
                    stem = current_image.stem
                    suffix = current_image.suffix
                    new_path = target_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                current_image.rename(new_path)
                logger.info(f"Moved back image: {current_image.name} -> {new_path}")
                
                # Try to remove empty subdirectory
                source_dir = current_image.parent
                if source_dir != self.base_directory and not any(source_dir.iterdir()):
                    try:
                        source_dir.rmdir()
                        logger.info(f"Removed empty directory: {source_dir}")
                    except Exception as e:
                        logger.debug(f"Could not remove directory {source_dir}: {e}")
                
                self.load_images()
                return True
            else:
                logger.info(f"Image already in base directory, cannot move back")
                return False
        except ValueError:
            logger.warning(f"Cannot determine relative path for {current_image}")
            return False
    
    def is_empty(self) -> bool:
        return len(self.images) == 0
    
    def get_count(self) -> int:
        return len(self.images)
    
    def get_index_info(self) -> str:
        if self.is_empty():
            return "No images"
        return f"{self.current_index + 1}/{len(self.images)}"
    
    def get_current_image_path(self) -> Optional[Path]:
        return self.get_current_image()

