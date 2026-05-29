import pygame
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

from core.image_list import ImageList
from core.image_viewer import ImageViewer
from core.button_panel import ButtonPanel
from ui.name_input_dialog import NameInputDialog
from ui.message_manager import MessageManager
from utils.config_manager import ConfigManager
from utils.logger_setup import setup_logger

logger = setup_logger(__name__)


class AppMode(Enum):
    """Application operation modes"""
    VIEWING = "viewing"          # Normal image viewing mode
    DIALOG = "dialog"            # Input dialog active
    MOVING = "moving"            # In the process of moving an image


class SortThemApp:
    """Main application class with state management"""

    def __init__(self):
        logger.info("Starting SortThemApp initialization")
        pygame.init()

        # Setup display
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h

        # Development mode: windowed; Production: fullscreen
        import sys
        if hasattr(sys, 'frozen'):
            # Packaged app - use fullscreen
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                pygame.FULLSCREEN
            )
        else:
            # Development - use windowed mode
            self.screen_width = 800
            self.screen_height = 600
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height)
            )

        pygame.display.set_caption("SortThem - Image Organizer")
        logger.info(f"Display initialized: {self.screen_width}x{self.screen_height}")

        # Initialize fonts
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Initialize components
        self.image_list = ImageList()
        self.button_panel = ButtonPanel(self.screen)
        self.dialog = NameInputDialog(self.screen, self.font, self.small_font)
        self.message_manager = MessageManager(self.screen, self.font)
        self.config_manager = ConfigManager()

        self.image_viewer = None
        self.current_mode = AppMode.VIEWING
        self.clock = pygame.time.Clock()

        # Pending action after dialog closes
        self.pending_letter = None

        # Load configuration
        self.config = self.config_manager.load()
        self.button_panel.load_bindings(self.config)

        # Load first image
        self.load_current_image()

        logger.info("SortThemApp initialization complete")

    def load_current_image(self):
        """Load the current image into the viewer"""
        current_image = self.image_list.get_current_image()
        if current_image and current_image.exists():
            self.image_viewer = ImageViewer(self.screen, str(current_image))
            self.button_panel.update_pressed_state(current_image, self.image_list.base_directory)
        else:
            self.image_viewer = None
            if not self.image_list.is_empty():
                logger.warning(f"Could not load image: {current_image}")

    def handle_letter_action(self, letter: str, dir_name: str):
        """Handle letter button action (bind directory and move image)"""
        logger.info(f"Processing letter action: '{letter}' -> directory '{dir_name}'")

        self.button_panel.set_button_directory(letter, dir_name)
        self.button_panel.save_bindings(self.config)
        self.config_manager.save()

        if self.image_viewer and not self.image_list.is_empty():
            if self.image_list.move_current_image_to_subdir(dir_name):
                self.load_current_image()
                self.message_manager.show(f"Moved to '{dir_name}'")
            else:
                self.message_manager.show("Failed to move image")
                logger.error(f"Failed to move image to '{dir_name}'")

    def _handle_viewing_mode_keydown(self, event) -> bool:
        """Handle key presses when in VIEWING mode"""
        key_map = {
            pygame.K_q: 'Q', pygame.K_w: 'W', pygame.K_e: 'E', pygame.K_r: 'R',
            pygame.K_t: 'T', pygame.K_y: 'Y', pygame.K_u: 'U', pygame.K_i: 'I',
            pygame.K_o: 'O', pygame.K_p: 'P', pygame.K_a: 'A', pygame.K_s: 'S',
            pygame.K_d: 'D', pygame.K_f: 'F', pygame.K_g: 'G', pygame.K_h: 'H',
            pygame.K_j: 'J', pygame.K_k: 'K', pygame.K_l: 'L', pygame.K_z: 'Z',
            pygame.K_x: 'X', pygame.K_c: 'C', pygame.K_v: 'V', pygame.K_b: 'B',
            pygame.K_n: 'N', pygame.K_m: 'M'
        }

        if event.key == pygame.K_ESCAPE:
            logger.info("Escape pressed, exiting")
            return False  # Signal to exit

        elif event.key == pygame.K_LEFT:
            new_image = self.image_list.previous_image()
            if new_image:
                self.load_current_image()

        elif event.key == pygame.K_RIGHT:
            new_image = self.image_list.next_image()
            if new_image:
                self.load_current_image()

        elif event.key == pygame.K_BACKSPACE:
            logger.info("Backspace pressed, moving image back")
            if self.image_list.move_current_image_back():
                self.load_current_image()
                self.message_manager.show("Moved back to current directory")
            else:
                self.message_manager.show("Image already in current directory")

        elif event.key in key_map:
            letter = key_map[event.key]
            logger.info(f"Key pressed: {letter}")
            directory = self.button_panel.get_button_directory(letter)

            if directory:
                if self.image_viewer and self.image_list.move_current_image_to_subdir(directory):
                    self.load_current_image()
                    self.message_manager.show(f"Moved to '{directory}'")
                elif self.image_list.is_empty():
                    self.message_manager.show("No images to move")
            else:
                # Switch to dialog mode
                self.current_mode = AppMode.DIALOG
                self.dialog.show(letter, self._on_dialog_complete)

        return True  # Continue running

    def _handle_viewing_mode_mousebutton(self, event) -> bool:
        """Handle mouse button presses when in VIEWING mode"""
        if event.button == 1:  # Left click
            letter = self.button_panel.handle_click(event.pos)
            if letter:
                directory = self.button_panel.get_button_directory(letter)

                if directory:
                    if self.image_viewer and self.image_list.move_current_image_to_subdir(directory):
                        self.load_current_image()
                        self.message_manager.show(f"Moved to '{directory}'")
                    elif self.image_list.is_empty():
                        self.message_manager.show("No images to move")
                else:
                    # Switch to dialog mode
                    self.current_mode = AppMode.DIALOG
                    self.dialog.show(letter, self._on_dialog_complete)

        elif event.button == 4:  # Scroll up
            if self.image_viewer:
                self.image_viewer.zoom(0.1, event.pos)

        elif event.button == 5:  # Scroll down
            if self.image_viewer:
                self.image_viewer.zoom(-0.1, event.pos)

        return True

    def _on_dialog_complete(self, letter: str, dir_name: str):
        """Callback when dialog completes"""
        self.handle_letter_action(letter, dir_name)
        self.current_mode = AppMode.VIEWING

    def _handle_dialog_mode_keydown(self, event) -> bool:
        """Handle key presses when in DIALOG mode"""
        # Delegate to dialog
        self.dialog.handle_keydown(event)

        # If dialog is no longer active, switch back to viewing mode
        if not self.dialog.is_active():
            self.current_mode = AppMode.VIEWING

        return True

    def _handle_dialog_mode_mousebutton(self, event) -> bool:
        """Handle mouse button presses when in DIALOG mode"""
        if event.button == 1:  # Left click
            self.dialog.handle_click(event.pos)

            # If dialog is no longer active, switch back to viewing mode
            if not self.dialog.is_active():
                self.current_mode = AppMode.VIEWING

        return True

    def _handle_dialog_mode_mousemotion(self, event) -> bool:
        """Handle mouse motion when in DIALOG mode"""
        # Dialog handles its own hover states, but we don't want button panel updates
        return True

    def run(self):
        """Main application loop with state machine"""
        logger.info("Starting main application loop")
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logger.info("Quit event received")
                    running = False
                    break

                # Delegate based on current mode
                if event.type == pygame.KEYDOWN:
                    if self.current_mode == AppMode.VIEWING:
                        running = self._handle_viewing_mode_keydown(event)
                    elif self.current_mode == AppMode.DIALOG:
                        self._handle_dialog_mode_keydown(event)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.current_mode == AppMode.VIEWING:
                        self._handle_viewing_mode_mousebutton(event)
                    elif self.current_mode == AppMode.DIALOG:
                        self._handle_dialog_mode_mousebutton(event)

                elif event.type == pygame.MOUSEMOTION:
                    if self.current_mode == AppMode.VIEWING and not self.dialog.is_active():
                        self.button_panel.update_hover(event.pos)
                    elif self.current_mode == AppMode.DIALOG:
                        # Optionally handle dialog hover effects here if needed
                        pass

            # Update components
            self.message_manager.update()

            # Draw everything
            self.screen.fill((0, 0, 0))

            if self.image_list.is_empty():
                text = self.font.render("No images found in the current directory",
                                       True, (255, 255, 255))
                text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(text, text_rect)
            elif self.image_viewer:
                self.image_viewer.draw()

            # Draw UI elements (only in viewing mode or always?)
            if not self.image_list.is_empty():
                counter_text = self.small_font.render(self.image_list.get_index_info(),
                                                     True, (255, 255, 255))
                counter_rect = counter_text.get_rect()
                counter_rect.topleft = (10, 10)
                bg_rect = counter_rect.inflate(20, 10)
                overlay = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, bg_rect)
                self.screen.blit(counter_text, counter_rect)

                backspace_text = self.small_font.render("BACKSPACE: Move image back to current directory",
                                                       True, (255, 255, 255))
                backspace_rect = backspace_text.get_rect()
                backspace_rect.bottomright = (self.screen_width - 10, self.screen_height - 10)
                self.screen.blit(backspace_text, backspace_rect)

            # Always draw button panel (it may be partially dimmed if dialog is active)
            self.button_panel.draw()

            # Draw dialog on top if active
            if self.dialog.is_active():
                self.dialog.draw()

            # Draw message on top of everything
            self.message_manager.draw()

            pygame.display.flip()
            self.clock.tick(60)

        # Cleanup
        self.button_panel.save_bindings(self.config)
        self.config_manager.save()
        logger.info("Application shutdown complete")
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = SortThemApp()
    app.run()
