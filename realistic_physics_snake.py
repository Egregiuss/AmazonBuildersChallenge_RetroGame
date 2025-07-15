import arcade
import pymunk
import random
import math
import numpy as np
from opensimplex import OpenSimplex
from perlin_noise import PerlinNoise
from scipy.interpolate import interp1d
import json
import os
# Removed complex image processing imports

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
GRID_SIZE = 35
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = (SCREEN_HEIGHT - 150) // GRID_SIZE
HIGH_SCORE_FILE = "snake_highscore.json"

def load_high_score():
    try:
        if os.path.exists(HIGH_SCORE_FILE):
            with open(HIGH_SCORE_FILE, 'r') as f:
                return json.load(f).get('high_score', 0)
    except:
        pass
    return 0

def save_high_score(score):
    try:
        with open(HIGH_SCORE_FILE, 'w') as f:
            json.dump({'high_score': score}, f)
    except:
        pass

class RealisticSnake:
    def __init__(self, start_pos):
        self.segments = [start_pos]
        self.direction = (1, 0)
        self.target_direction = (1, 0)
        self.physics_segments = []
        self.segment_angles = [0]
        self.breathing_phase = 0
        self.eye_blink = 0
        self.tongue_phase = 0
        self.skin_noise = OpenSimplex(seed=42)
        self.movement_smoothing = 0.8
        
        # Physics properties
        self.segment_mass = 1.0
        self.joint_stiffness = 0.9
        self.skin_elasticity = 0.1
        
    def update_physics(self, dt):
        # Only update animation phases, not positions
        self.breathing_phase += dt * 3
        self.eye_blink += dt * 2
        self.tongue_phase += dt * 5
        
        # Update direction for visuals only
        self.direction = self.target_direction
    
    def move(self):
        head = self.segments[0]
        new_head = (head[0] + self.target_direction[0], head[1] + self.target_direction[1])
        self.segments.insert(0, new_head)
        self.segment_angles.insert(0, math.atan2(self.target_direction[1], self.target_direction[0]))
        
    def grow(self):
        # Add new segment at tail
        tail = self.segments[-1]
        self.segments.append(tail)
        self.segment_angles.append(self.segment_angles[-1])
        
    def shrink(self):
        if len(self.segments) > 1:
            self.segments.pop()
            self.segment_angles.pop()
    
    def set_direction(self, direction):
        # Prevent 180-degree turns
        if (direction[0] * -1, direction[1] * -1) != self.target_direction:
            self.target_direction = direction
    
    def draw_realistic(self, shake_x=0, shake_y=0):
        for i, (x, y) in enumerate(self.segments):
            screen_x = x * GRID_SIZE + GRID_SIZE//2 + shake_x
            screen_y = y * GRID_SIZE + GRID_SIZE//2 + shake_y
            
            if i == 0:  # Head - ultra realistic
                self.draw_head(screen_x, screen_y)
            else:  # Body segments with physics
                self.draw_body_segment(screen_x, screen_y, i)
    
    def draw_head(self, x, y):
        # Simple breathing effect
        breath_scale = 1 + 0.03 * math.sin(self.breathing_phase)
        head_size = int(GRID_SIZE * 0.8 * breath_scale)
        
        # Head shadow
        arcade.draw_circle_filled(x + 3, y - 3, head_size + 2, (0, 60, 0))
        
        # Main head - bright green
        arcade.draw_circle_filled(x, y, head_size, (50, 200, 50))
        arcade.draw_circle_filled(x, y, head_size - 4, (80, 255, 80))
        
        # Simple scale pattern
        for i in range(8):
            angle = i * math.pi / 4
            scale_x = x + (head_size - 8) * math.cos(angle)
            scale_y = y + (head_size - 8) * math.sin(angle)
            arcade.draw_circle_filled(scale_x, scale_y, 3, (100, 255, 100))
        
        # Clean eyes
        self.draw_simple_eyes(x, y)
        
        # Simple tongue
        self.draw_simple_tongue(x, y)
    
    def draw_simple_eyes(self, x, y):
        # Simple, clean eyes
        blink = max(0.2, math.sin(self.eye_blink * 0.1)) if random.random() < 0.02 else 1
        
        # Left eye
        arcade.draw_circle_filled(x - 8, y + 6, 5, (255, 255, 255))
        arcade.draw_circle_filled(x - 8, y + 6, int(3 * blink), (0, 0, 0))
        if blink > 0.5:
            arcade.draw_circle_filled(x - 7, y + 7, 1, (255, 255, 255))
        
        # Right eye
        arcade.draw_circle_filled(x + 8, y + 6, 5, (255, 255, 255))
        arcade.draw_circle_filled(x + 8, y + 6, int(3 * blink), (0, 0, 0))
        if blink > 0.5:
            arcade.draw_circle_filled(x + 9, y + 7, 1, (255, 255, 255))
    
    def draw_simple_tongue(self, x, y):
        # Simple animated tongue
        tongue_length = 12 + 6 * math.sin(self.tongue_phase)
        direction_angle = math.atan2(self.direction[1], self.direction[0])
        
        base_x = x + 12 * math.cos(direction_angle)
        base_y = y + 12 * math.sin(direction_angle)
        tip_x = base_x + tongue_length * math.cos(direction_angle)
        tip_y = base_y + tongue_length * math.sin(direction_angle)
        
        # Tongue body
        arcade.draw_line(base_x, base_y, tip_x, tip_y, (255, 0, 0), 3)
        
        # Fork
        fork_size = 4
        arcade.draw_line(tip_x, tip_y, tip_x + fork_size * math.cos(direction_angle + 0.3), 
                        tip_y + fork_size * math.sin(direction_angle + 0.3), (255, 0, 0), 2)
        arcade.draw_line(tip_x, tip_y, tip_x + fork_size * math.cos(direction_angle - 0.3), 
                        tip_y + fork_size * math.sin(direction_angle - 0.3), (255, 0, 0), 2)
    
    def draw_body_segment(self, x, y, index):
        # Clean, simple body segments
        scale = max(0.4, 1 - index * 0.05)
        segment_size = int(GRID_SIZE * 0.7 * scale)
        
        # Subtle breathing
        breath_effect = 1 + 0.02 * math.sin(self.breathing_phase + index * 0.2)
        segment_size = int(segment_size * breath_effect)
        
        # Shadow
        arcade.draw_circle_filled(x + 2, y - 2, segment_size + 2, (0, 80, 0))
        
        # Main body - gradient green
        body_green = int(120 + 80 * scale)
        arcade.draw_circle_filled(x, y, segment_size, (40, body_green, 40))
        arcade.draw_circle_filled(x, y, segment_size - 3, (60, body_green + 40, 60))
        
        # Simple scale pattern
        if index % 2 == 0:
            for i in range(6):
                angle = i * math.pi / 3
                scale_x = x + (segment_size - 6) * math.cos(angle)
                scale_y = y + (segment_size - 6) * math.sin(angle)
                arcade.draw_circle_filled(scale_x, scale_y, 2, (80, body_green + 60, 80))
        
        # Highlight
        arcade.draw_circle_filled(x - 2, y + 2, segment_size // 3, (120, 255, 120))

class ProceduralEnvironment:
    def __init__(self):
        self.terrain_noise = PerlinNoise(octaves=4, seed=123)
        self.grass_positions = []
        self.rock_positions = []
        self.time = 0
        
        # Generate environment within frame
        for _ in range(100):
            x = random.randint(30, SCREEN_WIDTH - 30)
            y = random.randint(30, SCREEN_HEIGHT - 180)
            if self.terrain_noise([x * 0.01, y * 0.01]) > 0.3:
                self.grass_positions.append((x, y, random.uniform(0.5, 2.0)))
            elif self.terrain_noise([x * 0.01, y * 0.01]) < -0.3:
                self.rock_positions.append((x, y, random.uniform(3, 8)))
    
    def update(self, dt):
        self.time += dt
    
    def draw(self):
        # Animated grass
        for x, y, scale in self.grass_positions:
            sway = 2 * math.sin(self.time * 2 + x * 0.01)
            grass_color = (20 + int(10 * math.sin(self.time + x * 0.1)), 
                          80 + int(20 * math.sin(self.time + y * 0.1)), 20)
            arcade.draw_line(x, y, x + sway, y + 8 * scale, grass_color, int(2 * scale))
        
        # Static rocks with shadows
        for x, y, size in self.rock_positions:
            arcade.draw_circle_filled(x + 2, y - 2, size + 1, (30, 30, 30))  # Shadow
            arcade.draw_circle_filled(x, y, size, (60, 60, 70))              # Rock
            arcade.draw_circle_filled(x - 1, y + 1, size - 2, (80, 80, 90))  # Highlight

class GameView(arcade.View):
    def __init__(self, speed):
        super().__init__()
        self.speed = speed
        self.snake = RealisticSnake((GRID_WIDTH//2, GRID_HEIGHT//2))
        self.environment = ProceduralEnvironment()
        self.food_pos = self.spawn_food()
        self.score = 0
        self.move_timer = 0
        self.move_delay = 1.0 / self.speed
        self.paused = False
        self.particles = []
        self.screen_shake = 0
        self.bonus_food = None
        self.bonus_timer = 0
        self.bonus_spawn_time = random.uniform(10, 20)
        
    def spawn_food(self):
        attempts = 0
        while attempts < 100:
            # Spawn within frame boundaries (avoid edges)
            pos = (random.randint(2, GRID_WIDTH-3), random.randint(2, GRID_HEIGHT-3))
            snake_positions = [(int(round(x)), int(round(y))) for x, y in self.snake.segments]
            if pos not in snake_positions:
                return pos
            attempts += 1
        # Fallback: find any empty spot within boundaries
        for x in range(2, GRID_WIDTH-2):
            for y in range(2, GRID_HEIGHT-2):
                pos = (x, y)
                snake_positions = [(int(round(x)), int(round(y))) for x, y in self.snake.segments]
                if pos not in snake_positions:
                    return pos
        return (5, 5)  # Safe fallback
    
    def on_draw(self):
        self.clear()
        
        # Screen shake
        shake_x = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        self.screen_shake = max(0, self.screen_shake - 1)
        
        # Draw beautiful ornate frame
        self.draw_ornate_frame()
        
        # Draw environment
        self.environment.draw()
        
        # Draw realistic snake
        self.snake.draw_realistic(shake_x, shake_y)
        
        # Enhanced food
        food_x = self.food_pos[0] * GRID_SIZE + GRID_SIZE//2 + shake_x
        food_y = self.food_pos[1] * GRID_SIZE + GRID_SIZE//2 + shake_y
        
        # Food with realistic apple texture
        arcade.draw_circle_filled(food_x, food_y, 15, (180, 20, 20))
        arcade.draw_circle_filled(food_x - 3, food_y + 3, 12, (220, 60, 60))
        arcade.draw_circle_filled(food_x - 5, food_y + 5, 6, (255, 150, 150))
        
        # Apple stem
        arcade.draw_line(food_x, food_y + 15, food_x, food_y + 20, (101, 67, 33), 3)
        
        # Bonus food (golden apple)
        if self.bonus_food:
            bonus_x = self.bonus_food[0] * GRID_SIZE + GRID_SIZE//2 + shake_x
            bonus_y = self.bonus_food[1] * GRID_SIZE + GRID_SIZE//2 + shake_y
            
            # Pulsing golden glow
            glow_size = 20 + 8 * math.sin(self.bonus_timer * 5)
            for r in range(int(glow_size), 10, -2):
                alpha = 100 - r * 3
                arcade.draw_circle_filled(bonus_x, bonus_y, r, (255, 215, 0))
            
            # Golden apple
            arcade.draw_circle_filled(bonus_x, bonus_y, 15, (255, 215, 0))
            arcade.draw_circle_filled(bonus_x - 3, bonus_y + 3, 12, (255, 255, 100))
            arcade.draw_circle_filled(bonus_x - 5, bonus_y + 5, 6, (255, 255, 200))
            
            # Golden stem
            arcade.draw_line(bonus_x, bonus_y + 15, bonus_x, bonus_y + 20, (184, 134, 11), 4)
            
            # Timer indicator
            time_left = max(0, 8 - (self.bonus_timer - self.bonus_spawn_time))
            arcade.draw_text(f"{time_left:.1f}", bonus_x - 10, bonus_y + 25, (255, 255, 255), 16)
        
        # Particles
        for particle in self.particles[:]:
            particle[0] += particle[2]
            particle[1] += particle[3]
            particle[4] -= 1
            if particle[4] <= 0:
                self.particles.remove(particle)
            else:
                arcade.draw_circle_filled(particle[0], particle[1], 3, (255, 215, 0))
        
        # UI background
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, SCREEN_HEIGHT-150, SCREEN_HEIGHT, (0, 0, 0))
        
        # Title bar at top
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, SCREEN_HEIGHT-40, SCREEN_HEIGHT, (0, 0, 0))
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, SCREEN_HEIGHT-45, SCREEN_HEIGHT-40, (50, 50, 50))
        arcade.draw_text("Q_SNAKE", SCREEN_WIDTH//2, SCREEN_HEIGHT-20, (255, 255, 255), 36, anchor_x="center", anchor_y="center")
        
        # Stats row below title
        high_score = load_high_score()
        
        # Left side stats
        arcade.draw_text(f"SCORE: {self.score}", 30, SCREEN_HEIGHT-90, (255, 215, 0), 32)
        arcade.draw_text(f"HIGH: {high_score}", 30, SCREEN_HEIGHT-125, (255, 255, 255), 24)
        
        # Center stats
        arcade.draw_text(f"LENGTH: {len(self.snake.segments)}", 350, SCREEN_HEIGHT-90, (0, 255, 255), 28)
        
        # Right side status
        if self.bonus_food:
            arcade.draw_text("BONUS ACTIVE!", 650, SCREEN_HEIGHT-90, (255, 215, 0), 26)
        
        # Small pause indicator when paused
        if self.paused:
            # Semi-transparent overlay at top
            arcade.draw_lrbt_rectangle_filled(SCREEN_WIDTH//2 - 100, SCREEN_WIDTH//2 + 100, 
                                           SCREEN_HEIGHT-200, SCREEN_HEIGHT-150, (0, 0, 0, 180))
            arcade.draw_lrbt_rectangle_outline(SCREEN_WIDTH//2 - 100, SCREEN_WIDTH//2 + 100, 
                                            SCREEN_HEIGHT-200, SCREEN_HEIGHT-150, (255, 255, 0), 2)
            arcade.draw_text("PAUSED", SCREEN_WIDTH//2, SCREEN_HEIGHT-175, (255, 255, 0), 24, anchor_x="center", anchor_y="center")
    
    def draw_ornate_frame(self):
        frame_width = 25
        
        # Outer frame background
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT-150, (40, 30, 20))
        
        # Multi-layer frame with gradient
        for i in range(frame_width):
            progress = i / frame_width
            gold = int(255 * (1 - progress * 0.6))
            brown = int(139 * (1 - progress * 0.4))
            frame_color = (gold, int(gold * 0.8), brown)
            
            # Frame borders
            arcade.draw_lrbt_rectangle_filled(i, SCREEN_WIDTH-i, SCREEN_HEIGHT-150-i-1, SCREEN_HEIGHT-150-i, frame_color)
            arcade.draw_lrbt_rectangle_filled(i, SCREEN_WIDTH-i, i, i+1, frame_color)
            arcade.draw_lrbt_rectangle_filled(i, i+1, i, SCREEN_HEIGHT-150-i, frame_color)
            arcade.draw_lrbt_rectangle_filled(SCREEN_WIDTH-i-1, SCREEN_WIDTH-i, i, SCREEN_HEIGHT-150-i, frame_color)
        
        # Inner highlight
        arcade.draw_lrbt_rectangle_outline(23, SCREEN_WIDTH-23, 23, SCREEN_HEIGHT-173, (255, 255, 200), 2)
        
        # Corner ornaments
        for corner_x, corner_y in [(30, 30), (SCREEN_WIDTH-30, 30), (30, SCREEN_HEIGHT-180), (SCREEN_WIDTH-30, SCREEN_HEIGHT-180)]:
            for i in range(4):
                arcade.draw_circle_filled(corner_x, corner_y, 12-i*2, (255, 215, 0))
        
        # Decorative triangles
        decoration_color = (200, 150, 50)
        for x in range(80, SCREEN_WIDTH-80, 60):
            arcade.draw_triangle_filled(x, SCREEN_HEIGHT-160, x-8, SCREEN_HEIGHT-145, x+8, SCREEN_HEIGHT-145, decoration_color)
            arcade.draw_triangle_filled(x, 10, x-8, 25, x+8, 25, decoration_color)
    
    def on_update(self, delta_time):
        if not self.paused:
            # Disable physics updates to prevent position drift
            # self.snake.update_physics(delta_time)
            self.environment.update(delta_time)
            self.move_timer += delta_time
            self.bonus_timer += delta_time
            
            # Spawn bonus food
            if not self.bonus_food and self.bonus_timer >= self.bonus_spawn_time:
                attempts = 0
                while attempts < 50:
                    pos = (random.randint(2, GRID_WIDTH-3), random.randint(2, GRID_HEIGHT-3))
                    snake_positions = [(int(round(x)), int(round(y))) for x, y in self.snake.segments]
                    if pos not in snake_positions and pos != self.food_pos:
                        self.bonus_food = pos
                        break
                    attempts += 1
            
            # Remove bonus food after 8 seconds
            if self.bonus_food and self.bonus_timer >= self.bonus_spawn_time + 8:
                self.bonus_food = None
                self.bonus_spawn_time = self.bonus_timer + random.uniform(15, 25)
            
            if self.move_timer >= self.move_delay:
                self.move_timer = 0
                
                # Use integer positions for collision detection
                head_x, head_y = int(self.snake.segments[0][0]), int(self.snake.segments[0][1])
                new_head = (head_x + self.snake.target_direction[0], head_y + self.snake.target_direction[1])
                
                # Convert snake body to integer positions
                snake_body_positions = [(int(x), int(y)) for x, y in self.snake.segments]
                
                # Check collision - adjusted top boundary
                if (new_head[0] < 1 or new_head[0] >= GRID_WIDTH-1 or 
                    new_head[1] < 1 or new_head[1] > GRID_HEIGHT-2 or 
                    new_head in snake_body_positions):
                    game_over_view = GameOverView(self.score, len(self.snake.segments))
                    self.window.show_view(game_over_view)
                    return
                
                # Move snake with integer positions
                self.snake.segments.insert(0, new_head)
                self.snake.segment_angles.insert(0, math.atan2(self.snake.target_direction[1], self.snake.target_direction[0]))
                
                head_grid_pos = new_head
                
                # Check regular food collision
                if head_grid_pos == self.food_pos:
                    self.snake.grow()
                    self.score += 10
                    self.screen_shake = 5
                    
                    # Particle explosion
                    food_x = self.food_pos[0] * GRID_SIZE + GRID_SIZE//2
                    food_y = self.food_pos[1] * GRID_SIZE + GRID_SIZE//2
                    for _ in range(15):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2, 6)
                        self.particles.append([food_x, food_y, 
                                             speed * math.cos(angle), speed * math.sin(angle), 30])
                    
                    self.food_pos = self.spawn_food()
                    print(f"Food eaten! New food at {self.food_pos}, Score: {self.score}")
                
                # Check bonus food collision
                elif self.bonus_food and head_grid_pos == self.bonus_food:
                    self.snake.grow()
                    self.snake.grow()  # Double growth for bonus
                    self.score += 50
                    self.screen_shake = 10
                    
                    # Golden particle explosion
                    bonus_x = self.bonus_food[0] * GRID_SIZE + GRID_SIZE//2
                    bonus_y = self.bonus_food[1] * GRID_SIZE + GRID_SIZE//2
                    for _ in range(25):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(3, 8)
                        self.particles.append([bonus_x, bonus_y, 
                                             speed * math.cos(angle), speed * math.sin(angle), 40])
                    
                    self.bonus_food = None
                    self.bonus_spawn_time = self.bonus_timer + random.uniform(15, 25)
                    print(f"BONUS FOOD! +50 points, Score: {self.score}")
                
                # Remove tail if no food eaten
                if head_grid_pos != self.food_pos and (not self.bonus_food or head_grid_pos != self.bonus_food):
                    self.snake.segments.pop()
                    self.snake.segment_angles.pop()
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.paused = not self.paused
        elif not self.paused:
            if key == arcade.key.UP:
                self.snake.set_direction((0, 1))
            elif key == arcade.key.DOWN:
                self.snake.set_direction((0, -1))
            elif key == arcade.key.LEFT:
                self.snake.set_direction((-1, 0))
            elif key == arcade.key.RIGHT:
                self.snake.set_direction((1, 0))

class GameOverView(arcade.View):
    def __init__(self, score, length):
        super().__init__()
        self.score = score
        self.length = length
        self.high_score = load_high_score()
        self.is_new_high_score = score > self.high_score
        if self.is_new_high_score:
            save_high_score(score)
            self.high_score = score
        self.messages = [
            "Oops! Your snake got a little too excited! 🐍💥",
            "Well, that escalated quickly! Snake.exe has stopped working 😵",
            "Your snake just discovered it's not actually immortal! 🪦",
            "Congratulations! You've mastered the art of snake self-destruction! 🎭",
            "Plot twist: The wall was actually a mirror! 🪞",
            "Your snake tried to eat itself... again. Classic mistake! 🤦‍♂️",
            "Breaking news: Local snake forgets how walls work! 📰",
            "Achievement unlocked: Professional Wall Hugger! 🏆",
            "Your snake just rage-quit life! Try anger management next time 😤",
            "Error 404: Snake survival skills not found! 🔍"
        ]
        self.funny_message = random.choice(self.messages)
        self.glow_phase = 0
    
    def on_draw(self):
        self.clear()
        self.glow_phase += 0.1
        
        # Dramatic background
        for i in range(0, SCREEN_HEIGHT, 20):
            intensity = int(20 + 15 * math.sin(i * 0.05 + self.glow_phase))
            arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, i, i+20, (intensity, 0, 0))
        
        # Game Over title with glow
        glow_offset = int(10 * math.sin(self.glow_phase))
        for offset in range(8, 0, -1):
            arcade.draw_text("GAME OVER", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150 + offset, 
                           (255-offset*20, 0, 0), 72, anchor_x="center")
        arcade.draw_text("GAME OVER", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150, 
                        (255, min(255, 100 + glow_offset), min(255, 100 + glow_offset)), 72, anchor_x="center")
        
        # Funny message with more space
        arcade.draw_text(self.funny_message, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80, 
                        (255, 255, 150), 24, anchor_x="center")
        
        # Stats with better spacing
        stats_y = SCREEN_HEIGHT//2
        if self.is_new_high_score:
            arcade.draw_text("🎉 NEW HIGH SCORE! 🎉", SCREEN_WIDTH//2, stats_y, 
                            (255, 215, 0), 32, anchor_x="center")
            stats_y -= 50
        
        arcade.draw_text(f"Final Score: {self.score}", SCREEN_WIDTH//2, stats_y, 
                        (255, 215, 0), 28, anchor_x="center")
        arcade.draw_text(f"High Score: {self.high_score}", SCREEN_WIDTH//2, stats_y - 40, 
                        (255, 255, 255), 24, anchor_x="center")
        arcade.draw_text(f"Snake Length: {self.length}", SCREEN_WIDTH//2, stats_y - 80, 
                        (0, 255, 255), 24, anchor_x="center")
        
        # Instructions with better spacing
        pulse = int(50 + 50 * math.sin(self.glow_phase * 2))
        arcade.draw_text("Press SPACE to try again", SCREEN_WIDTH//2, stats_y - 140, 
                        (min(255, 100 + pulse), 255, min(255, 100 + pulse)), 22, anchor_x="center")
        arcade.draw_text("Press ESC for menu", SCREEN_WIDTH//2, stats_y - 180, 
                        (200, 200, 200), 20, anchor_x="center")
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            game_view = GameView(8)
            self.window.show_view(game_view)
        elif key == arcade.key.ESCAPE:
            menu_view = MenuView()
            self.window.show_view(menu_view)

class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.difficulty = 1  # 0=Easy, 1=Normal, 2=Hard, 3=Insane
        self.difficulties = [
            {"name": "EASY", "speed": 5, "color": (0, 255, 0)},
            {"name": "NORMAL", "speed": 8, "color": (255, 255, 0)},
            {"name": "HARD", "speed": 12, "color": (255, 165, 0)},
            {"name": "INSANE", "speed": 16, "color": (255, 0, 0)}
        ]
        self.glow_phase = 0
        self.high_score = load_high_score()
    
    def on_draw(self):
        self.clear()
        self.glow_phase += 0.05
        
        # Background gradient
        for y in range(0, SCREEN_HEIGHT, 10):
            color_val = int(20 + 10 * math.sin(y * 0.01 + self.glow_phase))
            arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, y, y+10, (0, color_val, color_val//2))
        
        # Title with glow effect
        title_y = SCREEN_HEIGHT - 150
        for offset in range(5, 0, -1):
            arcade.draw_text("Q_SNAKE", SCREEN_WIDTH//2, title_y + offset, 
                           (200-offset*20, 150-offset*20, 0), 72, anchor_x="center")
        arcade.draw_text("Q_SNAKE", SCREEN_WIDTH//2, title_y, 
                        (255, 215, 0), 72, anchor_x="center")
        
        # Subtitle
        arcade.draw_text("THE ULTIMATE SNAKE EXPERIENCE", SCREEN_WIDTH//2, title_y - 60, 
                        (200, 200, 200), 24, anchor_x="center")
        
        # Difficulty selection header
        arcade.draw_text("SELECT DIFFICULTY", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20, 
                        (255, 255, 255), 36, anchor_x="center")
        
        # Display difficulties in a clean layout
        for i, diff in enumerate(self.difficulties):
            y_pos = SCREEN_HEIGHT//2 - 20 - i * 60  # Moved up for more space
            
            # Background for selected difficulty
            if i == self.difficulty:
                # Draw selection box
                arcade.draw_lrbt_rectangle_filled(SCREEN_WIDTH//2 - 180, SCREEN_WIDTH//2 + 180, 
                                               y_pos - 20, y_pos + 20, (30, 30, 30))
            
            # Highlight selected difficulty
            if i == self.difficulty:
                glow = int(30 + 30 * math.sin(self.glow_phase * 3))
                r = min(255, diff['color'][0] + glow)
                g = min(255, diff['color'][1] + glow)
                b = min(255, diff['color'][2] + glow)
                
                # Name on left side
                arcade.draw_text(diff['name'], SCREEN_WIDTH//2 - 120, y_pos, 
                               (r, g, b), 32, anchor_y="center")
                               
                # Speed on right side
                arcade.draw_text(f"Speed: {diff['speed']}", SCREEN_WIDTH//2 + 60, y_pos, 
                               (255, 255, 255), 24, anchor_y="center")
            else:
                # Unselected options
                arcade.draw_text(diff['name'], SCREEN_WIDTH//2 - 120, y_pos, 
                               diff['color'], 28, anchor_y="center")
                arcade.draw_text(f"Speed: {diff['speed']}", SCREEN_WIDTH//2 + 60, y_pos, 
                               (180, 180, 180), 20, anchor_y="center")
        
        # High Score section with box - moved down to avoid overlap
        score_y = SCREEN_HEIGHT//2 - 300
        arcade.draw_lrbt_rectangle_filled(SCREEN_WIDTH//2 - 150, SCREEN_WIDTH//2 + 150, 
                                       score_y - 25, score_y + 25, (30, 30, 30))
        arcade.draw_lrbt_rectangle_outline(SCREEN_WIDTH//2 - 150, SCREEN_WIDTH//2 + 150, 
                                        score_y - 25, score_y + 25, (255, 215, 0), 2)
        arcade.draw_text(f"HIGH SCORE: {self.high_score}", SCREEN_WIDTH//2, score_y, 
                        (255, 215, 0), 32, anchor_x="center", anchor_y="center")
        
        # Instructions with better spacing and visual separation
        arcade.draw_text("↑↓ ARROWS: Change Difficulty", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 370, 
                        (200, 200, 200), 22, anchor_x="center")
        
        # Start prompt with pulse effect
        pulse = int(40 * math.sin(self.glow_phase * 2))
        start_color = (min(255, 150 + pulse), 255, min(255, 150 + pulse))
        arcade.draw_text("PRESS SPACE TO START", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 420, 
                        start_color, 28, anchor_x="center")
    
    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            selected_speed = self.difficulties[self.difficulty]["speed"]
            game_view = GameView(selected_speed)
            self.window.show_view(game_view)
        elif key == arcade.key.UP:
            self.difficulty = (self.difficulty - 1) % len(self.difficulties)
        elif key == arcade.key.DOWN:
            self.difficulty = (self.difficulty + 1) % len(self.difficulties)

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Q_Snake")
    window.center_window()  # Center on screen
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()

if __name__ == "__main__":
    main()