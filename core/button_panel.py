import pygame
import configparser
import os
from typing import Dict, Optional, Tuple
from ui.keyboard_button import KeyboardButton
from pathlib import Path
from utils.logger_setup import setup_logger

logger = setup_logger(__name__)


class ButtonPanel:
    """Manages letter buttons with directory bindings - positioned at bottom"""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.screen_width, self.screen_height = screen.get_size()
        self.buttons: Dict[str, KeyboardButton] = {}
        self.hovered_button = None
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 18)
        self.create_buttons()
        logger.info("Button panel initialized with QWERTY layout at bottom")

    def create_buttons(self):
        """Create letter buttons in QWERTY keyboard layout (3 rows) at bottom"""
        qwerty_rows = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['Z', 'X', 'C', 'V', 'B', 'N', 'M']
        ]

        # Calculate button size
        button_margin = 10
        bottom_margin = 20  # Margin from bottom of screen
        max_buttons_in_row = max(len(row) for row in qwerty_rows)
        available_width = self.screen_width - (button_margin * 2)

        button_size = min(
            (available_width - (button_margin * (max_buttons_in_row - 1))) // max_buttons_in_row,
            80  # Max button size
        )

        spacing = button_margin
        total_rows = len(qwerty_rows)
        total_buttons_height = (button_size * total_rows) + (spacing * (total_rows - 1))

        # Position at bottom
        start_y = self.screen_height - total_buttons_height - bottom_margin

        for row_idx, row in enumerate(qwerty_rows):
            row_width = len(row) * (button_size + spacing) - spacing
            start_x = (self.screen_width - row_width) // 2

            for col_idx, letter in enumerate(row):
                x = start_x + col_idx * (button_size + spacing)
                y = start_y + row_idx * (button_size + spacing)
                rect = pygame.Rect(x, y, button_size, button_size)
                self.buttons[letter] = KeyboardButton(letter, rect)

        logger.info(f"Created {len(self.buttons)} buttons at bottom (y={start_y})")

    def load_bindings(self, config: configparser.ConfigParser):
        """Load letter-directory bindings from config"""
        if config.has_section('KeyBindings'):
            loaded_count = 0
            for letter, button in self.buttons.items():
                if config.has_option('KeyBindings', letter):
                    directory = config.get('KeyBindings', letter)
                    if os.path.exists(directory):
                        button.set_directory(directory)
                        loaded_count += 1
            logger.info(f"Loaded {loaded_count} key bindings from config")

    def save_bindings(self, config: configparser.ConfigParser):
        """Save letter-directory bindings to config"""
        if not config.has_section('KeyBindings'):
            config.add_section('KeyBindings')

        for letter, button in self.buttons.items():
            if button.directory:
                config.set('KeyBindings', letter, button.directory)
            else:
                if config.has_option('KeyBindings', letter):
                    config.remove_option('KeyBindings', letter)

        logger.info("Saved key bindings to config")

    def get_button_at_pos(self, pos: Tuple[int, int]) -> Optional[KeyboardButton]:
        """Get button at mouse position"""
        for button in self.buttons.values():
            if button.rect.collidepoint(pos):
                return button
        return None

    def update_hover(self, pos: Tuple[int, int]):
        """Update hover state for buttons"""
        self.hovered_button = self.get_button_at_pos(pos)
        for button in self.buttons.values():
            button.is_hovered = (button == self.hovered_button)

    def handle_click(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle button click, return letter if clicked"""
        button = self.get_button_at_pos(pos)
        if button:
            logger.debug(f"Button '{button.letter}' clicked")
            return button.letter
        return None

    def set_button_directory(self, letter: str, directory: str):
        """Set directory for a button"""
        if letter in self.buttons:
            self.buttons[letter].set_directory(directory)

    def get_button_directory(self, letter: str) -> Optional[str]:
        """Get directory for a button"""
        if letter in self.buttons:
            return self.buttons[letter].directory
        return None

    def update_pressed_state(self, current_image_path: Optional[Path], base_directory: Path):
        """Update pressed state of buttons based on current image location"""
        if not current_image_path:
            for button in self.buttons.values():
                button.set_pressed(False)
            return

        try:
            # Get relative path from base directory
            relative_path = current_image_path.relative_to(base_directory)

            # Check if image is in a subdirectory
            if len(relative_path.parents) > 0 and str(relative_path.parent) != '.':
                current_subdir = str(relative_path.parent)

                # Find which button has this directory bound
                found = False
                for button in self.buttons.values():
                    if button.directory == current_subdir:
                        button.set_pressed(True)
                        found = True
                        logger.debug(f"Button '{button.letter}' pressed (image from '{current_subdir}')")
                    else:
                        button.set_pressed(False)

                if not found:
                    logger.debug(f"No button bound to directory '{current_subdir}'")
            else:
                # Image in root directory, no button pressed
                for button in self.buttons.values():
                    button.set_pressed(False)
        except ValueError:
            # Path not relative to base directory
            for button in self.buttons.values():
                button.set_pressed(False)

    def draw(self):
        """Draw all buttons"""
        for button in self.buttons.values():
            button.draw(self.screen, self.font, self.small_font)
