import pygame
from typing import Optional

class KeyboardButton:
    """Represents a single keyboard button"""
    
    def __init__(self, letter: str, rect: pygame.Rect, directory: Optional[str] = None):
        self.letter = letter
        self.rect = rect
        self.directory = directory
        self.is_hovered = False
        self.is_pressed = False
    
    def draw(self, screen: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font):
        """Draw the button with semi-transparent background"""
        button_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        
        # Different colors based on state
        if self.is_pressed:
            bg_color = (50, 200, 50, 220)  # Green for pressed/active
            border_color = (255, 255, 255, 255)
        elif self.is_hovered:
            bg_color = (100, 160, 210, 200)  # Blue for hover
            border_color = (255, 255, 255, 255)
        else:
            bg_color = (70, 130, 180, 180)  # Normal blue
            border_color = (200, 200, 200, 200)
        
        pygame.draw.rect(button_surface, bg_color, button_surface.get_rect())
        pygame.draw.rect(button_surface, border_color, button_surface.get_rect(), 3)
        
        # Draw letter
        text = font.render(self.letter, True, (255, 255, 255))
        text_rect = text.get_rect(center=button_surface.get_rect().center)
        button_surface.blit(text, text_rect)
        
        # Draw directory name if assigned
        if self.directory:
            dir_text = small_font.render(self.directory[:15], True, (220, 220, 220))
            dir_rect = dir_text.get_rect(center=(button_surface.get_rect().centerx, 
                                                button_surface.get_rect().bottom - 15))
            button_surface.blit(dir_text, dir_rect)
        
        screen.blit(button_surface, self.rect)
    
    def set_directory(self, directory: str):
        """Set the directory for this button"""
        self.directory = directory
    
    def clear_directory(self):
        """Clear the directory binding"""
        self.directory = None
    
    def set_pressed(self, pressed: bool):
        """Set pressed state"""
        self.is_pressed = pressed
