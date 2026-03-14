"""
Time Machine - Complete terminal activity tracker
"""

from .core import TimeMachine, get_timemachine
from .commands import (
    time_travel, show_timeline, whats_if, add_thought, record_moment,
    show_file_history, compare_files, restore_file, track_file_changes
)

__all__ = [
    'TimeMachine', 'get_timemachine',
    'time_travel', 'show_timeline', 'whats_if', 'add_thought', 'record_moment',
    'show_file_history', 'compare_files', 'restore_file', 'track_file_changes'
]