import pygame
from typing import Tuple
from utils.logger_setup import setup_logger

logger = setup_logger(__name__)


class ImageViewer:
    """Class for displaying images without proportion distortion"""
    
    def __init__(self, screen: pygame.Surface, image_path: str):
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
        self.original_image = pygame.image.load(image_path)
        self.image_path = image_path
        self.image = None
        self.image_rect = None
        self.zoom_level = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.calculate_initial_zoom()
        self.update_image()
        logger.info(f"Loaded image: {image_path}")
    
    def calculate_initial_zoom(self):
        """Calculate zoom level so the whole image is visible"""
        img_width, img_height = self.original_image.get_size()
        
        # Calculate zoom needed to fit width and height
        zoom_x = self.screen_width / img_width
        zoom_y = self.screen_height / img_height
        
        # Use the smaller zoom to ensure whole image fits
        self.zoom_level = min(zoom_x, zoom_y)
        
        # Reset offsets to center the image
        self.offset_x = 0
        self.offset_y = 0
    
    def update_image(self):
        """Update the scaled image maintaining aspect ratio"""
        img_width, img_height = self.original_image.get_size()
        
        # Apply zoom
        scaled_width = int(img_width * self.zoom_level)
        scaled_height = int(img_height * self.zoom_level)
        
        # Scale the image
        self.image = pygame.transform.scale(self.original_image, (scaled_width, scaled_height))
        
        # Calculate position to center the image
        self.image_rect = self.image.get_rect()
        self.image_rect.center = (self.screen_width // 2 + self.offset_x, 
                                  self.screen_height // 2 + self.offset_y)
    
    def zoom(self, amount: float, mouse_pos: Tuple[int, int]):
        """Zoom in/out at mouse position"""
        old_zoom = self.zoom_level
        self.zoom_level = max(0.1, min(5.0, self.zoom_level + amount))
        
        # Adjust offset to zoom towards mouse position
        if old_zoom != self.zoom_level:
            mouse_x, mouse_y = mouse_pos
            screen_center_x = self.screen_width // 2
            screen_center_y = self.screen_height // 2
            
            # Calculate mouse position relative to image center
            rel_x = mouse_x - (screen_center_x + self.offset_x)
            rel_y = mouse_y - (screen_center_y + self.offset_y)
            
            # Adjust offset
            zoom_ratio = self.zoom_level / old_zoom
            self.offset_x = mouse_x - screen_center_x - (rel_x * zoom_ratio)
            self.offset_y = mouse_y - screen_center_y - (rel_y * zoom_ratio)
            
            self.update_image()
            logger.debug(f"Zoom level: {self.zoom_level:.2f}")
    
    def draw(self):
        """Draw the image on screen"""
        if self.image:
            self.screen.blit(self.image, self.image_rect)
