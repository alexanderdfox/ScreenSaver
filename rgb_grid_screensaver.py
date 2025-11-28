#!/usr/bin/env python3
"""
RGB Grid Screensaver - Python Pygame Version
Displays a grid that fills with random RGB colors, with MIDI note sounds for each color.
"""

import pygame
import random
import math
import numpy as np
from typing import Optional, Tuple, List, Dict

class RGBGridScreensaver:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        
        # Get screen dimensions
        self.screen_info = pygame.display.Info()
        self.screen_width = self.screen_info.current_w
        self.screen_height = self.screen_info.current_h
        
        # Set up display
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("RGB Grid Screensaver")
        pygame.mouse.set_visible(False)
        
        # Grid setup
        self.grid_cols = 0
        self.grid_rows = 0
        self.grid_data: List[Optional[Tuple[int, int, int]]] = []
        self.grid_index = 0
        # 120 BPM = 120 beats per minute = 2 beats per second = 500ms per beat
        self.update_interval = 500  # milliseconds
        
        # Track previous colors for each cell
        self.previous_cell_colors: List[Optional[str]] = []
        
        # Color to MIDI note mapping for static colors
        self.color_to_midi_map: Dict[str, int] = {
            '#000000': 36,  # C2 - Black
            '#0a0a0a': 38,  # D2 - Very dark gray
            '#1a1a1a': 40,  # E2 - Dark gray
            '#ffffff': 60   # C4 - White
        }
        
        # Audio setup
        self.current_sound: Optional[pygame.mixer.Sound] = None
        
        # Font setup
        self.fonts = {}
        self._init_fonts()
        
        # Initialize grid
        self.update_grid_size()
        
        # Clock for timing
        self.clock = pygame.time.Clock()
        self.last_update = 0
        
    def _init_fonts(self):
        """Initialize fonts for different cell sizes"""
        try:
            # Try to use a monospace font
            self.fonts['large'] = pygame.font.Font(pygame.font.get_default_font(), 12)
            self.fonts['medium'] = pygame.font.Font(pygame.font.get_default_font(), 10)
        except:
            # Fallback to default font
            self.fonts['large'] = pygame.font.Font(None, 12)
            self.fonts['medium'] = pygame.font.Font(None, 10)
    
    def midi_note_to_frequency(self, note: int) -> float:
        """Convert MIDI note number to frequency in Hz"""
        # A4 (MIDI note 69) = 440 Hz
        return 440 * (2 ** ((note - 69) / 12))
    
    def color_to_midi_note(self, hex_color: str = None, rgb: Optional[Tuple[int, int, int]] = None) -> int:
        """Convert color to MIDI note number"""
        # Check if it's a mapped static color
        if hex_color and hex_color.lower() in self.color_to_midi_map:
            return self.color_to_midi_map[hex_color.lower()]
        
        # For dynamic RGB colors, map based on RGB values
        if rgb:
            r, g, b = rgb
            # Red maps to lower notes, Green to middle, Blue to higher
            red_note = 36 + int((r / 255) * 12)      # C2-B2 (12 semitones)
            green_note = 48 + int((g / 255) * 12)   # C3-B3 (12 semitones)
            blue_note = 60 + int((b / 255) * 12)   # C4-B4 (12 semitones)
            
            # Return the average note, rounded to nearest integer
            avg_note = round((red_note + green_note + blue_note) / 3)
            # Clamp to valid MIDI range (36-96)
            return max(36, min(96, avg_note))
        
        # Default note
        return 60  # C4
    
    def generate_tone(self, frequency: float, duration: float = 0.2, sample_rate: int = 44100) -> pygame.mixer.Sound:
        """Generate a sine wave tone as a pygame Sound object"""
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2), dtype=np.int16)
        
        max_sample = 2**(16 - 1) - 1
        
        for i in range(frames):
            # Generate sine wave
            wave = math.sin(2 * math.pi * frequency * i / sample_rate)
            
            # Apply envelope (fade in/out)
            envelope = 1.0
            if i < sample_rate * 0.01:  # Fade in
                envelope = i / (sample_rate * 0.01)
            elif i > frames - sample_rate * 0.01:  # Fade out
                envelope = (frames - i) / (sample_rate * 0.01)
            
            sample = int(wave * max_sample * envelope * 0.3)  # 0.3 for volume
            arr[i][0] = sample  # Left channel
            arr[i][1] = sample  # Right channel
        
        return pygame.sndarray.make_sound(arr)
    
    def play_midi_note(self, note: int, velocity: int = 64, duration: float = 0.2):
        """Play a MIDI note using generated tone"""
        # Stop any currently playing sound
        if self.current_sound:
            self.current_sound.stop()
            self.current_sound = None
        
        # Convert MIDI note to frequency
        frequency = self.midi_note_to_frequency(note)
        
        # Adjust duration based on velocity (optional)
        # duration = duration * (velocity / 127)
        
        # Generate and play tone
        try:
            sound = self.generate_tone(frequency, duration)
            sound.play()
            self.current_sound = sound
        except Exception as e:
            print(f"Error playing sound: {e}")
    
    def update_grid_size(self):
        """Calculate optimal grid dimensions based on screen size"""
        width = self.screen_width
        height = self.screen_height
        
        # Calculate optimal cell size (minimum 20px, with 2px gap)
        min_cell_size = 20
        gap = 2
        
        # Start with a reasonable cell size
        target_cell_size = max(min_cell_size, min(width, height) / 30)
        
        # Calculate maximum columns and rows that fit
        self.grid_cols = int((width + gap) / (target_cell_size + gap))
        self.grid_rows = int((height + gap) / (target_cell_size + gap))
        
        # Ensure minimum dimensions
        self.grid_cols = max(10, self.grid_cols)
        self.grid_rows = max(10, self.grid_rows)
        
        # Recalculate cell size to fill screen exactly
        cell_width = (width - (self.grid_cols - 1) * gap) / self.grid_cols
        cell_height = (height - (self.grid_rows - 1) * gap) / self.grid_rows
        self.cell_size = min(cell_width, cell_height)
        
        # Resize grid data array if dimensions changed
        total_cells = self.grid_cols * self.grid_rows
        if len(self.grid_data) != total_cells:
            old_data = self.grid_data.copy()
            self.grid_data = [None] * total_cells
            
            # Copy old data if possible
            if old_data:
                min_cells = min(len(old_data), total_cells)
                for i in range(min_cells):
                    self.grid_data[i] = old_data[i]
            
            # Reset index if grid got smaller
            if self.grid_index >= total_cells:
                self.grid_index = total_cells
            
            # Initialize previous colors array
            self.previous_cell_colors = [None] * total_cells
    
    def generate_random_rgb(self) -> Tuple[int, int, int]:
        """Generate random RGB values (0-255 for each channel)"""
        return (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
    
    def rgb_to_hex(self, r: int, g: int, b: int) -> str:
        """Convert RGB to hex color string"""
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def update_grid(self):
        """Update grid with new random RGB color"""
        # Generate new random RGB value
        rgb_value = self.generate_random_rgb()
        
        # Play MIDI note for the newly added color
        hex_color = self.rgb_to_hex(*rgb_value)
        midi_note = self.color_to_midi_note(hex_color, rgb_value)
        velocity = int((rgb_value[0] + rgb_value[1] + rgb_value[2]) / 3 / 255 * 127)
        self.play_midi_note(midi_note, max(1, velocity), 0.2)
        
        total_cells = self.grid_cols * self.grid_rows
        
        # Update grid data
        if self.grid_index >= total_cells:
            # Grid is full, shift all values left
            for i in range(total_cells - 1):
                self.grid_data[i] = self.grid_data[i + 1]
            self.grid_data[total_cells - 1] = rgb_value
        else:
            self.grid_data[self.grid_index] = rgb_value
            self.grid_index += 1
    
    def get_text_color(self, rgb: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """Calculate text color (white or black based on brightness)"""
        r, g, b = rgb
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return (0, 0, 0) if brightness > 128 else (255, 255, 255)
    
    def draw_grid(self):
        """Draw the grid on the screen"""
        self.screen.fill((0, 0, 0))  # Black background
        
        gap = 2
        total_cells = self.grid_cols * self.grid_rows
        
        # Initialize previous colors array if needed
        if len(self.previous_cell_colors) != total_cells:
            self.previous_cell_colors = [None] * total_cells
        
        for i in range(total_cells):
            row = i // self.grid_cols
            col = i % self.grid_cols
            
            # Calculate cell position
            x = col * (self.cell_size + gap)
            y = row * (self.cell_size + gap)
            
            current_color = None
            
            if self.grid_data[i] is not None:
                rgb = self.grid_data[i]
                current_color = self.rgb_to_hex(*rgb)
                
                # Draw cell with RGB color
                cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, rgb, cell_rect)
                pygame.draw.rect(self.screen, rgb, cell_rect, 1)  # Border
                
                # Draw text if cell is large enough
                if self.cell_size > 15:
                    text_color = self.get_text_color(rgb)
                    
                    if self.cell_size > 40:
                        # Show RGB values
                        text = f"{rgb[0]},{rgb[1]},{rgb[2]}"
                        font = self.fonts['large']
                    elif self.cell_size > 25:
                        # Show hex code
                        text = current_color.upper()
                        font = self.fonts['medium']
                    else:
                        text = ""
                    
                    if text:
                        text_surface = font.render(text, True, text_color)
                        text_rect = text_surface.get_rect(center=(x + self.cell_size // 2, 
                                                                   y + self.cell_size // 2))
                        self.screen.blit(text_surface, text_rect)
            else:
                # Default background color
                default_bg = (10, 10, 10)
                default_border = (26, 26, 26)
                current_color = '#0a0a0a'
                
                cell_rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                pygame.draw.rect(self.screen, default_bg, cell_rect)
                pygame.draw.rect(self.screen, default_border, cell_rect, 1)
            
            # Update previous color
            self.previous_cell_colors[i] = current_color
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            current_time = pygame.time.get_ticks()
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    running = False
            
            # Update grid at intervals
            if current_time - self.last_update >= self.update_interval:
                self.update_grid()
                self.last_update = current_time
            
            # Draw grid
            self.draw_grid()
            
            # Control frame rate
            self.clock.tick(60)
        
        pygame.quit()


def main():
    """Main entry point"""
    screensaver = RGBGridScreensaver()
    screensaver.run()


if __name__ == "__main__":
    main()

