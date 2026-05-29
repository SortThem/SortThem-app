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
        self.is_fullscreen = False

        # Start in windowed mode for development
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height),
            pygame.RESIZABLE
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

    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        was_fullscreen = pygame.display.is_fullscreen()

        if was_fullscreen:
            # Switch to windowed mode
            self.screen = pygame.display.set_mode(
                (self.screen_width, self.screen_height),
                pygame.RESIZABLE
            )
            logger.info("Switched to windowed mode")
        else:
            # Store windowed dimensions before going fullscreen
            if not hasattr(self, 'windowed_size'):
                self.windowed_size = (self.screen_width, self.screen_height)

            # Get fullscreen dimensions
            info = pygame.display.Info()
            fullscreen_width = info.current_w
            fullscreen_height = info.current_h

            # Switch to fullscreen
            self.screen = pygame.display.set_mode(
                (fullscreen_width, fullscreen_height),
                pygame.FULLSCREEN
            )

            # Update dimensions
            self.screen_width = fullscreen_width
            self.screen_height = fullscreen_height
            logger.info(f"Switched to fullscreen mode: {self.screen_width}x{self.screen_height}")

        # Update all components with new screen
        self._update_components_for_new_screen()

        # Resize existing image viewer instead of reloading
        if self.image_viewer:
            self.image_viewer.resize(self.screen)
        else:
            # Only reload if no viewer exists
            self.load_current_image()

        # Update button pressed state (may have changed due to image location)
        current_image = self.image_list.get_current_image()
        if current_image:
            self.button_panel.update_pressed_state(current_image, self.image_list.base_directory)

    def _update_components_for_new_screen(self):
        """Update all components after screen size change"""
        # Update button panel
        self.button_panel.screen = self.screen
        self.button_panel.screen_width, self.button_panel.screen_height = self.screen.get_size()
        self.button_panel.create_buttons()

        # Update dialog
        self.dialog.screen = self.screen

        # Update message manager
        self.message_manager.screen = self.screen


    def load_current_image(self):
        """Load the current image into the viewer"""
        current_image = self.image_list.get_current_image()
        if current_image and current_image.exists():
            # Create new image viewer
            self.image_viewer = ImageViewer(self.screen, str(current_image))
            self.button_panel.update_pressed_state(current_image, self.image_list.base_directory)
            self.update_window_title()
        else:
            self.image_viewer = None
            if not self.image_list.is_empty():
                logger.warning(f"Could not load image: {current_image}")
            self.update_window_title()

    def update_window_title(self):
        """Update window title with current image filename"""
        current_image = self.image_list.get_current_image()
        if current_image and not self.image_list.is_empty():
            filename = current_image.name
            title = f"SortThem! - get order in your image collection - {filename}"
        else:
            title = "SortThem! - get order in your image collection - No images"

        pygame.display.set_caption(title)
        logger.debug(f"Window title updated: {title}")

    def draw_help_text(self):
        """Draw help text at the top-left of the screen using multiple lines"""
        help_lines = [
            "ESC: Exit application",
            "F11: Toggle fullscreen mode",
            "BACKSPACE: Move current image back to root directory",
            "LEFT, RIGHT keys: Navigate between images",
        ]

        x_offset = 20
        y_offset = 10
        line_height = 24

        for line in help_lines:
            text = self.small_font.render(line, True, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.topleft = (x_offset, y_offset)

            # Add semi-transparent background
            bg_rect = text_rect.inflate(20, 6)
            overlay = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, bg_rect)

            self.screen.blit(text, text_rect)
            y_offset += line_height

    def draw_image_counter(self):
        """Draw image counter and filename at top-right corner"""
        if self.image_list.is_empty():
            return

        current_image = self.image_list.get_current_image()
        filename = current_image.name if current_image else ""

        # Truncate long filenames
        max_filename_len = 40
        if len(filename) > max_filename_len:
            filename = filename[:max_filename_len-3] + "..."

        info_text = f"{self.image_list.get_index_info()}  |  {filename}"
        info_surface = self.small_font.render(info_text, True, (255, 255, 255))
        info_rect = info_surface.get_rect()
        info_rect.topright = (self.screen_width - 20, 10)

        # Add semi-transparent background
        bg_rect = info_rect.inflate(20, 10)
        overlay = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, bg_rect)
        self.screen.blit(info_surface, info_rect)

    def draw_instruction_below_keyboard(self):
        """Draw instruction text below the keyboard"""
        instruction_text = "Click or press letter key to move image into assigned subdirectory"
        text = self.small_font.render(instruction_text, True, (200, 200, 200))
        text_rect = text.get_rect()
        text_rect.centerx = self.screen_width // 2
        text_rect.bottom = self.screen_height - 10

        # Add semi-transparent background
        bg_rect = text_rect.inflate(20, 8)
        overlay = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, bg_rect)

        self.screen.blit(text, text_rect)

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

        elif event.key == pygame.K_F11:
            logger.info("F11 pressed, toggling fullscreen")
            self.toggle_fullscreen()

        elif event.key == pygame.K_LEFT:
            new_image = self.image_list.previous_image()
            if new_image:
                self.load_current_image()
                self.update_window_title()

        elif event.key == pygame.K_RIGHT:
            new_image = self.image_list.next_image()
            if new_image:
                self.load_current_image()
                self.update_window_title()

        elif event.key == pygame.K_BACKSPACE:
            logger.info("Backspace pressed, moving image back")
            if self.image_list.move_current_image_back():
                self.load_current_image()
                self.update_window_title()
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
                    self.update_window_title()
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
                        self.update_window_title()
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
        self.update_window_title()
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

                # Handle window resize events (when in windowed mode)
                elif event.type == pygame.VIDEORESIZE:
                    if not pygame.display.is_fullscreen():
                        self.screen_width, self.screen_height = event.w, event.h
                        self.screen = pygame.display.set_mode(
                            (self.screen_width, self.screen_height),
                            pygame.RESIZABLE
                        )
                        self._update_components_for_new_screen()
                        self.load_current_image()
                        logger.info(f"Window resized to: {self.screen_width}x{self.screen_height}")

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

            # Draw image or "no images" message
            if self.image_list.is_empty():
                text = self.font.render("No images found in the current directory",
                                       True, (255, 255, 255))
                text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                self.screen.blit(text, text_rect)
            elif self.image_viewer:
                self.image_viewer.draw()

            # Draw UI elements
            self.draw_help_text()           # Help text at top-left
            self.draw_image_counter()       # Counter at top-right
            self.button_panel.draw()        # Keyboard at bottom

            # Draw instruction below keyboard
            self.draw_instruction_below_keyboard()

            # Draw message manager (temporary messages)
            self.message_manager.draw()

            # Draw dialog on top if active
            if self.dialog.is_active():
                self.dialog.draw()

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
