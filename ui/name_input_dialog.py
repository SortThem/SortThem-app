import pygame
import logging
from typing import Callable, Optional, Tuple

logger = logging.getLogger(__name__)

class NameInputDialog:
    """Separate class for handling directory name input dialog"""
    
    def __init__(self, screen: pygame.Surface, font: pygame.font.Font, small_font: pygame.font.Font):
        self.screen = screen
        self.font = font
        self.small_font = small_font
        self.active = False
        self.letter = None
        self.input_text = ""
        self.callback = None
        self.dialog_rect = None
        self.ok_rect = None
        self.cancel_rect = None
        self.input_rect = None
        
    def show(self, letter: str, callback: Callable):
        """Show dialog for a specific letter"""
        self.active = True
        self.letter = letter
        self.input_text = ""
        self.callback = callback
        logger.info(f"Showing directory input dialog for key '{letter}'")
        
    def hide(self):
        """Hide the dialog"""
        self.active = False
        self.letter = None
        self.input_text = ""
        self.callback = None
        
    def handle_keydown(self, event) -> bool:
        """Handle keyboard input when dialog is active"""
        if not self.active:
            return False
            
        if event.key == pygame.K_RETURN:
            if self.input_text:
                logger.info(f"Dialog confirmed: key '{self.letter}' -> directory '{self.input_text}'")
                if self.callback:
                    self.callback(self.letter, self.input_text)
            self.hide()
            return True
            
        elif event.key == pygame.K_ESCAPE:
            logger.info(f"Dialog cancelled for key '{self.letter}'")
            self.hide()
            return True
            
        elif event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
            return True
            
        else:
            if len(self.input_text) < 100 and event.unicode.isprintable() and event.unicode not in '/\\:?*"<>|':
                self.input_text += event.unicode
                return True
                
        return False
    
    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse clicks on dialog buttons"""
        if not self.active:
            return False
            
        if self.ok_rect and self.ok_rect.collidepoint(pos):
            if self.input_text:
                logger.info(f"Dialog OK clicked: key '{self.letter}' -> directory '{self.input_text}'")
                if self.callback:
                    self.callback(self.letter, self.input_text)
            self.hide()
            return True
            
        elif self.cancel_rect and self.cancel_rect.collidepoint(pos):
            logger.info(f"Dialog Cancel clicked for key '{self.letter}'")
            self.hide()
            return True
            
        return False
    
    def update_rects(self):
        """Update dialog rectangle positions based on screen size"""
        screen_width, screen_height = self.screen.get_size()
        
        dialog_width = 500
        dialog_height = 200
        self.dialog_rect = pygame.Rect(
            (screen_width - dialog_width) // 2,
            (screen_height - dialog_height) // 2,
            dialog_width, dialog_height
        )
        
        self.input_rect = pygame.Rect(
            self.dialog_rect.left + 20,
            self.dialog_rect.top + 80,
            dialog_width - 40,
            40
        )
        
        self.ok_rect = pygame.Rect(
            self.dialog_rect.centerx - 80,
            self.dialog_rect.bottom - 50,
            70, 30
        )
        
        self.cancel_rect = pygame.Rect(
            self.dialog_rect.centerx + 10,
            self.dialog_rect.bottom - 50,
            70, 30
        )
    
    def draw(self):
        """Draw the dialog"""
        if not self.active:
            return
            
        self.update_rects()
        
        # Draw dialog background
        pygame.draw.rect(self.screen, (50, 50, 50), self.dialog_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.dialog_rect, 3)
        
        # Draw prompt
        prompt = self.small_font.render(
            f"Enter directory name for key '{self.letter}':", 
            True, (255, 255, 255)
        )
        prompt_rect = prompt.get_rect(center=(self.dialog_rect.centerx, self.dialog_rect.top + 40))
        self.screen.blit(prompt, prompt_rect)
        
        # Draw input field
        pygame.draw.rect(self.screen, (255, 255, 255), self.input_rect, 2)
        pygame.draw.rect(self.screen, (30, 30, 30), self.input_rect)
        
        # Draw input text
        text_surface = self.font.render(self.input_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(midleft=(self.input_rect.left + 10, self.input_rect.centery))
        self.screen.blit(text_surface, text_rect)
        
        # Draw blinking cursor
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = text_rect.right + 2
            cursor_rect = pygame.Rect(cursor_x, self.input_rect.top + 5, 2, self.input_rect.height - 10)
            pygame.draw.rect(self.screen, (255, 255, 255), cursor_rect)
        
        # Draw buttons
        pygame.draw.rect(self.screen, (0, 100, 0), self.ok_rect)
        pygame.draw.rect(self.screen, (100, 0, 0), self.cancel_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), self.ok_rect, 2)
        pygame.draw.rect(self.screen, (255, 255, 255), self.cancel_rect, 2)
        
        ok_text = self.small_font.render("OK", True, (255, 255, 255))
        cancel_text = self.small_font.render("Cancel", True, (255, 255, 255))
        
        ok_text_rect = ok_text.get_rect(center=self.ok_rect.center)
        cancel_text_rect = cancel_text.get_rect(center=self.cancel_rect.center)
        
        self.screen.blit(ok_text, ok_text_rect)
        self.screen.blit(cancel_text, cancel_text_rect)
    
    def is_active(self) -> bool:
        """Check if dialog is active"""
        return self.active
