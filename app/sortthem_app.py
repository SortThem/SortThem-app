import pygame
import sys
from pathlib import Path
from typing import Optional

from core.image_list import ImageList
from core.image_viewer import ImageViewer
from core.button_panel import ButtonPanel
from ui.name_input_dialog import NameInputDialog
from ui.message_manager import MessageManager
from utils.config_manager import ConfigManager
from utils.logger_setup import setup_logger
from app.game_state import GameState

logger = setup_logger(__name__)


class SortThemApp:
    """Main application class"""

    def __init__(self):
        logger.info("Starting SortThemApp initialization")
        pygame.init()

        # Setup display
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h

        # ~ self.screen = pygame.display.set_mode(
            # ~ (self.screen_width, self.screen_height),
            # ~ pygame.FULLSCREEN
        # ~ )

        # set_mode without flags creates a windowed display by default
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height))

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
        self.state = GameState.RUNNING
        self.clock = pygame.time.Clock()

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

    def run(self):
        """Main application loop"""
        logger.info("Starting main application loop")
        running = True

        key_map = {
            pygame.K_q: 'Q', pygame.K_w: 'W', pygame.K_e: 'E', pygame.K_r: 'R',
            pygame.K_t: 'T', pygame.K_y: 'Y', pygame.K_u: 'U', pygame.K_i: 'I',
            pygame.K_o: 'O', pygame.K_p: 'P', pygame.K_a: 'A', pygame.K_s: 'S',
            pygame.K_d: 'D', pygame.K_f: 'F', pygame.K_g: 'G', pygame.K_h: 'H',
            pygame.K_j: 'J', pygame.K_k: 'K', pygame.K_l: 'L', pygame.K_z: 'Z',
            pygame.K_x: 'X', pygame.K_c: 'C', pygame.K_v: 'V', pygame.K_b: 'B',
            pygame.K_n: 'N', pygame.K_m: 'M'
        }

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    logger.info("Quit event received")
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if self.dialog.is_active():
                        self.dialog.handle_keydown(event)
                    else:
                        if event.key == pygame.K_ESCAPE:
                            logger.info("Escape pressed, exiting")
                            running = False
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
                                self.state = GameState.INPUT_ACTIVE
                                self.dialog.show(letter, self.handle_letter_action)

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if self.dialog.is_active():
                            self.dialog.handle_click(event.pos)
                        else:
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
                                    self.state = GameState.INPUT_ACTIVE
                                    self.dialog.show(letter, self.handle_letter_action)

                    elif event.button == 4:
                        if self.image_viewer and not self.dialog.is_active():
                            self.image_viewer.zoom(0.1, event.pos)

                    elif event.button == 5:
                        if self.image_viewer and not self.dialog.is_active():
                            self.image_viewer.zoom(-0.1, event.pos)

                elif event.type == pygame.MOUSEMOTION:
                    if not self.dialog.is_active():
                        self.button_panel.update_hover(event.pos)

            # Update state
            if not self.dialog.is_active() and self.state == GameState.INPUT_ACTIVE:
                self.state = GameState.RUNNING

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

            self.button_panel.draw()
            self.message_manager.draw()
            self.dialog.draw()

            pygame.display.flip()
            self.clock.tick(60)



        self.button_panel.save_bindings(self.config)
        self.config_manager.save()
        logger.info("Application shutdown complete")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    app = SortThemApp()
    app.run()
