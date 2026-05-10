import pygame
import logging

logger = logging.getLogger(__name__)

class MessageManager:
    """Manages temporary on-screen messages"""
    
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font):
        self.screen = screen
        self.font = font
        self.message = ""
        self.message_timer = 0
    
    def show(self, text: str, duration: int = 60):
        """Show a temporary message"""
        self.message = text
        self.message_timer = duration
        logger.info(f"UI Message: {text}")
    
    def update(self):
        """Update message timer"""
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.message = ""
    
    def draw(self):
        """Draw message if active"""
        if self.message_timer > 0 and self.message:
            text_surface = self.font.render(self.message, True, (255, 255, 255))
            text_rect = text_surface.get_rect()
            padding = 20
            bg_rect = text_rect.inflate(padding * 2, padding)
            bg_rect.center = (self.screen.get_width() // 2, 100)
            
            overlay = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, bg_rect)
            pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, 2)
            
            text_rect.center = bg_rect.center
            self.screen.blit(text_surface, text_rect)
