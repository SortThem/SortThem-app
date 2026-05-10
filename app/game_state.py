from enum import Enum

class GameState(Enum):
    """Application states"""
    RUNNING = "running"
    INPUT_ACTIVE = "input_active"
    EXITING = "exiting"

class EventType(Enum):
    """Custom event types"""
    IMAGE_CHANGED = "image_changed"
    IMAGE_MOVED = "image_moved"
    BINDING_CHANGED = "binding_changed"
    ZOOM_CHANGED = "zoom_changed"
    VIEW_RESET = "view_reset"
    MESSAGE_SHOW = "message_show"
