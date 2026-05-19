import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='PIL')
warnings.filterwarnings('ignore', category=RuntimeWarning, module='PIL')
warnings.filterwarnings('ignore', category=DeprecationWarning, module='PIL')

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import pygame
import sys
import random
import json
import math
from PIL import Image, ImageDraw, ImageFont

pygame.init()
pygame.mixer.init()
pygame.font.init()

WIDTH, HEIGHT = 900, 700
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("接球大挑战 - 终极豪华版 v3.0")
clock = pygame.time.Clock()
SCREEN_CENTER = (HALF_WIDTH, HALF_HEIGHT)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 80, 80)
GREEN = (80, 255, 120)
BLUE = (80, 150, 255)
GOLD = (255, 215, 0)
PURPLE = (180, 100, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PINK = (255, 105, 180)
DARK_BG = (15, 15, 35)
LIGHT_GRAY = (180, 180, 180)

# 扩展色彩系统 - 渐变色彩
GRADIENT_COLORS = {
    "sunset": [(255, 100, 100), (255, 150, 50), (255, 200, 100), (255, 100, 150)],
    "ocean": [(0, 150, 255), (0, 200, 255), (100, 220, 255), (0, 100, 200)],
    "forest": [(50, 200, 100), (100, 220, 80), (80, 180, 60), (40, 160, 80)],
    "neon": [(255, 0, 255), (0, 255, 255), (255, 255, 0), (255, 0, 128)],
    "candy": [(255, 182, 193), (255, 218, 185), (221, 160, 221), (176, 224, 230)],
    "fire": [(255, 69, 0), (255, 140, 0), (255, 215, 0), (220, 20, 60)],
    "cool": [(100, 149, 237), (72, 61, 139), (106, 90, 205), (123, 104, 238)],
    "warm": [(255, 160, 122), (255, 127, 80), (255, 99, 71), (255, 69, 0)],
    "gold": [(255, 215, 0), (255, 223, 0), (255, 236, 139), (218, 165, 32)]
}

# 主题色彩
THEME_COLORS = {
    "primary": (100, 150, 255),
    "secondary": (255, 100, 150),
    "accent": (100, 255, 200),
    "highlight": (255, 220, 100),
    "shadow": (30, 30, 60),
    "glow": (150, 200, 255, 100)
}

# 动态色彩函数
def get_rainbow_color(time_offset=0, speed=0.05):
    import math
    t = pygame.time.get_ticks() * speed + time_offset
    r = int(128 + 127 * math.sin(t))
    g = int(128 + 127 * math.sin(t + 2.094))
    b = int(128 + 127 * math.sin(t + 4.189))
    return (r, g, b)

def get_gradient_color(colors, progress):
    if len(colors) < 2:
        return colors[0] if colors else WHITE
    idx = int(progress * (len(colors) - 1))
    idx = min(idx, len(colors) - 2)
    local_progress = progress * (len(colors) - 1) - idx
    c1, c2 = colors[idx], colors[idx + 1]
    return tuple(int(c1[i] + (c2[i] - c1[i]) * local_progress) for i in range(3))

class ResourceCache:
    _fonts = {}
    _surfaces = {}
    _surface_metadata = {}
    _font_path = None
    _max_surfaces = 500
    _access_count = 0
    
    @classmethod
    def _find_font(cls):
        if cls._font_path is None:
            paths = [
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simsun.ttc',
                '/System/Library/Fonts/PingFang.ttc',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
            ]
            for p in paths:
                if os.path.exists(p):
                    cls._font_path = p
                    break
        return cls._font_path
    
    @classmethod
    def get_font(cls, size):
        if size not in cls._fonts:
            font_path = cls._find_font()
            if font_path:
                try:
                    cls._fonts[size] = pygame.font.Font(font_path, size)
                    print(f"Loaded font: {font_path} at size {size}")
                except Exception as e:
                    print(f"Failed to load font {font_path}: {e}, using system font")
                    cls._fonts[size] = pygame.font.SysFont(None, size)
            else:
                print(f"No font found, using system font at size {size}")
                cls._fonts[size] = pygame.font.SysFont(None, size)
        return cls._fonts[size]
    
    @classmethod
    def _cleanup_lru(cls, count=50):
        if len(cls._surfaces) <= cls._max_surfaces:
            return
        
        sorted_items = sorted(cls._surface_metadata.items(), key=lambda x: x[1]['access_time'])
        to_remove = [key for key, _ in sorted_items[:count]]
        
        for key in to_remove:
            del cls._surfaces[key]
            del cls._surface_metadata[key]
    
    @classmethod
    def get_text_surface(cls, text, size, color):
        if not text:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        
        key = (text, size, color)
        cls._access_count += 1
        
        if key not in cls._surfaces:
            cls._cleanup_lru()
            try:
                font = cls.get_font(size)
                surface = font.render(text, True, color)
                cls._surfaces[key] = surface
                cls._surface_metadata[key] = {
                    'access_time': cls._access_count,
                    'size_bytes': surface.get_width() * surface.get_height() * 4
                }
            except Exception as e:
                print(f"Error creating text surface for '{text}': {e}")
                surf = pygame.Surface((100, 30), pygame.SRCALPHA)
                cls._surfaces[key] = surf
                cls._surface_metadata[key] = {
                    'access_time': cls._access_count,
                    'size_bytes': 100 * 30 * 4
                }
        else:
            cls._surface_metadata[key]['access_time'] = cls._access_count
        
        return cls._surfaces[key]
    
    @classmethod
    def clear_cache(cls):
        cls._surfaces.clear()
        cls._surface_metadata.clear()
    
    @classmethod
    def get_cache_stats(cls):
        total_bytes = sum(m['size_bytes'] for m in cls._surface_metadata.values())
        return {
            'num_surfaces': len(cls._surfaces),
            'total_size_bytes': total_bytes,
            'total_size_mb': total_bytes / (1024 * 1024)
        }

class ParticlePool:
    def __init__(self, max_size=500, max_active=300):
        self.pool = []
        self.active = []
        self.max_size = max_size
        self.max_active = max_active
        for _ in range(max_size):
            self.pool.append(self._create_particle())
    
    def _create_particle(self):
        return {
            'x': 0, 'y': 0, 'vx': 0, 'vy': 0, 'life': 0, 'color': WHITE,
            'radius': 3, 'active': False, 'type': 'normal',
            'rotation': 0, 'rotation_speed': 0, 'scale': 1.0,
            'trail': [], 'glow': False, 'spark': False
        }
    
    def spawn(self, x, y, color, count=8, ptype='normal'):
        for _ in range(count):
            if self.pool and len(self.active) < self.max_active:
                p = self.pool.pop()
                p['x'] = x
                p['y'] = y
                p['vx'] = random.uniform(-5, 5)
                p['vy'] = random.uniform(-6, 0)
                p['life'] = random.randint(30, 50)
                p['color'] = color
                p['radius'] = random.uniform(2, 5)
                p['active'] = True
                p['type'] = ptype
                p['rotation'] = random.uniform(0, 360)
                p['rotation_speed'] = random.uniform(-10, 10)
                p['scale'] = 1.0
                p['trail'] = []
                p['glow'] = ptype in ['glow', 'explosion', 'star']
                p['spark'] = ptype in ['spark', 'electric']
                self.active.append(p)
    
    def spawn_trail(self, x, y, color):
        if self.pool and random.random() < 0.4 and len(self.active) < self.max_active:
            p = self.pool.pop()
            p['x'] = x + random.uniform(-3, 3)
            p['y'] = y + random.uniform(-3, 3)
            p['vx'] = random.uniform(-0.5, 0.5)
            p['vy'] = random.uniform(-0.5, 0.5)
            p['life'] = random.randint(15, 25)
            p['color'] = color
            p['radius'] = random.uniform(2, 4)
            p['active'] = True
            p['type'] = 'trail'
            p['scale'] = 1.0
            p['trail'] = []
            p['glow'] = False
            p['spark'] = False
            self.active.append(p)
    
    def spawn_explosion(self, x, y, color, count=20):
        for _ in range(count):
            if self.pool and len(self.active) < self.max_active:
                p = self.pool.pop()
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(3, 10)
                p['x'] = x
                p['y'] = y
                p['vx'] = math.cos(angle) * speed
                p['vy'] = math.sin(angle) * speed
                p['life'] = random.randint(40, 60)
                p['color'] = color
                p['radius'] = random.uniform(3, 8)
                p['active'] = True
                p['type'] = 'explosion'
                p['rotation'] = random.uniform(0, 360)
                p['rotation_speed'] = random.uniform(-20, 20)
                p['scale'] = 1.0
                p['trail'] = []
                p['glow'] = True
                p['spark'] = False
                self.active.append(p)
    
    def spawn_spark(self, x, y, color, count=10):
        for _ in range(count):
            if self.pool and len(self.active) < self.max_active:
                p = self.pool.pop()
                p['x'] = x
                p['y'] = y
                p['vx'] = random.uniform(-8, 8)
                p['vy'] = random.uniform(-8, 8)
                p['life'] = random.randint(10, 20)
                p['color'] = color
                p['radius'] = random.uniform(1, 3)
                p['active'] = True
                p['type'] = 'spark'
                p['rotation'] = random.uniform(0, 360)
                p['rotation_speed'] = random.uniform(-30, 30)
                p['scale'] = 1.0
                p['trail'] = []
                p['glow'] = False
                p['spark'] = True
                self.active.append(p)
    
    def spawn_star(self, x, y, color, count=8):
        for _ in range(count):
            if self.pool and len(self.active) < self.max_active:
                p = self.pool.pop()
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(2, 6)
                p['x'] = x
                p['y'] = y
                p['vx'] = math.cos(angle) * speed
                p['vy'] = math.sin(angle) * speed
                p['life'] = random.randint(50, 80)
                p['color'] = color
                p['radius'] = random.uniform(2, 5)
                p['active'] = True
                p['type'] = 'star'
                p['rotation'] = random.uniform(0, 360)
                p['rotation_speed'] = random.uniform(-15, 15)
                p['scale'] = 1.0
                p['trail'] = []
                p['glow'] = True
                p['spark'] = False
                self.active.append(p)
    
    def spawn_electric(self, x, y, color, count=15):
        for _ in range(count):
            if self.pool and len(self.active) < self.max_active:
                p = self.pool.pop()
                p['x'] = x + random.uniform(-20, 20)
                p['y'] = y + random.uniform(-20, 20)
                p['vx'] = random.uniform(-2, 2)
                p['vy'] = random.uniform(-2, 2)
                p['life'] = random.randint(8, 15)
                p['color'] = color
                p['radius'] = random.uniform(1, 2)
                p['active'] = True
                p['type'] = 'electric'
                p['rotation'] = random.uniform(0, 360)
                p['rotation_speed'] = random.uniform(-40, 40)
                p['scale'] = 1.0
                p['trail'] = []
                p['glow'] = True
                p['spark'] = True
                self.active.append(p)
    
    def update(self):
        for p in self.active[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            if p['type'] != 'trail' and p['type'] != 'electric':
                p['vy'] += 0.15
            
            p['rotation'] += p['rotation_speed']
            p['rotation_speed'] *= 0.98
            
            p['life'] -= 1
            
            if p['type'] in ['explosion', 'star']:
                p['scale'] = max(0.1, p['scale'] - 0.01)
            
            if p['type'] == 'trail':
                p['trail'].append((p['x'], p['y']))
                if len(p['trail']) > 5:
                    p['trail'].pop(0)
            
            if p['life'] <= 0:
                p['active'] = False
                self.active.remove(p)
                if len(self.pool) < self.max_size:
                    self.pool.append(p)
    
    def draw(self, surface):
        screen_rect = surface.get_rect()
        draw_circle = pygame.draw.circle
        
        for p in self.active:
            particle_rect = pygame.Rect(p['x'] - p['radius'], p['y'] - p['radius'], 
                                       p['radius'] * 2, p['radius'] * 2)
            if not screen_rect.colliderect(particle_rect.inflate(20, 20)):
                continue
            
            alpha = int(255 * (p['life'] / 60))
            radius = p['radius'] * p['scale']
            color = (*p['color'][:3], alpha)
            x, y = p['x'], p['y']
            
            if p['glow']:
                glow_radius = radius * 2
                for i in range(3):
                    glow_alpha = int(alpha * (0.3 - i * 0.1))
                    if glow_alpha > 0:
                        draw_circle(surface, (*p['color'][:3], glow_alpha), 
                                   (int(x), int(y)), 
                                   int(glow_radius - i * radius * 0.3))
            
            if p['type'] == 'trail' and p['trail']:
                for i, (tx, ty) in enumerate(p['trail']):
                    trail_alpha = int(alpha * (i / len(p['trail'])))
                    draw_circle(surface, (*p['color'][:3], trail_alpha), 
                               (int(tx), int(ty)), int(radius * 0.5))
            
            if p['spark']:
                spark_length = radius * 3
                angle_rad = math.radians(p['rotation'])
                end_x = x + math.cos(angle_rad) * spark_length
                end_y = y + math.sin(angle_rad) * spark_length
                pygame.draw.line(surface, color, (int(x), int(y)), (int(end_x), int(end_y)), 2)
            
            draw_circle(surface, color, (int(x), int(y)), int(radius))

class Meteor:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.x = random.randint(WIDTH, WIDTH + 200)
        self.y = random.randint(-100, HEIGHT // 2)
        self.speed = random.uniform(8, 15)
        self.length = random.randint(30, 80)
        self.alpha = random.randint(100, 200)
        self.active = True
    
    def update(self):
        self.x -= self.speed
        self.y += self.speed * 0.5
        if self.x < -100 or self.y > HEIGHT + 100:
            self.active = False
    
    def draw(self, surface):
        if self.active:
            end_x = self.x + self.length
            end_y = self.y - self.length * 0.5
            for i in range(3):
                alpha = self.alpha - i * 30
                if alpha > 0:
                    pygame.draw.line(surface, (255, 255, 255, alpha), 
                                   (int(self.x), int(self.y)), 
                                   (int(end_x), int(end_y)), 2 - i)

class AnimatedBackground:
    def __init__(self):
        self.stars = []
        for _ in range(120):
            self.stars.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(0, HEIGHT),
                'size': random.uniform(1, 3),
                'speed': random.uniform(0.2, 1.2),
                'alpha': random.randint(50, 200),
                'twinkle_speed': random.uniform(0.02, 0.08),
                'twinkle_offset': random.uniform(0, 2 * math.pi)
            })
        self.meteors = []
        self.meteor_timer = 0
        self.gradient_offset = 0
        self.nebula_clouds = []
        for _ in range(5):
            self.nebula_clouds.append({
                'x': random.randint(0, WIDTH),
                'y': random.randint(0, HEIGHT),
                'radius': random.randint(100, 300),
                'color': random.choice([(50, 30, 80), (30, 50, 80), (80, 30, 50)]),
                'alpha': random.randint(20, 40),
                'speed': random.uniform(0.05, 0.15)
            })
        self.shooting_stars = []
        self.shooting_star_timer = 0
    
    def update(self):
        self.gradient_offset = (self.gradient_offset + 0.5) % 360
        
        for star in self.stars:
            star['y'] += star['speed']
            star['twinkle_offset'] += star['twinkle_speed']
            if star['y'] > HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, WIDTH)
        
        for cloud in self.nebula_clouds:
            cloud['x'] += cloud['speed']
            if cloud['x'] > WIDTH + cloud['radius']:
                cloud['x'] = -cloud['radius']
                cloud['y'] = random.randint(0, HEIGHT)
        
        self.meteor_timer += 1
        if self.meteor_timer > random.randint(120, 300):
            self.meteors.append(Meteor())
            self.meteor_timer = 0
        
        for meteor in self.meteors[:]:
            meteor.update()
            if not meteor.active:
                self.meteors.remove(meteor)
        
        self.shooting_star_timer += 1
        if self.shooting_star_timer > random.randint(200, 400):
            self.shooting_stars.append(self._create_shooting_star())
            self.shooting_star_timer = 0
        
        for star in self.shooting_stars[:]:
            star['x'] += star['vx']
            star['y'] += star['vy']
            star['life'] -= 1
            if star['life'] <= 0:
                self.shooting_stars.remove(star)
    
    def _create_shooting_star(self):
        return {
            'x': random.randint(0, WIDTH),
            'y': random.randint(0, HEIGHT // 2),
            'vx': random.uniform(3, 8),
            'vy': random.uniform(1, 4),
            'life': random.randint(30, 60),
            'size': random.uniform(2, 4),
            'color': random.choice([WHITE, CYAN, GOLD])
        }
    
    def draw(self, surface):
        surface.fill(DARK_BG)
        
        draw_circle = pygame.draw.circle
        draw_line = pygame.draw.line
        
        for cloud in self.nebula_clouds:
            cx, cy, radius, color, alpha = cloud['x'], cloud['y'], cloud['radius'], cloud['color'], cloud['alpha']
            for i in range(3):
                cloud_alpha = alpha - i * 10
                if cloud_alpha > 0:
                    draw_circle(surface, (*color, cloud_alpha), (int(cx), int(cy)), int(radius - i * 20))
        
        for star in self.stars:
            twinkle = 0.5 + 0.5 * math.sin(star['twinkle_offset'])
            star_alpha = int(star['alpha'] * twinkle)
            draw_circle(surface, (255, 255, 255, star_alpha), 
                       (int(star['x']), int(star['y'])), int(star['size']))
        
        for meteor in self.meteors:
            meteor.draw(surface)
        
        for star in self.shooting_stars:
            trail_length = star['life'] * 0.5
            end_x = star['x'] - star['vx'] * trail_length * 0.3
            end_y = star['y'] - star['vy'] * trail_length * 0.3
            star_x, star_y = int(star['x']), int(star['y'])
            end_x_int, end_y_int = int(end_x), int(end_y)
            star_color = star['color']
            
            for i in range(3):
                trail_alpha = int(255 * (i / 3))
                draw_line(surface, (*star_color, trail_alpha), 
                         (star_x, star_y), (end_x_int, end_y_int), int(star['size'] - i))
            
            star_size = int(star['size'])
            draw_circle(surface, star_color, (star_x, star_y), star_size)

class ScreenShake:
    def __init__(self):
        self.offset_x = 0
        self.offset_y = 0
        self.intensity = 0
    
    def shake(self, intensity=10):
        self.intensity = intensity
    
    def update(self):
        if self.intensity > 0:
            self.offset_x = random.randint(-int(self.intensity), int(self.intensity))
            self.offset_y = random.randint(-int(self.intensity), int(self.intensity))
            self.intensity *= 0.9
            if self.intensity < 0.5:
                self.intensity = 0
                self.offset_x = 0
                self.offset_y = 0

class ScreenEffects:
    def __init__(self):
        self.shake = ScreenShake()
        self.flash_alpha = 0
        self.flash_color = WHITE
        self.blur_amount = 0
        self.color_filter = None
        self.slow_motion = 1.0
        self.target_slow_motion = 1.0
        self.vignette_alpha = 0
        self.chromatic_aberration = 0
    
    def trigger_shake(self, intensity=10):
        self.shake.shake(intensity)
    
    def trigger_flash(self, color=WHITE, duration=30):
        self.flash_color = color
        self.flash_alpha = 255
        self.flash_duration = duration
    
    def trigger_blur(self, amount=5, duration=60):
        self.blur_amount = amount
        self.blur_duration = duration
    
    def trigger_slow_motion(self, factor=0.3, duration=120):
        self.target_slow_motion = factor
        self.slow_motion_duration = duration
    
    def trigger_vignette(self, alpha=150, duration=60):
        self.vignette_alpha = alpha
        self.vignette_duration = duration
    
    def trigger_chromatic_aberration(self, offset=3, duration=30):
        self.chromatic_aberration = offset
        self.chromatic_duration = duration
    
    def update(self):
        self.shake.update()
        
        if self.flash_alpha > 0:
            self.flash_alpha -= 255 / self.flash_duration
            if self.flash_alpha < 0:
                self.flash_alpha = 0
        
        if self.blur_amount > 0:
            self.blur_amount -= 5 / self.blur_duration
            if self.blur_amount < 0:
                self.blur_amount = 0
        
        if abs(self.slow_motion - self.target_slow_motion) > 0.01:
            if self.slow_motion < self.target_slow_motion:
                self.slow_motion += 0.05
            else:
                self.slow_motion -= 0.05
        else:
            self.slow_motion = self.target_slow_motion
            self.target_slow_motion = 1.0
        
        if self.vignette_alpha > 0:
            self.vignette_alpha -= 150 / self.vignette_duration
            if self.vignette_alpha < 0:
                self.vignette_alpha = 0
        
        if self.chromatic_aberration > 0:
            self.chromatic_aberration -= 3 / self.chromatic_duration
            if self.chromatic_aberration < 0:
                self.chromatic_aberration = 0
    
    def apply(self, surface):
        offset_x, offset_y = self.shake.offset_x, self.shake.offset_y
        
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((*self.flash_color, int(self.flash_alpha)))
            surface.blit(flash_surf, (0, 0))
        
        if self.vignette_alpha > 0:
            vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            center_x, center_y = WIDTH // 2, HEIGHT // 2
            max_radius = int(math.sqrt(center_x**2 + center_y**2))
            
            for r in range(20, max_radius + 1, 20):
                alpha = int(self.vignette_alpha * (r / max_radius)**2)
                if alpha > 0:
                    pygame.draw.circle(vignette_surf, (0, 0, 0, alpha), 
                                     (center_x, center_y), r)
            surface.blit(vignette_surf, (0, 0))
        
        return offset_x, offset_y
    
    def get_time_scale(self):
        return self.slow_motion

class Easing:
    @staticmethod
    def linear(t):
        return t
    
    @staticmethod
    def ease_in_quad(t):
        return t * t
    
    @staticmethod
    def ease_out_quad(t):
        return t * (2 - t)
    
    @staticmethod
    def ease_in_out_quad(t):
        return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t
    
    @staticmethod
    def ease_in_cubic(t):
        return t * t * t
    
    @staticmethod
    def ease_out_cubic(t):
        return (--t) * t * t + 1
    
    @staticmethod
    def ease_in_out_cubic(t):
        return 4 * t * t * t if t < 0.5 else (t - 1) * (2 * t - 2) * (2 * t - 2) + 1
    
    @staticmethod
    def ease_in_elastic(t):
        if t == 0 or t == 1:
            return t
        return -math.pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * ((2 * math.pi) / 3))
    
    @staticmethod
    def ease_out_elastic(t):
        if t == 0 or t == 1:
            return t
        return math.pow(2, -10 * t) * math.sin((t * 10 - 0.75) * ((2 * math.pi) / 3)) + 1
    
    @staticmethod
    def ease_in_out_elastic(t):
        if t == 0 or t == 1:
            return t
        t = t * 2
        if t < 1:
            return -0.5 * math.pow(2, 10 * t - 10) * math.sin((t * 10 - 10.75) * ((2 * math.pi) / 3))
        return 0.5 * math.pow(2, -10 * t + 10) * math.sin((t * 10 - 10.75) * ((2 * math.pi) / 3)) + 1
    
    @staticmethod
    def ease_in_bounce(t):
        return 1 - Easing.ease_out_bounce(1 - t)
    
    @staticmethod
    def ease_out_bounce(t):
        n1 = 7.5625
        d1 = 2.75
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            t = t - 1.5 / d1
            return n1 * t * t + 0.75
        elif t < 2.5 / d1:
            t = t - 2.25 / d1
            return n1 * t * t + 0.9375
        else:
            t = t - 2.625 / d1
            return n1 * t * t + 0.984375
    
    @staticmethod
    def ease_in_out_bounce(t):
        return Easing.ease_in_bounce(t * 2) * 0.5 if t < 0.5 else Easing.ease_out_bounce(t * 2 - 1) * 0.5 + 0.5

class UIAnimation:
    def __init__(self):
        self.animations = []
    
    def add_fade_in(self, element, duration=30, callback=None):
        self.animations.append({
            'type': 'fade_in',
            'element': element,
            'duration': duration,
            'progress': 0,
            'callback': callback,
            'easing': Easing.ease_out_quad
        })
    
    def add_fade_out(self, element, duration=30, callback=None):
        self.animations.append({
            'type': 'fade_out',
            'element': element,
            'duration': duration,
            'progress': 0,
            'callback': callback,
            'easing': Easing.ease_in_quad
        })
    
    def add_slide_in(self, element, direction='left', duration=40, distance=200, callback=None):
        self.animations.append({
            'type': 'slide_in',
            'element': element,
            'direction': direction,
            'duration': duration,
            'distance': distance,
            'progress': 0,
            'callback': callback,
            'easing': Easing.ease_out_cubic
        })
    
    def add_scale_in(self, element, duration=30, callback=None):
        self.animations.append({
            'type': 'scale_in',
            'element': element,
            'duration': duration,
            'progress': 0,
            'callback': callback,
            'easing': Easing.ease_out_elastic
        })
    
    def add_bounce(self, element, duration=60, callback=None):
        self.animations.append({
            'type': 'bounce',
            'element': element,
            'duration': duration,
            'progress': 0,
            'callback': callback,
            'easing': Easing.ease_out_bounce
        })
    
    def add_pulse(self, element, duration=40, count=2, callback=None):
        self.animations.append({
            'type': 'pulse',
            'element': element,
            'duration': duration,
            'count': count,
            'progress': 0,
            'callback': callback,
            'easing': Easing.ease_in_out_sine
        })
    
    def add_shake(self, element, duration=20, intensity=5, callback=None):
        self.animations.append({
            'type': 'shake',
            'element': element,
            'duration': duration,
            'intensity': intensity,
            'progress': 0,
            'callback': callback
        })
    
    def update(self):
        for anim in self.animations[:]:
            anim['progress'] += 1
            
            if anim['progress'] >= anim['duration']:
                if anim['callback']:
                    anim['callback'](anim['element'])
                self.animations.remove(anim)
    
    def get_transform(self, element):
        for anim in self.animations:
            if anim['element'] == element:
                t = anim['progress'] / anim['duration']
                t = max(0, min(1, t))
                eased_t = anim['easing'](t)
                
                if anim['type'] == 'fade_in':
                    return {'alpha': int(255 * eased_t)}
                elif anim['type'] == 'fade_out':
                    return {'alpha': int(255 * (1 - eased_t))}
                elif anim['type'] == 'slide_in':
                    offset = anim['distance'] * (1 - eased_t)
                    if anim['direction'] == 'left':
                        return {'offset_x': -offset}
                    elif anim['direction'] == 'right':
                        return {'offset_x': offset}
                    elif anim['direction'] == 'up':
                        return {'offset_y': -offset}
                    elif anim['direction'] == 'down':
                        return {'offset_y': offset}
                elif anim['type'] == 'scale_in':
                    return {'scale': eased_t}
                elif anim['type'] == 'bounce':
                    return {'scale': eased_t}
                elif anim['type'] == 'pulse':
                    pulse_t = (anim['progress'] % (anim['duration'] // anim['count'])) / (anim['duration'] // anim['count'])
                    scale = 1.0 + 0.2 * math.sin(pulse_t * math.pi)
                    return {'scale': scale}
                elif anim['type'] == 'shake':
                    shake_x = random.randint(-anim['intensity'], anim['intensity'])
                    shake_y = random.randint(-anim['intensity'], anim['intensity'])
                    return {'offset_x': shake_x, 'offset_y': shake_y}
        
        return None

class AnimatedNumber:
    def __init__(self):
        self.animations = []
    
    def add(self, x, y, text, color, size=24):
        self.animations.append({
            'x': x, 'y': y, 'text': text, 'color': color, 'size': size,
            'life': 60, 'vy': -2, 'scale': 1.5
        })
    
    def update(self):
        to_remove = []
        for anim in self.animations:
            anim['y'] += anim['vy']
            anim['vy'] *= 0.95
            anim['life'] -= 1
            anim['scale'] = max(1.0, anim['scale'] - 0.02)
            if anim['life'] <= 0:
                to_remove.append(anim)
        
        for anim in to_remove:
            self.animations.remove(anim)
    
    def draw(self, surface):
        get_text_surface = ResourceCache.get_text_surface
        for anim in self.animations:
            life = anim['life']
            if life > 0:
                alpha = life * 4 if life <= 255 else 255
                text_surf = get_text_surface(anim['text'], anim['size'], anim['color'])
                text_surf.set_alpha(alpha)
                
                scale = anim['scale']
                if scale != 1.0:
                    w = int(text_surf.get_width() * scale)
                    h = int(text_surf.get_height() * scale)
                    scaled = pygame.transform.scale(text_surf, (w, h))
                    surface.blit(scaled, (anim['x'] - w // 2, anim['y']))
                else:
                    surface.blit(text_surf, (anim['x'] - text_surf.get_width() // 2, anim['y']))

class Button:
    def __init__(self, x, y, width, height, text, font_size=28, 
                 normal_color=(50, 50, 80), hover_color=(80, 80, 120), 
                 active_color=(100, 100, 150), text_color=WHITE,
                 border_radius=10, shadow_offset=3):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font_size = font_size
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.active_color = active_color
        self.text_color = text_color
        self.border_radius = border_radius
        self.shadow_offset = shadow_offset
        
        self.is_hovered = False
        self.is_pressed = False
        self.hover_progress = 0.0
        self.press_progress = 0.0
        self.scale = 1.0
        self.target_scale = 1.0
        self.click_callback = None
        self.particles = []
        self.glow_intensity = 0.0
    
    def set_callback(self, callback):
        self.click_callback = callback
    
    def update(self, mouse_pos, mouse_pressed):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        
        if self.is_hovered:
            self.target_scale = 1.05
            self.hover_progress = min(1.0, self.hover_progress + 0.15)
            self.glow_intensity = min(0.5, self.glow_intensity + 0.05)
        else:
            self.target_scale = 1.0
            self.hover_progress = max(0.0, self.hover_progress - 0.1)
            self.glow_intensity = max(0.0, self.glow_intensity - 0.03)
        
        if self.is_hovered and mouse_pressed[0]:
            self.is_pressed = True
            self.press_progress = min(1.0, self.press_progress + 0.2)
            self.target_scale = 0.95
        else:
            self.is_pressed = False
            self.press_progress = max(0.0, self.press_progress - 0.15)
        
        self.scale += (self.target_scale - self.scale) * 0.3
        
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.1
            p['life'] -= 1
            p['alpha'] = int(255 * (p['life'] / p['max_life']))
            if p['life'] <= 0:
                self.particles.remove(p)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            if self.click_callback:
                self.click_callback()
            self.spawn_click_particles()
            return True
        return False
    
    def spawn_click_particles(self):
        for _ in range(15):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            self.particles.append({
                'x': self.rect.centerx,
                'y': self.rect.centery,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.randint(20, 40),
                'max_life': 40,
                'color': self.text_color,
                'radius': random.uniform(2, 4),
                'alpha': 255
            })
    
    def draw(self, surface):
        current_color = self._interpolate_color(self.normal_color, self.hover_color, self.hover_progress)
        if self.is_pressed:
            current_color = self._interpolate_color(current_color, self.active_color, self.press_progress)
        
        scaled_rect = self._get_scaled_rect()
        
        if self.shadow_offset > 0:
            shadow_rect = scaled_rect.copy()
            shadow_rect.x += self.shadow_offset
            shadow_rect.y += self.shadow_offset
            shadow_color = (*[max(0, c - 30) for c in current_color], 100)
            self._draw_rounded_rect(surface, shadow_rect, shadow_color, self.border_radius)
        
        if self.glow_intensity > 0:
            glow_rect = scaled_rect.inflate(10, 10)
            glow_color = (*current_color[:3], int(50 * self.glow_intensity))
            self._draw_rounded_rect(surface, glow_rect, glow_color, self.border_radius + 5)
        
        self._draw_rounded_rect(surface, scaled_rect, current_color, self.border_radius)
        
        text_surf = ResourceCache.get_text_surface(self.text, self.font_size, self.text_color)
        scaled_text = pygame.transform.scale(text_surf, 
            (int(text_surf.get_width() * self.scale), 
             int(text_surf.get_height() * self.scale)))
        text_rect = scaled_text.get_rect(center=scaled_rect.center)
        surface.blit(scaled_text, text_rect)
        
        for p in self.particles:
            p_surf = pygame.Surface((int(p['radius'] * 2), int(p['radius'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*p['color'], p['alpha']), 
                             (int(p['radius']), int(p['radius'])), int(p['radius']))
            surface.blit(p_surf, (p['x'] - p['radius'], p['y'] - p['radius']))
    
    def _get_scaled_rect(self):
        center_x = self.rect.centerx
        center_y = self.rect.centery
        new_width = int(self.rect.width * self.scale)
        new_height = int(self.rect.height * self.scale)
        return pygame.Rect(center_x - new_width // 2, center_y - new_height // 2, new_width, new_height)
    
    def _interpolate_color(self, color1, color2, t):
        return tuple(int(c1 + (c2 - c1) * t) for c1, c2 in zip(color1, color2))
    
    def _draw_rounded_rect(self, surface, rect, color, radius):
        if len(color) == 4:
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, color, s.get_rect(), border_radius=radius)
            surface.blit(s, rect.topleft)
        else:
            pygame.draw.rect(surface, color, rect, border_radius=radius)

class Paddle:
    def __init__(self):
        self.width = 140
        self.height = 18
        self.base_width = 140
        self.base_height = 18
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 60
        self.speed = 10
        self.target_x = self.x
        self.glow_intensity = 0
        self.shake_offset = 0
        self.trail = []
        self.rainbow_hue = 0
        
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        self.rotation = 0.0
        self.target_rotation = 0.0
        self.elasticity = 0.0
        self.deformation = {'x': 0, 'y': 0}
        self.target_deformation = {'x': 0, 'y': 0}
        self.velocity_x = 0
        self.last_x = self.x
    
    def _get_rainbow_color(self):
        self.rainbow_hue = (self.rainbow_hue + 3) % 360
        color = pygame.Color(0)
        color.hsva = (self.rainbow_hue, 100, 100, 100)
        return (color.r, color.g, color.b)
    
    @property
    def rect(self):
        return pygame.Rect(self.x + self.shake_offset, self.y, self.width, self.height)
    
    @property
    def center(self):
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def move(self, direction):
        self.target_x += direction * self.speed
        self.target_x = max(0, min(WIDTH - self.width, self.target_x))
    
    def trigger_elastic(self):
        self.elasticity = 1.0
        self.scale_x = 1.2
        self.scale_y = 0.8
    
    def trigger_deformation(self, dx, dy):
        self.target_deformation = {'x': dx, 'y': dy}
    
    def trigger_rotation(self, angle):
        self.target_rotation = angle
    
    def update(self):
        old_x = self.x
        self.x += (self.target_x - self.x) * 0.3
        self.velocity_x = self.x - self.last_x
        self.last_x = self.x
        
        if abs(self.x - old_x) > 1:
            self.trail.append((old_x, self.y, 100, self.scale_x))
        
        if len(self.trail) > 10:
            self.trail.pop(0)
        
        for i in range(len(self.trail)):
            trail_item = list(self.trail[i])
            trail_item[2] -= 10
            if trail_item[2] <= 0:
                self.trail[i] = None
        
        self.trail = [t for t in self.trail if t is not None]
        
        self.glow_intensity = max(0, self.glow_intensity - 0.05)
        self.shake_offset *= 0.8
        
        self.scale_x += (self.target_scale_x - self.scale_x) * 0.2
        self.scale_y += (self.target_scale_y - self.scale_y) * 0.2
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        
        self.rotation += (self.target_rotation - self.rotation) * 0.1
        self.target_rotation = 0.0
        
        if self.elasticity > 0:
            self.elasticity *= 0.9
            sin_val = math.sin(self.elasticity * math.pi)
            self.scale_x = 1.0 + 0.2 * sin_val
            self.scale_y = 1.0 - 0.2 * sin_val
        
        self.deformation['x'] += (self.target_deformation['x'] - self.deformation['x']) * 0.15
        self.deformation['y'] += (self.target_deformation['y'] - self.deformation['y']) * 0.15
        self.target_deformation = {'x': 0, 'y': 0}
        
        self.width = self.base_width * self.scale_x
        self.height = self.base_height * self.scale_y
    
    def trigger_glow(self):
        self.glow_intensity = 1.0
    
    def shake(self):
        self.shake_offset = random.randint(-5, 5)
    
    def draw(self, surface, color=BLUE, has_shield=False, has_rage=False, skin_data=None):
        rect = self.rect
        center_x = rect.centerx
        center_y = rect.centery
        
        display_color = color
        glow_color = CYAN
        
        if skin_data:
            if skin_data.get("rainbow"):
                display_color = self._get_rainbow_color()
                glow_color = display_color
            elif skin_data.get("color"):
                display_color = skin_data["color"]
            if skin_data.get("glow"):
                glow_color = skin_data["glow"]
        
        final_color = RED if has_rage else display_color
        
        for t in self.trail:
            trail_alpha = t[2]
            trail_rect = pygame.Rect(t[0], t[1], self.width, self.height)
            pygame.draw.rect(surface, (*display_color[:3], int(trail_alpha * 0.5)), 
                            trail_rect, border_radius=8)
        
        if self.glow_intensity > 0:
            glow_radius = int(max(self.width, self.height) * 1.5 * self.glow_intensity)
            for i in range(3):
                alpha = int(50 * self.glow_intensity * (1 - i / 3))
                pygame.draw.ellipse(surface, (*glow_color, alpha), 
                                   (center_x - glow_radius + i * 10, 
                                    center_y - glow_radius * 0.3 + i * 5,
                                    glow_radius * 2 - i * 20, 
                                    glow_radius * 0.6 - i * 10))
        
        if has_shield:
            for i in range(3, 0, -1):
                shield_rect = rect.inflate(i * 8, i * 8)
                pygame.draw.rect(surface, (*ORANGE, 50), shield_rect, border_radius=15)
        
        pygame.draw.rect(surface, final_color, rect, border_radius=10)
        
        highlight = pygame.Rect(rect.x + 5, rect.y + 3, rect.width - 10, 6)
        pygame.draw.rect(surface, (*WHITE, 100), highlight, border_radius=3)
        
        pygame.draw.rect(surface, WHITE, rect, 2, border_radius=10)
        
        if has_rage:
            rage_color = (255, 100, 100)
            pygame.draw.rect(surface, rage_color, rect, 3, border_radius=10)
            for i in range(3):
                offset = (i - 1) * 5
                pygame.draw.line(surface, rage_color, 
                               (center_x + offset, rect.y + 5),
                               (center_x + offset, rect.bottom - 5), 2)
        
        if has_shield:
            shield_color = (100, 200, 255)
            pygame.draw.ellipse(surface, (*shield_color, 100), rect.inflate(10, 10))
            pygame.draw.ellipse(surface, shield_color, rect.inflate(10, 10), 2)

class Ball(pygame.sprite.Sprite):
    def __init__(self, ball_type="normal", item_type=None, skin_color=None, speed_mult=1.0):
        super().__init__()
        self.ball_type = ball_type
        self.item_type = item_type
        self.angle = 0
        self.pulse = 0
        self.trail = []
        self.skin_color = skin_color
        self.speed_mult = speed_mult
        
        self.base_radius = 15
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        self.rotation = 0.0
        self.rotation_speed = 0.0
        self.elasticity = 0.0
        self.glow_intensity = 0.0
        self.velocity_x = 0
        self.velocity_y = 0
        self.last_x = 0
        self.last_y = 0
        
        self._setup_properties()
        self._create_image()
        self.rect = self.image.get_rect(center=(random.randint(60, WIDTH - 60), 50))
    
    def _setup_properties(self):
        if self.ball_type == "boss":
            self.base_radius = 28
            self.radius = 28
            self.color = (220, 50, 50)
            self.speed_x = random.choice([-4, 4]) * self.speed_mult
            self.speed_y = 5 * self.speed_mult
            self.health = 10
        elif self.ball_type == "fast":
            self.base_radius = 12
            self.radius = 12
            self.color = (255, 100, 100)
            self.speed_x = random.choice([-6, 6]) * self.speed_mult
            self.speed_y = 6 * self.speed_mult
        elif self.ball_type == "big":
            self.base_radius = 22
            self.radius = 22
            self.color = (100, 100, 255)
            self.speed_x = random.choice([-3, 3]) * self.speed_mult
            self.speed_y = 3 * self.speed_mult
        elif self.ball_type == "item":
            item_colors = {
                "score_plus": GOLD, "slow_down": CYAN, "extra_life": GREEN,
                "shield": ORANGE, "magnet": PURPLE, "rage": RED,
                "freeze": (150, 220, 255), "double_score": PINK, "shrink": (100, 255, 100),
                "expand": (255, 200, 100), "multiball": (200, 100, 255)
            }
            self.base_radius = 14
            self.radius = 14
            self.color = item_colors.get(self.item_type, WHITE)
            self.speed_x = random.choice([-2, 2])
            self.speed_y = 2.5
        else:
            self.base_radius = 15
            self.radius = 15
            self.color = self.skin_color if self.skin_color else (100, 150, 255)
            self.speed_x = random.choice([-3, 3]) * self.speed_mult
            self.speed_y = 4 * self.speed_mult
    
    def trigger_elastic(self):
        self.elasticity = 1.0
        self.scale_x = 1.3
        self.scale_y = 0.7
    
    def trigger_rotation(self, speed):
        self.rotation_speed = speed
    
    def trigger_glow(self, intensity=1.0):
        self.glow_intensity = intensity
    
    def _create_image(self):
        size = int(self.base_radius * 2 + 10)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        color = self.color
        radius = self.base_radius
        draw_circle = pygame.draw.circle
        
        draw_circle(self.image, (*color[:3], 30), (center, center), radius + 6)
        draw_circle(self.image, (*color[:3], 30), (center, center), radius + 4)
        draw_circle(self.image, color, (center, center), radius)
        
        draw_circle(self.image, (*WHITE, 150), 
                   (center - radius // 3, center - radius // 3), radius // 4)
        
        if self.ball_type == "item":
            font_size = max(12, radius)
            symbols = {
                "score_plus": "+", "slow_down": "S", "extra_life": "♥",
                "shield": "◆", "magnet": "M", "rage": "!",
                "freeze": "❄", "double_score": "×2", "shrink": "↓",
                "expand": "↑", "multiball": "⊕"
            }
            symbol = symbols.get(self.item_type, "?")
            text = ResourceCache.get_text_surface(symbol, font_size, WHITE)
            text_rect = text.get_rect(center=(center, center))
            self.image.blit(text, text_rect)
    
    def update(self):
        last_center_x = self.rect.centerx
        last_center_y = self.rect.centery
        
        self.trail.append((last_center_x, last_center_y, self.scale_x))
        if len(self.trail) > 12:
            self.trail.pop(0)
        
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        
        self.velocity_x = self.rect.centerx - last_center_x
        self.velocity_y = self.rect.centery - last_center_y
        
        self.rotation += self.rotation_speed
        self.rotation_speed *= 0.98
        
        self.scale_x += (self.target_scale_x - self.scale_x) * 0.15
        self.scale_y += (self.target_scale_y - self.scale_y) * 0.15
        self.target_scale_x = 1.0
        self.target_scale_y = 1.0
        
        if self.elasticity > 0:
            self.elasticity *= 0.9
            sin_val = math.sin(self.elasticity * math.pi)
            self.scale_x = 1.0 + 0.3 * sin_val
            self.scale_y = 1.0 - 0.3 * sin_val
        
        self.glow_intensity = max(0, self.glow_intensity - 0.02)
        
        rect_left = self.rect.left
        rect_right = self.rect.right
        
        if rect_left <= 0 or rect_right >= WIDTH:
            self.speed_x *= -1
            self.rect.left = max(0, rect_left)
            self.rect.right = min(WIDTH, rect_right)
            self.trigger_elastic()
        
        ui_top_bound = 180
        if self.rect.top <= 0:
            self.speed_y *= -1
            self.rect.top = 0
            self.trigger_elastic()
        
        ui_right_bound = WIDTH - 70
        if self.rect.right > ui_right_bound and self.rect.top < ui_top_bound:
            if self.speed_x > 0:
                self.speed_x *= -1
                self.rect.right = ui_right_bound
    
    def draw_trail(self, surface):
        pass

class Block(pygame.sprite.Sprite):
    _COLORS = {"normal": PURPLE, "strong": (200, 100, 50), "moving": CYAN}
    
    def __init__(self, x, y, block_type="normal"):
        super().__init__()
        self.block_type = block_type
        self.width = 70
        self.height = 25
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._setup_appearance()
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 2 if block_type == "strong" else 1
    
    def _setup_appearance(self):
        color = self._COLORS.get(self.block_type, PURPLE)
        rect = self.image.get_rect()
        
        pygame.draw.rect(self.image, color, rect, border_radius=5)
        pygame.draw.rect(self.image, WHITE, rect, 2, border_radius=5)
        
        if self.block_type == "strong":
            pygame.draw.line(self.image, WHITE, (15, 8), (15, 17), 2)
            pygame.draw.line(self.image, WHITE, (35, 8), (35, 17), 2)

class LevelSystem:
    def __init__(self):
        self.level = 1
        self.exp = 0
        self.exp_to_next = 10
        self.level_up_animation = 0
    
    def add_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_next:
            self.exp -= self.exp_to_next
            self.level += 1
            self.exp_to_next = int(self.exp_to_next * 1.3)
            self.level_up_animation = 60
            return True
        return False
    
    def get_difficulty_multiplier(self):
        return 1.0 + (self.level - 1) * 0.15
    
    def update(self):
        if self.level_up_animation > 0:
            self.level_up_animation -= 1

class AchievementSystem:
    def __init__(self):
        self.achievements = {
            "first_blood": {"name": "初次接球", "desc": "成功接住第一个球", "unlocked": False},
            "combo_master": {"name": "连击大师", "desc": "达成10连击", "unlocked": False},
            "boss_slayer": {"name": "BOSS杀手", "desc": "击败第一个BOSS", "unlocked": False},
            "score_100": {"name": "百分达人", "desc": "单局得分超过100", "unlocked": False},
            "survivor": {"name": "生存专家", "desc": "生命值达到5", "unlocked": False},
            "level_5": {"name": "升级达人", "desc": "达到5级", "unlocked": False},
            "time_master": {"name": "时间大师", "desc": "限时模式得分超过50", "unlocked": False},
            "challenge_complete": {"name": "挑战成功", "desc": "完成挑战模式", "unlocked": False},
        }
        self.notification_queue = []
        self.current_notification = None
        self.notification_timer = 0
    
    def check(self, achievement_id, condition):
        if condition and not self.achievements[achievement_id]["unlocked"]:
            self.achievements[achievement_id]["unlocked"] = True
            self.notification_queue.append(achievement_id)
            return True
        return False
    
    def update(self):
        if self.notification_timer > 0:
            self.notification_timer -= 1
        elif self.notification_queue:
            self.current_notification = self.notification_queue.pop(0)
            self.notification_timer = 120
        elif self.notification_timer <= 0:
            self.current_notification = None
    
    def draw_notification(self, surface):
        if self.current_notification and self.notification_timer > 0:
            achievement = self.achievements[self.current_notification]
            
            if self.notification_timer > 30:
                alpha = 255
            else:
                alpha = self.notification_timer * 4
                if alpha > 255:
                    alpha = 255
            
            text1 = ResourceCache.get_text_surface("成就解锁!", 28, GOLD)
            text2 = ResourceCache.get_text_surface(achievement["name"], 24, WHITE)
            
            box_width = max(text1.get_width(), text2.get_width()) + 40
            box_height = 70
            box_x = WIDTH // 2 - box_width // 2
            box_y = 150
            
            s = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            pygame.draw.rect(s, (0, 0, 0, int(alpha * 0.8)), s.get_rect(), border_radius=10)
            pygame.draw.rect(s, (*GOLD, alpha), s.get_rect(), 2, border_radius=10)
            
            text1.set_alpha(alpha)
            text2.set_alpha(alpha)
            
            surface.blit(s, (box_x, box_y))
            surface.blit(text1, (WIDTH // 2 - text1.get_width() // 2, box_y + 10))
            surface.blit(text2, (WIDTH // 2 - text2.get_width() // 2, box_y + 40))

ITEM_TYPES = {
    "score_plus": {"effect": "score", "value": 15, "desc": "加分"},
    "slow_down": {"effect": "slow", "value": 0.6, "desc": "减速"},
    "extra_life": {"effect": "life", "value": 1, "desc": "生命"},
    "shield": {"effect": "shield", "value": 400, "desc": "护盾"},
    "magnet": {"effect": "magnet", "value": 350, "desc": "磁铁"},
    "rage": {"effect": "rage", "value": 300, "desc": "狂暴"},
    "freeze": {"effect": "freeze", "value": 200, "desc": "冻结"},
    "double_score": {"effect": "double", "value": 300, "desc": "双倍"},
    "shrink": {"effect": "shrink", "value": 250, "desc": "缩小"},
    "expand": {"effect": "expand", "value": 300, "desc": "扩大"},
    "multiball": {"effect": "multiball", "value": 3, "desc": "多球"},
    "bomb": {"effect": "bomb", "value": 100, "desc": "炸弹"},
    "time_slow": {"effect": "time_slow", "value": 0.5, "desc": "时间减缓"},
    "attract": {"effect": "attract", "value": 200, "desc": "吸引"},
    "rainbow": {"effect": "rainbow", "value": 150, "desc": "彩虹球"},
    "lightning": {"effect": "lightning", "value": 1, "desc": "闪电"},
}

SKILL_ICONS = {
    "shield": {"color": ORANGE, "symbol": "◆"},
    "magnet": {"color": PURPLE, "symbol": "M"},
    "rage": {"color": RED, "symbol": "!"},
    "freeze": {"color": (150, 220, 255), "symbol": "❄"},
    "double_score": {"color": PINK, "symbol": "×2"},
    "expand": {"color": (255, 200, 100), "symbol": "↑"},
}

PADDLE_SKINS = {
    "default": {
        "name": "经典蓝",
        "color": BLUE,
        "glow": CYAN,
        "unlock_score": 0,
        "description": "默认皮肤"
    },
    "fire": {
        "name": "烈焰红",
        "color": (255, 80, 50),
        "glow": (255, 200, 100),
        "unlock_score": 50,
        "description": "达到50分解锁"
    },
    "nature": {
        "name": "自然绿",
        "color": (50, 200, 80),
        "glow": (150, 255, 150),
        "unlock_score": 100,
        "description": "达到100分解锁"
    },
    "royal": {
        "name": "皇家紫",
        "color": (150, 80, 200),
        "glow": (200, 150, 255),
        "unlock_score": 200,
        "description": "达到200分解锁"
    },
    "golden": {
        "name": "黄金圣剑",
        "color": GOLD,
        "glow": (255, 255, 200),
        "unlock_score": 500,
        "description": "达到500分解锁"
    },
    "rainbow": {
        "name": "彩虹幻影",
        "color": None,
        "glow": None,
        "unlock_score": 1000,
        "description": "达到1000分解锁",
        "rainbow": True
    },
    "neon": {
        "name": "霓虹之夜",
        "color": (0, 255, 200),
        "glow": (255, 0, 200),
        "unlock_score": 1500,
        "description": "达到1500分解锁"
    },
}

BALL_SKINS = {
    "default": {
        "name": "经典球",
        "color": (100, 150, 255),
        "unlock_score": 0,
        "description": "默认皮肤"
    },
    "fire": {
        "name": "火球",
        "color": (255, 100, 50),
        "unlock_score": 75,
        "description": "达到75分解锁"
    },
    "ice": {
        "name": "冰球",
        "color": (150, 220, 255),
        "unlock_score": 150,
        "description": "达到150分解锁"
    },
    "gold": {
        "name": "金球",
        "color": GOLD,
        "unlock_score": 300,
        "description": "达到300分解锁"
    },
    "void": {
        "name": "虚空球",
        "color": (80, 0, 120),
        "unlock_score": 800,
        "description": "达到800分解锁"
    },
}

class MenuAnimation:
    def __init__(self):
        self.title_glow = 0
        self.title_glow_dir = 1
        self.selected_index = 0
        self.hover_scales = [1.0, 1.0, 1.0, 1.0]
        self.target_scales = [1.0, 1.0, 1.0, 1.0]
        self.fade_alpha = 255
        self.fade_target = 255
        self.fade_speed = 15
        self.particles = []
        self.particle_timer = 0
    
    def update(self):
        self.title_glow += 0.03 * self.title_glow_dir
        if self.title_glow >= 1.0:
            self.title_glow_dir = -1
        elif self.title_glow <= 0.0:
            self.title_glow_dir = 1
        
        for i in range(len(self.hover_scales)):
            diff = self.target_scales[i] - self.hover_scales[i]
            self.hover_scales[i] += diff * 0.15
        
        if self.fade_alpha != self.fade_target:
            diff = self.fade_target - self.fade_alpha
            self.fade_alpha += diff * 0.1
            if abs(diff) < 1:
                self.fade_alpha = self.fade_target
        
        self.particle_timer += 1
        if self.particle_timer > 5:
            self.particle_timer = 0
            self.particles.append({
                'x': random.randint(0, WIDTH),
                'y': HEIGHT + 10,
                'vx': random.uniform(-1, 1),
                'vy': random.uniform(-3, -1),
                'size': random.uniform(2, 6),
                'alpha': random.randint(100, 200),
                'color': random.choice([GOLD, CYAN, PURPLE, PINK])
            })
        
        to_remove = []
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['alpha'] -= 2
            if p['alpha'] <= 0 or p['y'] < -10:
                to_remove.append(p)
        
        for p in to_remove:
            self.particles.remove(p)
    
    def set_hover(self, index):
        for i in range(len(self.target_scales)):
            self.target_scales[i] = 1.15 if i == index else 1.0
    
    def start_fade_out(self):
        self.fade_target = 0
    
    def start_fade_in(self):
        self.fade_alpha = 0
        self.fade_target = 255
    
    def is_fade_complete(self):
        return abs(self.fade_alpha - self.fade_target) < 5
    
    def draw_particles(self, surface):
        draw_circle = pygame.draw.circle
        for p in self.particles:
            size = p['size']
            size_int = int(size)
            s = pygame.Surface((size_int * 2, size_int * 2), pygame.SRCALPHA)
            draw_circle(s, (*p['color'][:3], int(p['alpha'])), 
                       (size_int, size_int), size_int)
            surface.blit(s, (p['x'], p['y']))
    
    def draw_title_with_glow(self, surface, text, size, base_color, x, y):
        try:
            glow_intensity = int(100 + 155 * self.title_glow)
            glow_color = (base_color[0], base_color[1], base_color[2])
            
            for offset in range(3, 0, -1):
                glow_surf = ResourceCache.get_text_surface(text, size, glow_color)
                if glow_surf.get_width() > 1:
                    glow_surf.set_alpha(glow_intensity // (offset + 1))
                    surface.blit(glow_surf, (x - glow_surf.get_width() // 2 - offset * 2, 
                                              y - offset * 2))
            
            main_surf = ResourceCache.get_text_surface(text, size, base_color)
            surface.blit(main_surf, (x - main_surf.get_width() // 2, y))
            
            return main_surf.get_height()
        except Exception as e:
            print(f"Error in draw_title_with_glow: {e}")
            return 0
    
    def draw_fade_overlay(self, surface):
        if self.fade_alpha > 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, int(self.fade_alpha)))
            surface.blit(overlay, (0, 0))

class Game:
    def __init__(self):
        self.state = "menu"
        self.game_mode = "endless"
        self.difficulty = "normal"
        self.bg = AnimatedBackground()
        self.particles = ParticlePool()
        self.level_system = LevelSystem()
        self.achievements = AchievementSystem()
        self.screen_shake = ScreenShake()
        self.screen_effects = ScreenEffects()
        self.animated_numbers = AnimatedNumber()
        self.menu_animation = MenuAnimation()
        self.load_high_score()
        self.load_skins()
        self.reset_game()
        self.key_cooldown = {}
        self.key_states = {}
        self.pending_state = None
        self.show_difficulty_notification = False
        self.difficulty_notification_time = 0
        self.rainbow_hue = 0
        self.last_spawn_time = 0
        
        # 缓存表面
        self.ui_cache = {}
        self.static_cache = {}
        
        pygame.key.stop_text_input()
    
    def reset_game(self):
        self.paddle = Paddle()
        self.balls = pygame.sprite.Group()
        self.blocks = pygame.sprite.Group()
        
        ball_skin = BALL_SKINS.get(self.ball_skin, BALL_SKINS["default"])
        ball_color = ball_skin.get("color")
        self.balls.add(Ball(skin_color=ball_color, speed_mult=self.get_speed_multiplier()))
        
        self.score = 0
        self.combo = 0
        self.combo_timer = 0
        
        difficulty_lives = {"easy": 4, "normal": 3, "hard": 2}
        self.lives = difficulty_lives.get(self.difficulty, 3)
        self.max_lives = 5
        
        self.shield = False
        self.shield_timer = 0
        self.magnet = False
        self.magnet_timer = 0
        self.rage = False
        self.rage_timer = 0
        self.freeze = False
        self.freeze_timer = 0
        self.double_score = False
        self.double_score_timer = 0
        self.expand = False
        self.expand_timer = 0
        self.attract = False
        self.attract_timer = 0
        
        self.boss_mode = False
        self.boss_health = 0
        self.boss_defeated = 0
        
        self.countdown = 3
        self.countdown_tick = pygame.time.get_ticks()
        
        self.level_system = LevelSystem()
        self.game_time = 0
        self.fps = 60.0
        
        self.time_limit = 60
        self.time_remaining = self.time_limit
        self.challenge_goal = 30
        self.challenge_progress = 0
    
    def load_high_score(self):
        try:
            if os.path.exists("high.json"):
                with open("high.json", encoding='utf-8') as f:
                    data = json.load(f)
                    self.high_scores = data.get("scores", {"endless": 0, "timed": 0, "challenge": 0})
                    return
        except:
            pass
        self.high_scores = {"endless": 0, "timed": 0, "challenge": 0}
    
    def load_skins(self):
        self.paddle_skin = "default"
        self.ball_skin = "default"
        self.skin_page = 0
        self.skin_type = "paddle"
        try:
            if os.path.exists("skins.json"):
                with open("skins.json", encoding='utf-8') as f:
                    data = json.load(f)
                    self.paddle_skin = data.get("paddle_skin", "default")
                    self.ball_skin = data.get("ball_skin", "default")
        except:
            pass
    
    def save_skins(self):
        try:
            with open("skins.json", "w", encoding='utf-8') as f:
                json.dump({"paddle_skin": self.paddle_skin, "ball_skin": self.ball_skin}, f)
        except:
            pass
    
    def get_max_score(self):
        return max(self.high_scores.values()) if self.high_scores else 0
    
    def is_skin_unlocked(self, skin_id, skin_type="paddle"):
        if skin_type == "paddle":
            skin = PADDLE_SKINS.get(skin_id)
        else:
            skin = BALL_SKINS.get(skin_id)
        if not skin:
            return False
        return self.get_max_score() >= skin["unlock_score"]
    
    def get_rainbow_color(self):
        self.rainbow_hue = (self.rainbow_hue + 2) % 360
        color = pygame.Color(0)
        color.hsva = (self.rainbow_hue, 100, 100, 100)
        return (color.r, color.g, color.b)
    
    def save_high_score(self):
        try:
            with open("high.json", "w", encoding='utf-8') as f:
                json.dump({"scores": self.high_scores}, f)
        except:
            pass
    
    def get_speed_multiplier(self):
        return {"easy": 0.7, "normal": 1.0, "hard": 1.2}.get(self.difficulty, 1.0)
    
    def spawn_ball(self):
        level_mult = self.level_system.get_difficulty_multiplier()
        
        difficulty_settings = {
            "easy": {"max_balls": 3, "spawn_rate": 0.01, "item_chance": 0.3, "special_chance": 0.02, "spawn_cooldown": 60},
            "normal": {"max_balls": 4, "spawn_rate": 0.015, "item_chance": 0.22, "special_chance": 0.06, "spawn_cooldown": 45},
            "hard": {"max_balls": 5, "spawn_rate": 0.02, "item_chance": 0.18, "special_chance": 0.1, "spawn_cooldown": 35}
        }
        settings = difficulty_settings.get(self.difficulty, difficulty_settings["normal"])
        
        max_balls = settings["max_balls"]
        spawn_rate = settings["spawn_rate"]
        spawn_cooldown = settings["spawn_cooldown"]
        
        if self.boss_mode:
            max_balls = 5
        
        balls_count = len(self.balls)
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_spawn_time < spawn_cooldown * 10:
            return
        
        if balls_count < max_balls and random.random() < spawn_rate * level_mult:
            ball_skin = BALL_SKINS.get(self.ball_skin, BALL_SKINS["default"])
            ball_color = ball_skin.get("color")
            rand_val = random.random()
            
            item_chance = settings["item_chance"]
            special_chance = settings["special_chance"]
            
            speed_mult = self.get_speed_multiplier()
            
            if rand_val < item_chance:
                item = random.choice(list(ITEM_TYPES.keys()))
                self.balls.add(Ball(ball_type="item", item_type=item))
            elif rand_val < item_chance + special_chance and self.level_system.level >= 3:
                ball_type = "fast" if random.random() < 0.5 else "big"
                self.balls.add(Ball(ball_type=ball_type, speed_mult=speed_mult))
            else:
                self.balls.add(Ball(skin_color=ball_color, speed_mult=speed_mult))
            
            self.last_spawn_time = current_time
    
    def handle_item_effect(self, item_type):
        effect = ITEM_TYPES[item_type]["effect"]
        value = ITEM_TYPES[item_type]["value"]
        
        if effect == "score":
            add = value * (2 if self.double_score else 1)
            self.score += add
            self.animated_numbers.add(WIDTH // 2, HEIGHT // 2, f"+{add}", GOLD, 32)
        elif effect == "slow":
            for ball in self.balls:
                ball.speed_x *= value
                ball.speed_y *= value
        elif effect == "life":
            self.lives = min(self.lives + value, self.max_lives)
            self.achievements.check("survivor", self.lives >= 5)
        elif effect == "shield":
            self.shield = True
            self.shield_timer = value
        elif effect == "magnet":
            self.magnet = True
            self.magnet_timer = value
        elif effect == "rage":
            self.rage = True
            self.rage_timer = value
        elif effect == "freeze":
            self.freeze = True
            self.freeze_timer = value
        elif effect == "double":
            self.double_score = True
            self.double_score_timer = value
        elif effect == "shrink":
            self.paddle.width = max(80, self.paddle.width - 20)
        elif effect == "expand":
            self.expand = True
            self.expand_timer = value
            self.paddle.width = min(200, self.paddle.width + 40)
        elif effect == "multiball":
            ball_skin = BALL_SKINS.get(self.ball_skin, BALL_SKINS["default"])
            ball_color = ball_skin.get("color")
            for _ in range(value):
                self.balls.add(Ball(skin_color=ball_color, speed_mult=self.get_speed_multiplier()))
        elif effect == "bomb":
            for ball in list(self.balls):
                if ball.ball_type != "boss":
                    ball.kill()
            self.particles.spawn_explosion(WIDTH // 2, HEIGHT // 2, ORANGE, 50)
            self.screen_shake.shake(15)
            self.score += 50
            self.animated_numbers.add(WIDTH // 2, HEIGHT // 2, "+50", ORANGE, 32)
        elif effect == "time_slow":
            self.screen_effects.trigger_slow_motion(value, 120)
            self.animated_numbers.add(WIDTH // 2, HEIGHT // 2, "⏱", CYAN, 32)
        elif effect == "attract":
            self.attract = True
            self.attract_timer = value
            self.animated_numbers.add(WIDTH // 2, HEIGHT // 2, "⚡", PURPLE, 32)
        elif effect == "rainbow":
            for ball in self.balls:
                ball.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                ball._create_image()
            self.animated_numbers.add(WIDTH // 2, HEIGHT // 2, "🌈", PINK, 32)
        elif effect == "lightning":
            for block in list(self.blocks):
                block.health -= 1
                if block.health <= 0:
                    block.kill()
                    self.score += 5
            self.screen_effects.trigger_flash(WHITE, 10)
            self.screen_shake.shake(8)
    
    def update(self):
        self.bg.update()
        self.screen_shake.update()
        self.screen_effects.update()
        self.animated_numbers.update()
        self.menu_animation.update()
        
        if self.pending_state and self.menu_animation.is_fade_complete():
            self.state = self.pending_state
            self.pending_state = None
            self.menu_animation.start_fade_in()
        
        if self.state == "playing":
            self._update_game()
        elif self.state == "countdown":
            self._update_countdown()
        
        self.achievements.update()
    
    def _update_countdown(self):
        now = pygame.time.get_ticks()
        if now - self.countdown_tick > 1000:
            self.countdown -= 1
            self.countdown_tick = now
            if self.countdown <= 0:
                self.state = "playing"
                if self.game_mode == "timed":
                    self.time_remaining = self.time_limit
                    self.game_start_time = pygame.time.get_ticks()
    
    def _update_game(self):
        self.game_time += 1
        
        if self.game_mode == "timed":
            elapsed = (pygame.time.get_ticks() - self.game_start_time) / 1000
            self.time_remaining = max(0, self.time_limit - elapsed)
            if self.time_remaining <= 0:
                self.state = "game_over"
                mode_key = "timed"
                if self.score > self.high_scores.get(mode_key, 0):
                    self.high_scores[mode_key] = self.score
                    self.save_high_score()
                self.achievements.check("time_master", self.score >= 50)
                return
        
        self.combo_timer = max(0, self.combo_timer - 1)
        
        timers = [
            ('shield', 'shield_timer'),
            ('magnet', 'magnet_timer'),
            ('rage', 'rage_timer'),
            ('freeze', 'freeze_timer'),
            ('double_score', 'double_score_timer'),
            ('expand', 'expand_timer'),
            ('attract', 'attract_timer')
        ]
        
        for attr, timer_attr in timers:
            current = getattr(self, timer_attr)
            if current > 0:
                setattr(self, timer_attr, current - 1)
            else:
                setattr(self, attr, False)
        
        if not self.expand and self.paddle.width > 140:
            self.paddle.width = 140
        
        self.paddle.update()
        self.level_system.update()
        
        if not self.freeze:
            self.balls.update()
        
        for ball in self.balls:
            if ball.ball_type != "item":
                self.particles.spawn_trail(ball.rect.centerx, ball.rect.centery, ball.color)
        
        self.spawn_ball()
        
        # 确保至少有一个球
        if not self.balls:
            ball_skin = BALL_SKINS.get(self.ball_skin, BALL_SKINS["default"])
            ball_color = ball_skin.get("color")
            self.balls.add(Ball(skin_color=ball_color, speed_mult=self.get_speed_multiplier()))
        
        difficulty_settings = {
            "easy": {"speed_mult": 0.6, "ball_count": 1, "life": 3},
            "normal": {"speed_mult": 1.0, "ball_count": 2, "life": 2},
            "hard": {"speed_mult": 1.4, "ball_count": 3, "life": 1}
        }
        settings = difficulty_settings.get(self.difficulty, difficulty_settings["normal"])
        speed_mult = settings["speed_mult"]
        level_mult = self.level_system.get_difficulty_multiplier()
        current_speed = (4 + self.level_system.level * 0.3) * speed_mult
        
        for ball in self.balls:
            if ball.ball_type not in ["item", "boss"]:
                max_speed = current_speed * 1.5
                ball.speed_x = max(-max_speed, min(max_speed, ball.speed_x))
                ball.speed_y = max(2, min(max_speed, abs(ball.speed_y))) * (1 if ball.speed_y > 0 else -1)
        
        if self.magnet:
            for ball in self.balls:
                if ball.ball_type not in ["item", "boss"]:
                    dx = self.paddle.center[0] - ball.rect.centerx
                    ball.rect.x += dx * 0.03
        
        self._handle_collisions()
        self._check_boss_spawn()
        self.particles.update()
    
    def _handle_collisions(self):
        paddle_rect = self.paddle.rect
        paddle_center_x = paddle_rect.centerx
        paddle_width_half = self.paddle.width / 2
        
        balls_to_kill = []
        need_new_ball = False
        lost_life = False
        
        for ball in self.balls:
            ball_rect = ball.rect
            
            if ball_rect.colliderect(paddle_rect) and ball.speed_y > 0:
                ball_center_x = ball_rect.centerx
                ball_center_y = ball_rect.centery
                
                self.particles.spawn(ball_center_x, ball_center_y, ball.color, 15)
                self.paddle.trigger_glow()
                ball.trigger_elastic()
                self.screen_effects.trigger_shake(intensity=5)
                
                if ball.ball_type == "item":
                    self.handle_item_effect(ball.item_type)
                    balls_to_kill.append(ball)
                    need_new_ball = True
                    continue
                
                self.combo += 1
                self.combo_timer = 90
                
                combo_bonus = self._check_combo_bonus()
                
                points = 1 + self.combo // 5
                if self.double_score:
                    points *= 2
                if ball.ball_type == "fast":
                    points *= 2
                elif ball.ball_type == "big":
                    points = max(1, points // 2)
                
                self.score += points
                self.animated_numbers.add(ball_center_x, ball_center_y, f"+{points}", GOLD, 20)
                
                if self.game_mode == "challenge":
                    self.challenge_progress += 1
                    if self.challenge_progress >= self.challenge_goal:
                        self.state = "game_over"
                        self.achievements.check("challenge_complete", True)
                        mode_key = "challenge"
                        if self.score > self.high_scores.get(mode_key, 0):
                            self.high_scores[mode_key] = self.score
                            self.save_high_score()
                
                if self.level_system.add_exp(points):
                    self.achievements.check("level_5", self.level_system.level >= 5)
                    self.screen_shake.shake(8)
                    self.screen_effects.trigger_flash(GOLD, 30)
                    self.screen_effects.trigger_slow_motion(0.5, 60)
                
                self.achievements.check("first_blood", True)
                self.achievements.check("combo_master", self.combo >= 10)
                self.achievements.check("score_100", self.score >= 100)
                
                if ball.ball_type == "boss":
                    ball.health -= 1
                    if ball.health <= 0:
                        self.boss_mode = False
                        self.boss_defeated += 1
                        self.score += 30
                        self.achievements.check("boss_slayer", True)
                        self.screen_shake.shake(15)
                        balls_to_kill.append(ball)
                        continue
                
                hit_pos = (ball_center_x - paddle_center_x) / paddle_width_half
                ball.speed_x = hit_pos * 6
                ball.speed_y = -abs(ball.speed_y) * 1.02
            
            elif ball_rect.top > HEIGHT:
                if ball.ball_type == "boss":
                    if self.shield:
                        self.shield = False
                    else:
                        self.lives -= 2
                        self.paddle.shake()
                        self.screen_shake.shake(10)
                        lost_life = True
                elif ball.ball_type != "item":
                    self.combo = 0
                    if self.shield:
                        self.shield = False
                    else:
                        self.lives -= 1
                        self.paddle.shake()
                        self.screen_shake.shake(5)
                        lost_life = True
                
                balls_to_kill.append(ball)
        
        for ball in balls_to_kill:
            ball.kill()
        
        if need_new_ball and not self.balls:
            ball_skin = BALL_SKINS.get(self.ball_skin, BALL_SKINS["default"])
            ball_color = ball_skin.get("color")
            self.balls.add(Ball(skin_color=ball_color, speed_mult=self.get_speed_multiplier()))
        
        if lost_life and self.lives <= 0 and self.game_mode != "challenge":
            self.state = "game_over"
            mode_key = "endless" if self.game_mode == "endless" else "timed"
            if self.score > self.high_scores.get(mode_key, 0):
                self.high_scores[mode_key] = self.score
                self.save_high_score()
        
        for ball in self.balls:
            if ball.ball_type not in ["item", "boss"]:
                hit_blocks = pygame.sprite.spritecollide(ball, self.blocks, False)
                for block in hit_blocks:
                    block_center_x = block.rect.centerx
                    block_center_y = block.rect.centery
                    
                    block.health -= 1
                    self.particles.spawn_explosion(block_center_x, block_center_y, block.image.get_at((0, 0))[:3], 15)
                    
                    if block.health <= 0:
                        block.kill()
                        self.score += 5
                        self.animated_numbers.add(block_center_x, block_center_y, "+5", GOLD, 15)
                    
                    ball_center_x = ball.rect.centerx
                    ball_center_y = ball.rect.centery
                    dx = abs(ball_center_x - block_center_x)
                    dy = abs(ball_center_y - block_center_y)
                    
                    if dx > dy:
                        ball.speed_x *= -1
                    else:
                        ball.speed_y *= -1
                    
                    ball.trigger_elastic()
                    self.screen_effects.trigger_shake(intensity=3)
                    break
        
        if self.attract:
            paddle_center_x = self.paddle.rect.centerx
            paddle_center_y = self.paddle.rect.centery
            for ball in self.balls:
                if ball.ball_type != "boss":
                    dx = paddle_center_x - ball.rect.centerx
                    dy = paddle_center_y - ball.rect.centery
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist > 10:
                        ball.speed_x += dx * 0.02
                        ball.speed_y += dy * 0.02
        
        if not self.balls:
            ball_skin = BALL_SKINS.get(self.ball_skin, BALL_SKINS["default"])
            ball_color = ball_skin.get("color")
            self.balls.add(Ball(skin_color=ball_color, speed_mult=self.get_speed_multiplier()))
    
    def _check_combo_bonus(self):
        combo_thresholds = [
            (10, "连击x10!", "extra_life"),
            (20, "连击x20!", "double_score"),
            (30, "连击x30!", "shield"),
            (50, "连击x50!", "rage"),
            (100, "连击x100!", "multiball")
        ]
        
        for threshold, message, bonus_type in combo_thresholds:
            if self.combo == threshold:
                self.animated_numbers.add(WIDTH // 2, HEIGHT // 3, message, ORANGE, 36)
                self.screen_effects.trigger_flash(GOLD, 15)
                
                if bonus_type == "extra_life":
                    self.lives = min(self.lives + 1, self.max_lives)
                elif bonus_type == "double_score":
                    self.double_score = True
                    self.double_score_timer = 600
                elif bonus_type == "shield":
                    self.shield = True
                    self.shield_timer = 400
                elif bonus_type == "rage":
                    self.rage = True
                    self.rage_timer = 300
                elif bonus_type == "multiball":
                    ball_skin = BALL_SKINS.get(self.ball_skin, BALL_SKINS["default"])
                    ball_color = ball_skin.get("color")
                    for _ in range(2):
                        self.balls.add(Ball(skin_color=ball_color, speed_mult=self.get_speed_multiplier()))
                
                return bonus_type
        
        return None
    
    def _check_boss_spawn(self):
        if self.game_mode != "endless":
            return
        if not self.boss_mode and self.score >= 40 and self.score % 40 == 0 and self.game_time % 60 == 0:
            self.boss_mode = True
            self.boss_health = 5 + self.level_system.level
            self.balls.empty()
            boss_ball = Ball(ball_type="boss", speed_mult=self.get_speed_multiplier())
            self.balls.add(boss_ball)
            self.screen_shake.shake(12)
            
            self.blocks.empty()
            for i in range(2 + self.level_system.level // 2):
                x = random.randint(100, WIDTH - 100)
                y = random.randint(180, 400)
                block_type = "strong" if random.random() < 0.3 else "normal"
                self.blocks.add(Block(x, y, block_type))
    
    def draw(self):
        offset_x = self.screen_shake.offset_x
        offset_y = self.screen_shake.offset_y
        
        self.bg.draw(screen)
        
        if self.state == "menu":
            self._draw_menu()
        elif self.state == "mode_select":
            self._draw_mode_select()
        elif self.state == "skin_select":
            self._draw_skin_select()
        elif self.state == "help":
            self._draw_help()
        elif self.state in ["countdown", "playing"]:
            self._draw_game(offset_x, offset_y)
        elif self.state == "game_over":
            self._draw_game(offset_x, offset_y)
            self._draw_game_over()
        elif self.state == "paused":
            self._draw_game(offset_x, offset_y)
            self._draw_pause()
        
        self.achievements.draw_notification(screen)
        self.animated_numbers.draw(screen)
        pygame.display.flip()
    
    def _draw_menu(self):
        try:
            # 绘制背景粒子
            self.menu_animation.draw_particles(screen)
            
            # 绘制简洁标题
            title_surf = ResourceCache.get_text_surface("接球大挑战", 64, GOLD)
            screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 80))
            
            # 绘制副标题
            subtitle = ResourceCache.get_text_surface("终极豪华版 v3.0", 28, CYAN)
            screen.blit(subtitle, (WIDTH // 2 - subtitle.get_width() // 2, 150))
            
            # 绘制简洁菜单项
            menu_items = [
                ("按 ENTER 选择模式", 30, WHITE),
                ("按 S 选择皮肤", 24, LIGHT_GRAY),
                ("按 H 查看帮助", 24, LIGHT_GRAY),
                ("按 1/2/3 选择难度", 22, CYAN),
            ]
            
            for i, (text, size, color) in enumerate(menu_items):
                surf = ResourceCache.get_text_surface(text, size, color)
                y = 250 + i * 50
                screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, y))
            
            # 绘制最高分区域
            high_y = 480
            high_text = ResourceCache.get_text_surface("最高分记录", 26, GOLD)
            screen.blit(high_text, (WIDTH // 2 - high_text.get_width() // 2, high_y))
            
            mode_names = {"endless": "无尽模式", "timed": "限时模式", "challenge": "挑战模式"}
            for i, (mode, name) in enumerate(mode_names.items()):
                score = self.high_scores.get(mode, 0)
                text = ResourceCache.get_text_surface(f"{name}: {score}", 20, WHITE)
                screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 520 + i * 28))
            
            # 绘制当前难度
            difficulty_names = {"easy": "简单", "normal": "普通", "hard": "困难"}
            difficulty_color = {"easy": GREEN, "normal": ORANGE, "hard": RED}
            current_diff_color = difficulty_color.get(self.difficulty, ORANGE)
            
            # 难度选择通知效果
            if self.show_difficulty_notification:
                now = pygame.time.get_ticks()
                elapsed = now - self.difficulty_notification_time
                if elapsed < 1000:
                    alpha = 255 - int(elapsed / 1000 * 255)
                    scale = 1.0 + int(elapsed / 1000 * 50) / 100
                    notif_text = ResourceCache.get_text_surface(
                        f"难度已设置: {difficulty_names.get(self.difficulty, '普通')}", 
                        32, current_diff_color)
                    notif_surf = pygame.transform.scale(notif_text, 
                        (int(notif_text.get_width() * scale), int(notif_text.get_height() * scale)))
                    notif_surf.set_alpha(alpha)
                    screen.blit(notif_surf, (WIDTH // 2 - notif_surf.get_width() // 2, HEIGHT // 2 - 100))
                else:
                    self.show_difficulty_notification = False
            
            diff_text = ResourceCache.get_text_surface(
                f"当前难度: {difficulty_names.get(self.difficulty, '普通')}", 
                18, current_diff_color)
            screen.blit(diff_text, (WIDTH // 2 - diff_text.get_width() // 2, HEIGHT - 60))
            
            # 绘制当前皮肤
            current_paddle = PADDLE_SKINS.get(self.paddle_skin, PADDLE_SKINS["default"])
            current_ball = BALL_SKINS.get(self.ball_skin, BALL_SKINS["default"])
            skin_text = ResourceCache.get_text_surface(
                f"当前皮肤: {current_paddle['name']} / {current_ball['name']}", 18, PURPLE)
            screen.blit(skin_text, (WIDTH // 2 - skin_text.get_width() // 2, HEIGHT - 35))
            
        except Exception as e:
            print(f"Error in _draw_menu: {e}")
            import traceback
            traceback.print_exc()
    
    def _draw_mode_select(self):
        try:
            title = ResourceCache.get_text_surface("选择游戏模式", 48, GOLD)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))
            
            modes = [
                ("1 - 无尽模式", "经典玩法，生命耗尽结束", WHITE),
                ("2 - 限时模式", "60秒内尽可能得分", CYAN),
                ("3 - 挑战模式", "连续接30个球不掉落", ORANGE),
            ]
            
            for i, (name, desc, color) in enumerate(modes):
                y = 220 + i * 100
                name_surf = ResourceCache.get_text_surface(name, 36, color)
                desc_surf = ResourceCache.get_text_surface(desc, 22, LIGHT_GRAY)
                screen.blit(name_surf, (WIDTH // 2 - name_surf.get_width() // 2, y))
                screen.blit(desc_surf, (WIDTH // 2 - desc_surf.get_width() // 2, y + 45))
            
            back = ResourceCache.get_text_surface("按 ESC 返回", 26, LIGHT_GRAY)
            screen.blit(back, (WIDTH // 2 - back.get_width() // 2, HEIGHT - 60))
        except Exception as e:
            print(f"Error in _draw_mode_select: {e}")
            import traceback
            traceback.print_exc()
    
    def _draw_skin_select(self):
        try:
            title = ResourceCache.get_text_surface("皮肤商店", 48, GOLD)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))
            
            tab_paddle = ResourceCache.get_text_surface("[ 挡板皮肤 ]", 28, 
                CYAN if self.skin_type == "paddle" else LIGHT_GRAY)
            tab_ball = ResourceCache.get_text_surface("[ 球皮肤 ]", 28,
                CYAN if self.skin_type == "ball" else LIGHT_GRAY)
            screen.blit(tab_paddle, (WIDTH // 2 - 150, 85))
            screen.blit(tab_ball, (WIDTH // 2 + 30, 85))
            
            max_score = self.get_max_score()
            score_text = ResourceCache.get_text_surface(f"历史最高分: {max_score}", 22, GOLD)
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, 120))
            
            skins = PADDLE_SKINS if self.skin_type == "paddle" else BALL_SKINS
            skin_list = list(skins.items())
            
            cols = 3
            card_width = 250
            card_height = 120
            start_x = (WIDTH - cols * card_width) // 2
            start_y = 160
            
            for i, (skin_id, skin) in enumerate(skin_list):
                try:
                    col = i % cols
                    row = i // cols
                    x = start_x + col * card_width + 10
                    y = start_y + row * (card_height + 15)
                    
                    unlocked = self.is_skin_unlocked(skin_id, self.skin_type)
                    selected = (skin_id == self.paddle_skin and self.skin_type == "paddle") or \
                               (skin_id == self.ball_skin and self.skin_type == "ball")
                    
                    card = pygame.Surface((card_width - 20, card_height), pygame.SRCALPHA)
                    
                    if selected:
                        pygame.draw.rect(card, (*GOLD, 50), card.get_rect(), border_radius=10)
                        pygame.draw.rect(card, GOLD, card.get_rect(), 3, border_radius=10)
                    elif unlocked:
                        pygame.draw.rect(card, (40, 40, 60, 200), card.get_rect(), border_radius=10)
                        pygame.draw.rect(card, (100, 100, 150), card.get_rect(), 2, border_radius=10)
                    else:
                        pygame.draw.rect(card, (30, 30, 40, 200), card.get_rect(), border_radius=10)
                        pygame.draw.rect(card, (60, 60, 80), card.get_rect(), 2, border_radius=10)
                    
                    preview_y = 15
                    if self.skin_type == "paddle":
                        preview_color = skin.get("color", BLUE)
                        if skin.get("rainbow"):
                            preview_color = self.get_rainbow_color()
                        pygame.draw.rect(card, preview_color, (30, preview_y, card_width - 80, 20), border_radius=8)
                        pygame.draw.rect(card, WHITE, (30, preview_y, card_width - 80, 20), 2, border_radius=8)
                    else:
                        preview_color = skin.get("color", (100, 150, 255))
                        pygame.draw.circle(card, preview_color, (card_width // 2 - 10, preview_y + 15), 18)
                        pygame.draw.circle(card, WHITE, (card_width // 2 - 10, preview_y + 15), 18, 2)
                    
                    name_text = ResourceCache.get_text_surface(skin["name"], 20, 
                        WHITE if unlocked else (100, 100, 100))
                    card.blit(name_text, (10, 50))
                    
                    if unlocked:
                        desc_text = ResourceCache.get_text_surface(skin["description"], 14, LIGHT_GRAY)
                        card.blit(desc_text, (10, 75))
                        
                        if selected:
                            use_text = ResourceCache.get_text_surface("使用中", 16, GOLD)
                        else:
                            use_text = ResourceCache.get_text_surface(f"按 {i+1} 选择", 14, CYAN)
                        card.blit(use_text, (10, 95))
                    else:
                        lock_text = ResourceCache.get_text_surface(f"需要 {skin['unlock_score']} 分解锁", 14, RED)
                        card.blit(lock_text, (10, 75))
                    
                    screen.blit(card, (x, y))
                except Exception as e:
                    print(f"Error drawing skin card {i}: {e}")
            
            hint = ResourceCache.get_text_surface("按 TAB 切换类型 | 按 ESC 返回", 22, LIGHT_GRAY)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 50))
        except Exception as e:
            print(f"Error in _draw_skin_select: {e}")
            import traceback
            traceback.print_exc()
    
    def _draw_help(self):
        try:
            title = ResourceCache.get_text_surface("游戏帮助", 48, GOLD)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))
            
            help_texts = [
                ("操作说明:", 26, CYAN),
                ("← → 或 A D : 移动挡板", 22, WHITE),
                ("ESC : 暂停游戏", 22, WHITE),
                ("", 20, WHITE),
                ("道具效果:", 26, CYAN),
                ("+ : 加15分  |  S : 减速  |  ♥ : 生命+1", 20, WHITE),
                ("◆ : 护盾  |  M : 磁铁  |  ! : 狂暴", 20, WHITE),
                ("❄ : 冻结  |  ×2 : 双倍  |  ↑ : 扩大", 20, WHITE),
                ("⊕ : 多球  |  ↓ : 缩小挡板", 20, WHITE),
                ("", 20, WHITE),
                ("游戏模式:", 26, CYAN),
                ("无尽: 生命耗尽结束", 20, WHITE),
                ("限时: 60秒内最高分", 20, WHITE),
                ("挑战: 连续接30球", 20, WHITE),
            ]
            
            for i, (text, size, color) in enumerate(help_texts):
                surf = ResourceCache.get_text_surface(text, size, color)
                screen.blit(surf, (100, 85 + i * 32))
            
            back = ResourceCache.get_text_surface("按 ESC 或 ENTER 返回", 28, LIGHT_GRAY)
            screen.blit(back, (WIDTH // 2 - back.get_width() // 2, HEIGHT - 50))
        except Exception as e:
            print(f"Error in _draw_help: {e}")
            import traceback
            traceback.print_exc()
    
    def _draw_game(self, offset_x=0, offset_y=0):
        self.screen_effects.apply(screen)
        
        screen_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        
        for ball in self.balls:
            if screen_rect.colliderect(ball.rect.inflate(50, 50)):
                ball.draw_trail(screen)
        
        for block in self.blocks:
            screen.blit(block.image, block.rect)
        
        for ball in self.balls:
            screen.blit(ball.image, ball.rect)
        
        self.particles.draw(screen)
        
        paddle_skin = PADDLE_SKINS.get(self.paddle_skin, PADDLE_SKINS["default"])
        self.paddle.draw(screen, has_shield=self.shield, has_rage=self.rage, skin_data=paddle_skin)
        
        self._draw_ui()
        
        if self.state == "countdown":
            self._draw_countdown()
    
    def _draw_ui(self):
        draw_circle = pygame.draw.circle
        
        panel = pygame.Surface((200, 130), pygame.SRCALPHA)
        pygame.draw.rect(panel, (0, 0, 0, 120), panel.get_rect(), border_radius=8)
        pygame.draw.rect(panel, (100, 100, 150, 80), panel.get_rect(), 2, border_radius=8)
        
        score_text = ResourceCache.get_text_surface(f"得分: {self.score}", 24, WHITE)
        panel.blit(score_text, (10, 8))
        
        level_text = ResourceCache.get_text_surface(f"等级: {self.level_system.level}", 20, CYAN)
        panel.blit(level_text, (10, 35))
        
        exp_bar_width = 170
        exp_bar_height = 6
        exp_ratio = self.level_system.exp / self.level_system.exp_to_next
        pygame.draw.rect(panel, (50, 50, 80), (10, 58, exp_bar_width, exp_bar_height), border_radius=3)
        pygame.draw.rect(panel, CYAN, (10, 58, int(exp_bar_width * exp_ratio), exp_bar_height), border_radius=3)
        
        screen.blit(panel, (10, 10))
        
        for i in range(self.max_lives):
            x = WIDTH - 30 - i * 28
            if i < self.lives:
                draw_circle(screen, RED, (x, 30), 10)
                draw_circle(screen, (255, 150, 150), (x - 3, 27), 4)
            else:
                draw_circle(screen, (50, 50, 50), (x, 30), 10)
        
        high_score = self.high_scores.get(self.game_mode, 0)
        high_text = ResourceCache.get_text_surface(f"最高: {high_score}", 18, GOLD)
        screen.blit(high_text, (WIDTH - high_text.get_width() - 20, 55))
        
        fps_text = ResourceCache.get_text_surface(f"FPS: {int(self.fps)}", 14, GREEN)
        screen.blit(fps_text, (10, HEIGHT - 25))
        
        # 游戏模式特定信息
        if self.game_mode == "timed":
            time_text = ResourceCache.get_text_surface(f"时间: {int(self.time_remaining)}s", 26, 
                RED if self.time_remaining < 10 else WHITE)
            screen.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, 15))
        
        if self.game_mode == "challenge":
            progress_text = ResourceCache.get_text_surface(f"进度: {self.challenge_progress}/{self.challenge_goal}", 26, ORANGE)
            screen.blit(progress_text, (WIDTH // 2 - progress_text.get_width() // 2, 15))
        
        if self.combo >= 3:
            combo_color = GOLD if self.combo >= 10 else ORANGE if self.combo >= 5 else WHITE
            combo_text = ResourceCache.get_text_surface(f"COMBO ×{self.combo}", 32, combo_color)
            pulse = 1 + 0.1 * math.sin(pygame.time.get_ticks() / 100)
            scaled = pygame.transform.scale(combo_text, 
                (int(combo_text.get_width() * pulse), int(combo_text.get_height() * pulse)))
            screen.blit(scaled, (WIDTH // 2 - scaled.get_width() // 2, 70))
        
        self._draw_skill_icons()
        
        if self.boss_mode:
            boss_text = ResourceCache.get_text_surface("BOSS战!", 36, RED)
            screen.blit(boss_text, (WIDTH // 2 - boss_text.get_width() // 2, 110))
            
            bar_width = 200
            bar_height = 15
            bar_x = WIDTH // 2 - bar_width // 2
            bar_y = 150
            health_ratio = self.balls.sprites()[0].health / 10 if self.balls else 0
            
            pygame.draw.rect(screen, (80, 0, 0), (bar_x, bar_y, bar_width, bar_height), border_radius=5)
            pygame.draw.rect(screen, RED, (bar_x, bar_y, int(bar_width * health_ratio), bar_height), border_radius=5)
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 2, border_radius=5)
    
    def _draw_skill_icons(self):
        pass
    
    def _draw_countdown(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 100))
        screen.blit(s, (0, 0))
        
        num_text = ResourceCache.get_text_surface(str(self.countdown), 100, GOLD)
        screen.blit(num_text, (WIDTH // 2 - num_text.get_width() // 2, HEIGHT // 2 - 60))
    
    def _draw_game_over(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, (0, 0))
        
        if self.game_mode == "challenge" and self.challenge_progress >= self.challenge_goal:
            title = ResourceCache.get_text_surface("挑战成功!", 60, GOLD)
        else:
            title = ResourceCache.get_text_surface("游戏结束", 60, RED)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 130))
        
        score_text = ResourceCache.get_text_surface(f"最终得分: {self.score}", 36, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 - 50))
        
        mode_key = self.game_mode
        if self.score >= self.high_scores.get(mode_key, 0):
            new_record = ResourceCache.get_text_surface("新纪录!", 32, GOLD)
            screen.blit(new_record, (WIDTH // 2 - new_record.get_width() // 2, HEIGHT // 2))
        
        level_text = ResourceCache.get_text_surface(f"达到等级: {self.level_system.level}", 28, CYAN)
        screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, HEIGHT // 2 + 45))
        
        restart = ResourceCache.get_text_surface("按 SPACE 重新开始 | 按 ESC 返回菜单", 26, LIGHT_GRAY)
        screen.blit(restart, (WIDTH // 2 - restart.get_width() // 2, HEIGHT // 2 + 100))
    
    def _draw_pause(self):
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        screen.blit(s, (0, 0))
        
        pause_text = ResourceCache.get_text_surface("游戏暂停", 50, WHITE)
        screen.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - 40))
        
        hint = ResourceCache.get_text_surface("按 ESC 继续 | 按 Q 返回菜单", 26, LIGHT_GRAY)
        screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 30))
    
    def _key_pressed(self, key):
        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        
        if keys[key]:
            if key in self.key_cooldown:
                if now - self.key_cooldown[key] < 200:
                    return False
            self.key_cooldown[key] = now
            return True
        return False
 
    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        if self.state == "playing":
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.paddle.move(-1)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.paddle.move(1)
            if self._key_pressed(pygame.K_ESCAPE):
                self.state = "paused"
        
        elif self.state == "menu":
            if self._key_pressed(pygame.K_RETURN):
                self.menu_animation.start_fade_out()
                self.pending_state = "mode_select"
            elif self._key_pressed(pygame.K_s):
                self.menu_animation.start_fade_out()
                self.pending_state = "skin_select"
            elif self._key_pressed(pygame.K_h):
                self.menu_animation.start_fade_out()
                self.pending_state = "help"
            elif self._key_pressed(pygame.K_1):
                self.difficulty = "easy"
                self.show_difficulty_notification = True
                self.difficulty_notification_time = pygame.time.get_ticks()
            elif self._key_pressed(pygame.K_2):
                self.difficulty = "normal"
                self.show_difficulty_notification = True
                self.difficulty_notification_time = pygame.time.get_ticks()
            elif self._key_pressed(pygame.K_3):
                self.difficulty = "hard"
                self.show_difficulty_notification = True
                self.difficulty_notification_time = pygame.time.get_ticks()
            
            if keys[pygame.K_RETURN]:
                self.menu_animation.set_hover(0)
            elif keys[pygame.K_s]:
                self.menu_animation.set_hover(1)
            elif keys[pygame.K_h]:
                self.menu_animation.set_hover(2)
            elif keys[pygame.K_1] or keys[pygame.K_2] or keys[pygame.K_3]:
                self.menu_animation.set_hover(3)
        
        elif self.state == "skin_select":
            if self._key_pressed(pygame.K_ESCAPE):
                self.save_skins()
                self.menu_animation.start_fade_out()
                self.pending_state = "menu"
            elif self._key_pressed(pygame.K_TAB):
                self.skin_type = "ball" if self.skin_type == "paddle" else "paddle"
            else:
                skins = PADDLE_SKINS if self.skin_type == "paddle" else BALL_SKINS
                skin_list = list(skins.keys())
                for i in range(len(skin_list)):
                    if self._key_pressed(pygame.K_1 + i):
                        skin_id = skin_list[i]
                        if self.is_skin_unlocked(skin_id, self.skin_type):
                            if self.skin_type == "paddle":
                                self.paddle_skin = skin_id
                            else:
                                self.ball_skin = skin_id
                            self.save_skins()
        
        elif self.state == "mode_select":
            if self._key_pressed(pygame.K_ESCAPE):
                self.menu_animation.start_fade_out()
                self.pending_state = "menu"
            elif self._key_pressed(pygame.K_1):
                self.game_mode = "endless"
                self.reset_game()
                self.state = "countdown"
            elif self._key_pressed(pygame.K_2):
                self.game_mode = "timed"
                self.reset_game()
                self.state = "countdown"
            elif self._key_pressed(pygame.K_3):
                self.game_mode = "challenge"
                self.reset_game()
                self.state = "countdown"
        
        elif self.state == "help":
            if self._key_pressed(pygame.K_ESCAPE) or self._key_pressed(pygame.K_RETURN) or self._key_pressed(pygame.K_h):
                self.menu_animation.start_fade_out()
                self.pending_state = "menu"
        
        elif self.state == "paused":
            if self._key_pressed(pygame.K_ESCAPE):
                self.state = "playing"
            elif self._key_pressed(pygame.K_q):
                self.state = "menu"
        
        elif self.state == "game_over":
            if self._key_pressed(pygame.K_SPACE):
                self.reset_game()
                self.state = "countdown"
            elif self._key_pressed(pygame.K_ESCAPE):
                self.state = "menu"

def main():
    game = Game()
    running = True
    frame_count = 0
    fps_update_interval = 60
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        game.handle_input()
        game.update()
        game.draw()
        
        frame_count += 1
        if frame_count % fps_update_interval == 0:
            game.fps = clock.get_fps()
        
        clock.tick_busy_loop(60)
    
    game.save_high_score()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
