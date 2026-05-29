import shutil
from pathlib import Path
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class ImageList:
    """Manages list of images and file operations without full reloads"""

    def __init__(self, directory: str = "."):
        self.base_directory = Path(directory).resolve()
        self.current_directory = self.base_directory
        self.images: List[Path] = []
        self.current_index = 0
        self.image_directories: Dict[Path, Optional[str]] = {}  # Track which subdir each image is in
        self.load_images()

    def load_images(self):
        """Load all images from current directory and all subdirectories recursively"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        self.images = []
        self.image_directories = {}

        # Use rglob to search recursively through all subdirectories
        for ext in image_extensions:
            for image_path in self.base_directory.rglob(f'*{ext}'):
                self.images.append(image_path)
                self._track_image_directory(image_path)

            for image_path in self.base_directory.rglob(f'*{ext.upper()}'):
                self.images.append(image_path)
                self._track_image_directory(image_path)

        # Remove duplicates and sort by filename only
        self.images = sorted(set(self.images), key=lambda p: p.name.lower())
        self.current_index = 0 if self.images else -1

        # Rebuild directory tracking after sorting
        self.image_directories = {}
        for img in self.images:
            self._track_image_directory(img)

        # Log results
        image_count = len(self.images)
        if image_count > 0:
            root_images = sum(1 for img in self.images if self.get_image_subdirectory(img) is None)
            subdir_images = image_count - root_images
            logger.info(f"Loaded {image_count} images from {self.base_directory} and subdirectories "
                       f"({root_images} in root, {subdir_images} in subdirectories)")
        else:
            logger.info(f"No images found in {self.base_directory} or its subdirectories")

    def _track_image_directory(self, image_path: Path):
        """Track which subdirectory an image belongs to"""
        try:
            relative = image_path.relative_to(self.base_directory)
            if relative.parent == Path('.'):
                self.image_directories[image_path] = None  # In root directory
            else:
                self.image_directories[image_path] = str(relative.parent)
        except ValueError:
            self.image_directories[image_path] = None

    def get_image_subdirectory(self, image_path: Path) -> Optional[str]:
        """Get the subdirectory name for a given image (or None if in root)"""
        return self.image_directories.get(image_path)

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
        logger.debug(f"Navigation: next image -> {current.name if current else 'None'} (index {self.current_index})")
        return current

    def previous_image(self) -> Optional[Path]:
        """Go to previous image"""
        if not self.images:
            return None
        self.current_index = (self.current_index - 1) % len(self.images)
        current = self.get_current_image()
        logger.debug(f"Navigation: previous image -> {current.name if current else 'None'} (index {self.current_index})")
        return current

    def move_current_image_to_subdir(self, subdir_name: str) -> bool:
        """
        Move current image to a subdirectory WITHOUT reloading entire list.
        Updates the internal list structure efficiently.
        """
        current_image = self.get_current_image()
        if not current_image or not current_image.exists():
            logger.warning(f"Cannot move: no current image or file doesn't exist")
            return False

        # Check if already in this directory
        current_subdir = self.get_image_subdirectory(current_image)
        if current_subdir == subdir_name:
            logger.info(f"Image already in '{subdir_name}', skipping move")
            return True

        target_dir = self.base_directory / subdir_name
        target_dir.mkdir(parents=True, exist_ok=True)

        new_path = target_dir / current_image.name

        # Handle duplicate filenames
        counter = 1
        original_stem = current_image.stem
        original_suffix = current_image.suffix

        while new_path.exists():
            new_path = target_dir / f"{original_stem}_{counter}{original_suffix}"
            counter += 1

        try:
            # Physically move the file
            current_image.rename(new_path)
            logger.info(f"Moved image: {current_image.name} -> {new_path}")

            # Update the image list in memory (no reload!)
            old_index = self.current_index

            # Replace the path in the images list
            self.images[old_index] = new_path

            # Update directory tracking
            self.image_directories[new_path] = subdir_name
            del self.image_directories[current_image]

            # Re-sort the list if filename changed (it didn't, but for consistency)
            # Actually filename stayed same, so no resort needed, but we maintain order
            self.images.sort(key=lambda p: p.name.lower())

            # Find the new index after sorting (if position changed)
            try:
                self.current_index = self.images.index(new_path)
            except ValueError:
                self.current_index = old_index

            # Jump to next image (don't stay on moved one)
            self.next_image()

            return True

        except Exception as e:
            logger.error(f"Failed to move image: {e}")
            return False

    def move_current_image_back(self) -> bool:
        """
        Move current image back to base directory WITHOUT reloading entire list.
        Updates the internal list structure efficiently.
        """
        current_image = self.get_current_image()
        if not current_image or not current_image.exists():
            logger.warning(f"Cannot move back: no current image or file doesn't exist")
            return False

        # Check if already in base directory
        current_subdir = self.get_image_subdirectory(current_image)
        if current_subdir is None:
            logger.info("Image already in base directory, cannot move back")
            return False

        target_dir = self.base_directory
        new_path = target_dir / current_image.name

        # Handle duplicate filenames
        counter = 1
        original_stem = current_image.stem
        original_suffix = current_image.suffix

        while new_path.exists():
            new_path = target_dir / f"{original_stem}_{counter}{original_suffix}"
            counter += 1

        try:
            # Physically move the file
            current_image.rename(new_path)
            logger.info(f"Moved back image: {current_image.name} -> {new_path}")

            # Update the image list in memory (no reload!)
            old_index = self.current_index

            # Replace the path in the images list
            self.images[old_index] = new_path

            # Update directory tracking
            self.image_directories[new_path] = None
            del self.image_directories[current_image]

            # Try to remove empty subdirectory
            source_dir = current_image.parent
            if source_dir != self.base_directory and not any(source_dir.iterdir()):
                try:
                    source_dir.rmdir()
                    logger.info(f"Removed empty directory: {source_dir}")
                except Exception as e:
                    logger.debug(f"Could not remove directory {source_dir}: {e}")

            # Re-sort the list
            self.images.sort(key=lambda p: p.name.lower())

            # Find the new index after sorting
            try:
                self.current_index = self.images.index(new_path)
            except ValueError:
                self.current_index = old_index

            # Jump to next image
            self.next_image()

            return True

        except Exception as e:
            logger.error(f"Failed to move image back: {e}")
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

    def refresh(self):
        """
        Full refresh of image list (useful when external changes occur).
        This is the expensive operation, use sparingly.
        """
        logger.info("Performing full image list refresh")
        old_index = self.current_index
        old_image = self.get_current_image()

        self.load_images()

        # Try to restore position to same image if it still exists
        if old_image and old_image in self.images:
            self.current_index = self.images.index(old_image)
        elif self.images:
            self.current_index = min(old_index, len(self.images) - 1)
