import math
import random
import time
import webbrowser
import json
import pygame

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FPS = 60

BLACK = (0, 0, 0)
DARK_PURPLE = (30, 0, 30)
DARK_GRAY = (10, 10, 10)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 50, 0)
RED = (255, 100, 100)
WHITE = (220, 220, 220)
CYAN = (0, 200, 200)
AMBER = (255, 191, 0)
BRIGHT_GREEN = (100, 255, 100)
MAP_GRAY = (50, 50, 50)
MAP_WALL = (100, 100, 100)
POPUP_BG = (20, 20, 40, 220)

pygame.init()
pygame.mixer.init()

UI_FONT = pygame.font.SysFont("Consolas", 24)
MESSAGE_FONT = pygame.font.SysFont("Consolas", 32)
TERMINAL_FONT = pygame.font.SysFont("Lucida Console", 20)
POPUP_FONT = pygame.font.SysFont("Consolas", 28)
TITLE_FONT = pygame.font.SysFont("Lucida Console", 96)
BUTTON_FONT = pygame.font.SysFont("Consolas", 48)
LEVEL_TITLE_FONT = pygame.font.SysFont("Consolas", 64)
STORY_FONT = pygame.font.SysFont("Consolas", 28)


def wrap_text(text, font, max_width):
    """Wraps a single line of text to a given width."""
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    lines.append(current_line.strip())
    return lines

class WardenManager:
    def __init__(self, game_scene):
        self.game_scene = game_scene
        self.next_event_time = 0
        self.event_cooldown = 15000  # Milliseconds (15 seconds)
        self.current_interference = None # For terminal interference
        self.reset_timer()

    def reset_timer(self):
        """Sets the time for the next Warden event."""
        self.next_event_time = pygame.time.get_ticks() + self.event_cooldown + random.randint(-5000, 5000)

    def update(self):
        now = pygame.time.get_ticks()
        if now > self.next_event_time:
            self.trigger_event()
            self.reset_timer()

    def trigger_event(self):
        """Triggers a random hostile event."""
        events = [self.minor_glitch, self.major_glitch, self.terminal_interference]
        # Make major events rarer if privilege is low
        if self.game_scene.puzzle_manager.get_state('privilege_level') < 1:
            events = [self.minor_glitch]

        chosen_event = random.choice(events)
        chosen_event()

    def minor_glitch(self):
        print("[Warden] Triggering minor glitch.")
        self.game_scene.glitch_manager.trigger_glitch(300, 8)
        self.game_scene.camera.start_shake(300, 2)

    def major_glitch(self):
        print("[Warden] Triggering MAJOR glitch.")
        self.game_scene.popup_manager.add_popup("SYS.SECURITY//: Anomaly Detected.", 2)
        self.game_scene.glitch_manager.trigger_glitch(1200, 20)
        self.game_scene.camera.start_shake(1000, 7)

    def terminal_interference(self):
        """Prepares a message to be injected into the terminal."""
        print("[Warden] Preparing terminal interference.")
        interferences = [
            " [Warden]: You don't belong here.",
            " [Warden]: I SEE YOU.",
            " [Warden]: Deletion imminent."
        ]
        self.current_interference = random.choice(interferences)
        # Give the player a warning
        self.game_scene.popup_manager.add_popup("WARNING: I/O stream corrupted by unknown process.", 3)

class SettingsManager:

    def __init__(self, filepath='settings.json'):
        self.filepath = filepath
        self.defaults = {
            'master_volume': 0.8,
            'music_volume': 0.7,
            'sfx_volume': 1.0,
            'show_map_on_start': True
        }
        self.settings = self.defaults.copy()
        self.load_settings()

    def load_settings(self):
        try:
            with open(self.filepath, 'r') as f:
                loaded_settings = json.load(f)
                self.settings.update(loaded_settings)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Settings file not found or corrupted, creating with defaults.")
            self.save_settings()

    def save_settings(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key):
        return self.settings.get(key, self.defaults.get(key))

    def set(self, key, value):
        self.settings[key] = value

    def reset_to_defaults(self):
        self.settings = self.defaults.copy()
        self.save_settings()


class AssetManager:

    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.load_assets()

    def load_image(self, name, path):
        try:
            self.images[name] = pygame.image.load(path).convert_alpha()
        except pygame.error as e:
            print(f"Warning: Could not load image '{path}': {e}")
            self.images[name] = None

    def load_sound(self, name, path):
        try:
            self.sounds[name] = pygame.mixer.Sound(path)
        except pygame.error as e:
            print(f"Warning: Could not load sound '{path}': {e}")
            self.sounds[name] = None

    def load_assets(self):
        self.load_image("terminal", "assets/images/terminal.png")
        self.load_image("cables", "assets/images/cables.png")
        self.load_image("door_locked", "assets/images/door_locked.png")
        self.load_image("door_unlocked", "assets/images/door_unlocked.png")
        self.load_image("puzzle_terminal_1", "assets/images/puzzle_terminal_1.png")
        self.load_image("puzzle_terminal_2", "assets/images/puzzle_terminal_2.png")
        self.load_image("puzzle_terminal_3", "assets/images/puzzle_terminal_3.png")
        self.load_image("notice", "assets/images/notice.png")
        self.load_image("data_log", "assets/images/data_log.png")
        self.load_image("background", "assets/images/cet.png")
        self.load_sound("walk", "assets/audios/walk.mp3")
        self.load_sound("hum", "assets/audios/hum.mp3")
        self.load_sound("glitch", "assets/audios/glitch.mp3")
        self.load_sound("interact", "assets/audios/interact.mp3")
        self.load_sound("popup", "assets/audios/popup.mp3")
        self.load_sound("key_press", "assets/audios/key_press.mp3")
        self.load_sound("terminal_error", "assets/audios/terminal_error.mp3")
        self.load_sound("override_success", "assets/audios/override_success.mp3")
        self.load_sound("menu_music", "assets/audios/menu.mp3")
        self.load_sound("ambient_music", "assets/audios/ambience.mp3")
        self.load_sound("terminal_music", "assets/audios/terminal_music.mp3")

    def get_image(self, name):
        return self.images.get(name)

    def get_sound(self, name):
        return self.sounds.get(name)

    def play_sound(self, name, channel='sfx', loops=0, fade_ms=0):
        sound = self.get_sound(name)
        if not sound:
            return
        master_vol = settings.get('master_volume')
        if channel == 'music':
            channel_vol = settings.get('music_volume')
        else:
            channel_vol = settings.get('sfx_volume')
        final_vol = master_vol * channel_vol
        sound.set_volume(final_vol)
        sound.play(loops=loops, fade_ms=fade_ms)


assets = None
settings = None


class PopupManager:

    def __init__(self):
        self.popups = []

    def add_popup(self, text, duration_seconds):
        assets.play_sound("popup")
        end_time = pygame.time.get_ticks() + duration_seconds * 1000
        lines = []
        words = text.split(' ')
        current_line = ""
        max_width = SCREEN_WIDTH * 0.6
        for word in words:
            test_line = current_line + word + " "
            if POPUP_FONT.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(POPUP_FONT.render(current_line, True, WHITE))
                current_line = word + " "
        lines.append(POPUP_FONT.render(current_line, True, WHITE))
        total_height = sum(line.get_height() for line in lines)
        max_line_width = max(line.get_width() for line in lines) if lines else 0
        padding = 40
        bg_width = max_line_width + padding * 2
        bg_height = total_height + padding * 2
        bg_surf = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surf.fill(POPUP_BG)
        current_y = padding
        for line in lines:
            line_rect = line.get_rect(centerx=bg_width / 2, top=current_y)
            bg_surf.blit(line, line_rect)
            current_y += line.get_height()
        bg_rect = bg_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.popups.append({'surface': bg_surf, 'rect': bg_rect, 'end_time': end_time})

    def update(self):
        current_time = pygame.time.get_ticks()
        self.popups = [p for p in self.popups if p['end_time'] > current_time]

    def draw(self, surface):
        for popup in self.popups:
            surface.blit(popup['surface'], popup['rect'])


class GameStateManager:
    def __init__(self, initial_state):
        self.states = {}
        self.current_state_name = initial_state
        self.current_state = None

    def add_state(self, state_name, state_instance):
        self.states[state_name] = state_instance

    def set_state(self, state_name):
        if self.current_state: self.current_state.on_exit()
        self.current_state_name = state_name
        self.current_state = self.states[state_name]
        self.current_state.on_enter()

    def handle_events(self, events): self.current_state.handle_events(events)

    def update(self): self.current_state.update()

    def draw(self, surface): self.current_state.draw(surface)


class BaseState:
    def __init__(self): pass

    def on_enter(self): pass

    def on_exit(self):
        pygame.mixer.stop()

    def handle_events(self, events): pass

    def update(self): pass

    def draw(self, surface): pass


class GlitchManager:
    def __init__(self):
        self.glitches = []
        self.active = False
        self.chromatic_offset_x = 0
        self.chromatic_offset_y = 0
        self.scanline_alpha = 0

    def trigger_glitch(self, duration_ms, intensity):
        end_time = pygame.time.get_ticks() + duration_ms
        self.glitches.append({'end_time': end_time, 'intensity': intensity})
        self.active = True
        assets.play_sound("glitch")

    def update(self):
        current_time = pygame.time.get_ticks()
        self.glitches = [g for g in self.glitches if g['end_time'] > current_time]
        self.active = bool(self.glitches)

        if self.active:

            max_intensity = max(g['intensity'] for g in self.glitches)

            self.chromatic_offset_x = random.randint(-max_intensity // 5,
                                                     max_intensity // 5) if random.random() < 0.7 else 0
            self.chromatic_offset_y = random.randint(-max_intensity // 5,
                                                     max_intensity // 5) if random.random() < 0.7 else 0

            self.scanline_alpha = min(100, max_intensity * 5)
        else:
            self.chromatic_offset_x = 0
            self.chromatic_offset_y = 0
            self.scanline_alpha = max(0, self.scanline_alpha - 5)

    def draw(self, surface):
        if not self.active and self.scanline_alpha == 0: return

        if self.chromatic_offset_x != 0 or self.chromatic_offset_y != 0:
            temp_surf = surface.copy()
            surface.fill(BLACK)

            surface.blit(temp_surf, (self.chromatic_offset_x, self.chromatic_offset_y),
                         special_flags=pygame.BLEND_RGB_ADD)

            surface.blit(temp_surf, (-self.chromatic_offset_x, -self.chromatic_offset_y),
                         special_flags=pygame.BLEND_RGB_SUB)

        if self.active:
            intensity = max(g['intensity'] for g in self.glitches) if self.glitches else 0
            for _ in range(intensity // 3):
                slice_height = random.randint(1, 3)
                y = random.randint(0, SCREEN_HEIGHT - slice_height)
                slice_rect = pygame.Rect(0, y, SCREEN_WIDTH, slice_height)
                if not surface.get_locked():
                    try:
                        subsurface = surface.subsurface(slice_rect).copy()
                        offset = random.randint(-15, 15)
                        surface.blit(subsurface, (offset, y))
                    except ValueError:

                        pass

        if self.scanline_alpha > 0:
            scanline_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for y in range(0, SCREEN_HEIGHT, 4):
                pygame.draw.line(scanline_surf, (0, 0, 0, 50), (0, y), (SCREEN_WIDTH, y))
            scanline_surf.set_alpha(self.scanline_alpha)
            surface.blit(scanline_surf, (0, 0))


class Camera:
    def __init__(self, width, height):
        self.rect = pygame.Rect(0, 0, width, height)
        self.shake_intensity = 0
        self.shake_duration = 0
        self.shake_start_time = 0

    def apply(self, entity_rect):
        return entity_rect.move(self.rect.topleft)

    def start_shake(self, duration_ms, intensity):
        self.shake_duration = duration_ms
        self.shake_intensity = intensity
        self.shake_start_time = pygame.time.get_ticks()

    def update(self, target):
        x = -target.rect.centerx + SCREEN_WIDTH // 2
        y = -target.rect.centery + SCREEN_HEIGHT // 2
        if self.shake_duration > 0 and self.shake_start_time > 0:
            elapsed = pygame.time.get_ticks() - self.shake_start_time
            if elapsed > self.shake_duration:
                self.shake_duration = 0
                self.shake_intensity = 0
            else:
                x += random.randint(-self.shake_intensity, self.shake_intensity)
                y += random.randint(-self.shake_intensity, self.shake_intensity)
        self.rect.topleft = (x, y)


class PuzzleManager:
    def __init__(self):
        self.state = {
            "power_restored": False, "door_unlocked": False, "privilege_level": 0,
            "chai_riddle_solved": False, "sgpa_riddle_solved": False, "landmark_riddle_solved": False,
        }

    def set_state(self, key, value):
        if key not in self.state or self.state[key] != value:
            print(f"[PuzzleManager] State change: {key} -> {value}")
            self.state[key] = value

    def get_state(self, key): return self.state.get(key, None)

    def increment_privilege(self):
        self.state["privilege_level"] += 1
        print(f"[PuzzleManager] Privilege level increased to: {self.state['privilege_level']}")


class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, name="", image=None):
        super().__init__()
        self.name = name
        self.image = image
        if image:
            self.image = pygame.transform.scale(image, (w, h))
        else:
            self.image = pygame.Surface((w, h))
            self.image.fill(DARK_PURPLE)
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface, camera, puzzle_manager=None):
        surface.blit(self.image, camera.apply(self.rect))


class Player(Entity):
    def __init__(self, x, y):
        size = 32
        super().__init__(x, y, size, size, name="player")

        self.animation_timer = 0
        self.animation_speed = 0.2
        self.bob_height = 2

        self.speed = 5
        self.dx, self.dy = 0, 0
        self.is_walking = False

        self.image = pygame.Surface((size, size), pygame.SRCALPHA)

        pygame.draw.circle(self.image, CYAN, (size // 2, size // 2), size // 2)

        self.speed = 5
        self.dx, self.dy = 0, 0
        self.is_walking = False

    def update(self, walls):
        self.get_input()
        self.move(walls)
        self.update_sound()

    def animate(self):
        if self.is_walking:
            self.animation_timer += self.animation_speed
            offset_y = int(math.sin(self.animation_timer) * self.bob_height)

            animated_image = pygame.Surface(self.base_image.get_size(), pygame.SRCALPHA)
            animated_image.blit(self.base_image, (0, offset_y))
            self.image = animated_image
        else:
            self.animation_timer = 0
            self.image = self.base_image

    def get_input(self):
        keys = pygame.key.get_pressed()
        self.dx, self.dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: self.dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.dx += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]: self.dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: self.dy += self.speed

    def update_sound(self):
        is_moving_now = self.dx != 0 or self.dy != 0
        if is_moving_now and not self.is_walking:
            self.is_walking = True
            assets.play_sound("walk", loops=-1)
        elif not is_moving_now and self.is_walking:
            self.is_walking = False
            sound = assets.get_sound("walk")
            if sound: sound.stop()

    def stop_sound(self):
        if self.is_walking:
            self.is_walking = False
            sound = assets.get_sound("walk")
            if sound: sound.stop()

    def move(self, collidables):
        self.rect.x += self.dx
        self.check_collision('x', collidables)
        self.rect.y += self.dy
        self.check_collision('y', collidables)

    def check_collision(self, direction, collidables):
        for entity in collidables:
            if self.rect.colliderect(entity.rect):
                if direction == 'x':
                    if self.dx > 0: self.rect.right = entity.rect.left
                    if self.dx < 0: self.rect.left = entity.rect.right
                if direction == 'y':
                    if self.dy > 0: self.rect.bottom = entity.rect.top
                    if self.dy < 0: self.rect.top = entity.rect.bottom

    def draw(self, surface, camera):
        surface.blit(self.image, camera.apply(self.rect))


class Wall(Entity):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h, "wall")


class InteractiveObject(Entity):
    def get_interaction_message(self, puzzle_manager): return f"It's a {self.name}."

    def interact(self, game_state_manager, puzzle_manager): print(f"Interacted with {self.name}")


class NoticeBoard(InteractiveObject):
    def __init__(self, x, y, w, h, message, image=None):
        super().__init__(x, y, w, h, "notice board", image=image)
        self.message = message

    def get_interaction_message(self, puzzle_manager):
        return "> An old, dusty notice board. [E] to read."

    def interact(self, game_state_manager, puzzle_manager):
        game_state_manager.current_state.popup_manager.add_popup(self.message, 6)


class CorruptedDataLog(InteractiveObject):
    def __init__(self, x, y, w, h, message, image=None):
        super().__init__(x, y, w, h, "corrupted data log", image=image)
        self.message = message

    def get_interaction_message(self, puzzle_manager):
        return "> A data log, flickering erratically. [E] to examine."

    def interact(self, game_state_manager, puzzle_manager):
        game_state_manager.current_state.popup_manager.add_popup(self.message, 5)
        game_state_manager.current_state.glitch_manager.trigger_glitch(500, 10)


class PuzzleTerminal(InteractiveObject):
    def __init__(self, x, y, w, h, name, puzzle_id, question, answer, image=None):
        super().__init__(x, y, w, h, name, image=image)
        self.puzzle_id, self.question, self.answer = puzzle_id, question, answer

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state(f"{self.puzzle_id}_solved"): return f"The {self.name} is offline."
        return f"> A flickering {self.name}. [E] to read."

    def interact(self, game_state_manager, puzzle_manager):
        if not puzzle_manager.get_state(f"{self.puzzle_id}_solved"):
            game_state_manager.current_state.popup_manager.add_popup(
                f"{self.question} The answer is the override code.", 8)


class Door(InteractiveObject):
    def __init__(self, x, y, w, h, image_locked=None, image_unlocked=None):
        super().__init__(x, y, w, h, name="door")
        self.image_locked = pygame.transform.scale(image_locked, (w, h)) if image_locked else None
        self.image_unlocked = pygame.transform.scale(image_unlocked, (w, h)) if image_unlocked else None
        self.image = self.image_locked
        if not self.image: self.image = pygame.Surface((w, h))
        self.rect = self.image.get_rect(topleft=(x, y))

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state("door_unlocked"): return "The door is unlocked. [E] to leave."
        return "> It's locked. A digital keypad is dark."

    def interact(self, game_state_manager, puzzle_manager):
        if puzzle_manager.get_state("door_unlocked"): game_state_manager.current_state.level_manager.next_level()

    def draw(self, surface, camera, puzzle_manager):
        is_unlocked = puzzle_manager.get_state("door_unlocked")
        current_image = self.image_unlocked if is_unlocked and self.image_unlocked else self.image_locked
        if current_image:
            surface.blit(current_image, camera.apply(self.rect))
        else:
            color = BRIGHT_GREEN if is_unlocked else DARK_PURPLE
            pygame.draw.rect(surface, color, camera.apply(self.rect))


class Terminal(InteractiveObject):
    def __init__(self, x, y, w, h, image=None):
        super().__init__(x, y, w, h, "old terminal", image=image)

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state("power_restored"): return "The terminal hums with power. [E] to access."
        return "> The screen is dead. Power seems to be out."

    def interact(self, game_state_manager, puzzle_manager):
        if puzzle_manager.get_state("power_restored"):
            game_state_manager.set_state("TERMINAL")
        else:
            game_state_manager.current_state.popup_manager.add_popup("No power to the terminal.", 2)


class PowerCable(InteractiveObject):
    def __init__(self, x, y, w, h, image=None):
        super().__init__(x, y, w, h, "pile of cables", image=image)

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state("power_restored"): return "The cables are connected to the backup generator."
        return "> A tangled mess. One seems to lead to a backup generator. [E] to connect."

    def interact(self, game_state_manager, puzzle_manager):
        if not puzzle_manager.get_state("power_restored"):
            puzzle_manager.set_state("power_restored", True)
            game_state_manager.current_state.popup_manager.add_popup(
                "You connected the main cable. A low hum fills the room.", 4)
            game_state_manager.current_state.glitch_manager.trigger_glitch(1000, 15)
            game_state_manager.current_state.camera.start_shake(1000, 5)
            assets.play_sound("hum", loops=-1)


class StoryState(BaseState):
    """Displays the introductory story text with a typewriter effect."""

    def __init__(self, state_manager, next_state):
        super().__init__()
        self.state_manager = state_manager
        self.next_state = next_state

        unwrapped_lines = [
            "The last thing I remember is the smell of ozone.",
            "I was in the new Quantum AI Lab, pushing the final simulation for Project Chimera.",
            "There was a flash. A sound like tearing metal.",
            "...",
            "Now... I'm still in the lab, but it's wrong. The air hums. The walls flicker. This isn't real.",
            "I'm trapped inside. The system is unstable.",
            "A terminal message flickers:",
            "> KERNEL PANIC. SIMULATION DEGRADING.",
            "> ESCAPE IS NOT AN OPTION.",
            "> MANUAL REBOOT REQUIRED: ROOT ACCESS (PRIVILEGE 3/3)",
            "",
            "I have to get admin rights and reboot, or I'll be deleted with the rest of this collapsing reality."
        ]

        self.story_lines = []
        for line in unwrapped_lines:
            self.story_lines.extend(wrap_text(line, STORY_FONT, SCREEN_WIDTH * 0.8))

        self.skip_prompt = UI_FONT.render("> Press any key to speed up / skip...", True, AMBER)
        self.typing_delay = 50
        self.line_pause = 500

    def on_enter(self):
        self.current_line_index = 0
        self.current_char_index = 0
        self.last_update = pygame.time.get_ticks()
        self.state = "TYPING"

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.state_manager.set_state(self.next_state)

    def update(self):
        now = pygame.time.get_ticks()

        if self.state == "TYPING":
            if now - self.last_update > self.typing_delay:
                self.last_update = now

                line_len = len(self.story_lines[self.current_line_index])
                if self.current_char_index < line_len:
                    self.current_char_index += 1
                    if self.story_lines[self.current_line_index][self.current_char_index - 1] != ' ':
                        assets.play_sound('key_press')
                else:
                    self.state = "PAUSED"
                    self.last_update = now

        elif self.state == "PAUSED":
            if now - self.last_update > self.line_pause:
                self.current_line_index += 1
                self.current_char_index = 0
                if self.current_line_index >= len(self.story_lines):
                    self.state_manager.set_state(self.next_state)
                else:
                    self.state = "TYPING"

    def draw(self, surface):
        surface.fill(BLACK)
        y_pos = 100

        for i in range(self.current_line_index):
            rendered_line = STORY_FONT.render(self.story_lines[i], True, WHITE)
            rect = rendered_line.get_rect(centerx=SCREEN_WIDTH / 2, y=y_pos)
            surface.blit(rendered_line, rect)
            y_pos += 40

        if self.current_line_index < len(self.story_lines):
            typing_line_text = self.story_lines[self.current_line_index][:self.current_char_index]
            rendered_typing_line = STORY_FONT.render(typing_line_text, True, WHITE)
            rect = rendered_typing_line.get_rect(centerx=SCREEN_WIDTH / 2, y=y_pos)
            surface.blit(rendered_typing_line, rect)

        prompt_rect = self.skip_prompt.get_rect(centerx=SCREEN_WIDTH / 2, bottom=SCREEN_HEIGHT - 40)
        surface.blit(self.skip_prompt, prompt_rect)


class LevelIntroState(BaseState):
    """Displays story text before a level starts."""

    def __init__(self, state_manager, level_manager):
        super().__init__()
        self.state_manager = state_manager
        self.level_manager = level_manager
        self.typing_delay = 50

    def on_enter(self):
        level_index = self.level_manager.current_level_index
        self.level_title = self.level_manager.level_themes[level_index]
        story_text = level_story_intros[level_index]

        self.wrapped_story_lines = wrap_text(story_text, STORY_FONT, SCREEN_WIDTH * 0.9)
        self.level_title_surf = LEVEL_TITLE_FONT.render(self.level_title, True, WHITE)

        self.char_index = 0
        self.line_index = 0
        self.last_update = pygame.time.get_ticks()
        self.finished_typing = False

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if not self.finished_typing:
                    self.finished_typing = True
                else:
                    self.state_manager.set_state("GAME")

    def update(self):
        if self.finished_typing:
            return

        now = pygame.time.get_ticks()
        if now - self.last_update > self.typing_delay:
            self.last_update = now

            if self.line_index < len(self.wrapped_story_lines):
                current_line_len = len(self.wrapped_story_lines[self.line_index])
                if self.char_index < current_line_len:
                    self.char_index += 1
                    if self.wrapped_story_lines[self.line_index][self.char_index - 1] != ' ':
                        assets.play_sound('key_press')
                else:
                    self.line_index += 1
                    self.char_index = 0
            else:
                self.finished_typing = True

    def draw(self, surface):
        surface.fill(BLACK)
        title_rect = self.level_title_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 80))
        surface.blit(self.level_title_surf, title_rect)

        y_pos = SCREEN_HEIGHT / 2

        if self.finished_typing:
            for line in self.wrapped_story_lines:
                story_surf = STORY_FONT.render(line, True, CYAN)
                story_rect = story_surf.get_rect(center=(SCREEN_WIDTH / 2, y_pos))
                surface.blit(story_surf, story_rect)
                y_pos += 40
        else:

            for i in range(self.line_index):
                story_surf = STORY_FONT.render(self.wrapped_story_lines[i], True, CYAN)
                story_rect = story_surf.get_rect(center=(SCREEN_WIDTH / 2, y_pos))
                surface.blit(story_surf, story_rect)
                y_pos += 40

            if self.line_index < len(self.wrapped_story_lines):
                sub_text = self.wrapped_story_lines[self.line_index][:self.char_index]
                story_surf = STORY_FONT.render(sub_text, True, CYAN)
                story_rect = story_surf.get_rect(center=(SCREEN_WIDTH / 2, y_pos))
                surface.blit(story_surf, story_rect)


class LevelManager:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.levels = [level_1_data, level_2_data, level_3_data, level_4_data, level_5_data]
        self.level_themes = [
            "Chapter 1: The Quantum Lab", "Chapter 2: The Digital Archives", "Chapter 3: The Network Hub",
            "Chapter 4: The Warden's Core", "Chapter 5: The System Kernel"
        ]
        self.current_level_index = 0

    def load_level(self, level_data):
        puzzle_manager = PuzzleManager()
        game_scene = GameScene(self.state_manager, puzzle_manager, self, level_data,
                               self.level_themes[self.current_level_index])
        self.state_manager.add_state("GAME", game_scene)
        terminal_files = level_data.get("terminal_files", {})
        terminal_scene = TerminalState(self.state_manager, puzzle_manager, level_data["puzzles"], terminal_files)
        self.state_manager.add_state("TERMINAL", terminal_scene)
        self.state_manager.set_state("LEVEL_INTRO")

    def start_new_game(self):
        self.current_level_index = 0
        self.load_level(self.levels[self.current_level_index])

    def load_specific_level(self, level_index):
        if 0 <= level_index < len(self.levels):
            self.current_level_index = level_index
            self.load_level(self.levels[self.current_level_index])
        else:
            print(f"Error: Level index {level_index} is out of bounds.")

    def next_level(self):
        self.current_level_index += 1
        if self.current_level_index < len(self.levels):
            self.load_level(self.levels[self.current_level_index])
        else:
            self.state_manager.set_state("WIN")


class GameScene(BaseState):
    def __init__(self, state_manager, puzzle_manager, level_manager, level_data, level_title):
        super().__init__()
        self.state_manager, self.puzzle_manager, self.level_manager = state_manager, puzzle_manager, level_manager
        self.glitch_manager, self.camera, self.popup_manager = GlitchManager(), Camera(SCREEN_WIDTH,
                                                                                       SCREEN_HEIGHT), PopupManager()
        self.show_map = settings.get('show_map_on_start')
        self.player = Player(level_data["player"]["start_pos"][0], level_data["player"]["start_pos"][1])
        self.level_title = level_title
        self.interactives = []
        for obj_data in level_data["objects"]:
            obj_type, x, y, w, h = obj_data["type"], obj_data["x"], obj_data["y"], obj_data["w"], obj_data["h"]
            if obj_type == "Terminal":
                self.interactives.append(Terminal(x, y, w, h, image=assets.get_image(obj_data["image_key"])))
            elif obj_type == "PowerCable":
                self.interactives.append(PowerCable(x, y, w, h, image=assets.get_image(obj_data["image_key"])))
            elif obj_type == "Door":
                self.interactives.append(Door(x, y, w, h, image_locked=assets.get_image(obj_data["image_locked_key"]),
                                              image_unlocked=assets.get_image(obj_data["image_unlocked_key"])))
            elif obj_type == "PuzzleTerminal":
                p_info = level_data["puzzles"][obj_data["puzzle_key"]]
                self.interactives.append(
                    PuzzleTerminal(x, y, w, h, obj_data["name"], p_info["id"], p_info["question"], p_info["answer"],
                                   image=assets.get_image(obj_data["image_key"])))
            elif obj_type == "NoticeBoard":
                self.interactives.append(
                    NoticeBoard(x, y, w, h, obj_data["message"], image=assets.get_image(obj_data["image_key"])))
            elif obj_type == "CorruptedDataLog":
                self.interactives.append(
                    CorruptedDataLog(x, y, w, h, obj_data["message"], image=assets.get_image(obj_data["image_key"])))
        self.walls, self.flicker_timer, self.interaction_message = [Wall(w[0], w[1], w[2], w[3]) for w in
                                                                    level_data["walls"]], 0, ""

    def on_enter(self):
        assets.play_sound("ambient_music", channel='music', loops=-1, fade_ms=1000)
        if self.puzzle_manager.get_state("power_restored"):
            assets.play_sound("hum", loops=-1)

    def on_exit(self):
        self.player.stop_sound()
        sound = assets.get_sound("hum")
        if sound: sound.stop()
        music = assets.get_sound("ambient_music")
        if music: music.fadeout(500)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e: self.try_interact()
                if event.key == pygame.K_m: self.show_map = not self.show_map

    def try_interact(self):
        for obj in self.interactives:
            if self.player.rect.colliderect(obj.rect.inflate(20, 20)):
                assets.play_sound("interact")
                obj.interact(self.state_manager, self.puzzle_manager)
                return

    def update(self):
        self.player.update(self.walls)
        self.camera.update(self.player)
        self.glitch_manager.update()
        self.popup_manager.update()
        prompt = ""
        for obj in self.interactives:
            if self.player.rect.colliderect(obj.rect.inflate(20, 20)):
                prompt = obj.get_interaction_message(self.puzzle_manager)
                break
        self.interaction_message = prompt

    def draw(self, surface):
        self.flicker_timer = (self.flicker_timer + 1) % 60
        surface.fill(DARK_GRAY if self.flicker_timer < 50 else DARK_PURPLE)
        for entity in self.walls + self.interactives: entity.draw(surface, self.camera, self.puzzle_manager)
        self.player.draw(surface, self.camera)
        self.glitch_manager.draw(surface)
        self.popup_manager.draw(surface)
        if self.interaction_message:
            surface.blit(UI_FONT.render(self.interaction_message, True, WHITE), (20, SCREEN_HEIGHT - 40))
        surface.blit(UI_FONT.render("[M] Map", True, WHITE), (SCREEN_WIDTH - 120, 20))
        if self.show_map: self.draw_map(surface)

    def draw_map(self, surface):
        map_surf = pygame.Surface((250, 150))
        map_surf.fill(MAP_GRAY)
        map_surf.set_alpha(200)
        all_rects = [w.rect for w in self.walls] + [p.rect for p in self.interactives]
        if not all_rects: return
        min_x, max_x = min(r.left for r in all_rects), max(r.right for r in all_rects)
        min_y, max_y = min(r.top for r in all_rects), max(r.bottom for r in all_rects)
        world_w, world_h = max_x - min_x, max_y - min_y
        if world_w == 0 or world_h == 0: return
        scale = min(250 / world_w, 150 / world_h)

        def scale_rect(rect):
            return pygame.Rect((rect.x - min_x) * scale, (rect.y - min_y) * scale, rect.w * scale, rect.h * scale)

        for wall in self.walls: pygame.draw.rect(map_surf, MAP_WALL, scale_rect(wall.rect))
        for obj in self.interactives:
            color = AMBER
            if isinstance(obj, Door): color = BRIGHT_GREEN
            if isinstance(obj, Terminal): color = WHITE
            pygame.draw.rect(map_surf, color, scale_rect(obj.rect))
        pygame.draw.rect(map_surf, CYAN, scale_rect(self.player.rect))
        surface.blit(map_surf, (SCREEN_WIDTH - 270, 60))


class TerminalState(BaseState):
    def __init__(self, state_manager, puzzle_manager, puzzles_data, terminal_files):
        super().__init__()
        self.state_manager, self.puzzle_manager, self.puzzles, self.files = state_manager, puzzle_manager, puzzles_data, terminal_files
        self.input_text, self.output_lines, self.command_history, self.history_index = "", [], [], -1
        self.cursor_visible, self.cursor_timer = True, 0
        self.typewriter_effect = {"text": "", "pos": 0, "lines": [], "start_time": 0}
        self.transition_alpha, self.transition_state = 255, "in"

    def on_enter(self):
        self.transition_alpha, self.transition_state = 255, "in"
        self.input_text, self.output_lines, self.command_history, self.history_index = "", [], [], -1
        assets.play_sound("terminal_music", channel='music', loops=-1, fade_ms=500)
        boot_sequence = ["CET OS v1.3a [Kernel: GL-0xDEADBEEF]", "...", "System Integrity Check... FAILED.",
                         "Memory Corruption Detected.",
                         f"User privilege level: {self.puzzle_manager.get_state('privilege_level')}",
                         "Type 'help' for a list of commands."]
        self.add_output_multiline(boot_sequence)

    def on_exit(self):
        music = assets.get_sound("terminal_music")
        if music: music.fadeout(500)

    def _wrap_text(self, text, font, max_width):
        words, lines, current_line = text.split(' '), [], ""
        for word in words:
            if font.size(current_line + word)[0] <= max_width:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())
        return lines

    def add_output(self, text, instant=False):
        wrapped_lines = [line for single_line in text.split('\n') for line in
                         self._wrap_text(single_line, TERMINAL_FONT, SCREEN_WIDTH - 40)]
        if instant:
            self.output_lines.extend(wrapped_lines)
        else:
            self.typewriter_effect = {"text": "", "pos": 0, "lines": wrapped_lines, "start_time": time.time()}

    def add_output_multiline(self, lines_list):
        self.typewriter_effect = {"text": "", "pos": 0, "lines": lines_list, "start_time": time.time()}

    def handle_events(self, events):
        if self.transition_state != 'active': return
        if self.typewriter_effect["lines"]:
            if any(e.type == pygame.KEYDOWN for e in events): self.finish_typewriter()
            return
        for event in events:
            if event.type == pygame.KEYDOWN:
                assets.play_sound("key_press")
                if event.key == pygame.K_RETURN:
                    if self.input_text.strip(): self.command_history.insert(0, self.input_text); self.history_index = -1
                    self.process_command()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.transition_state = "out"
                elif event.key == pygame.K_UP:
                    if self.history_index < len(self.command_history) - 1: self.history_index += 1; self.input_text = \
                        self.command_history[self.history_index]
                elif event.key == pygame.K_DOWN:
                    if self.history_index > 0:
                        self.history_index -= 1
                        self.input_text = self.command_history[self.history_index]
                    else:
                        self.history_index = -1
                        self.input_text = ""
                else:
                    self.input_text += event.unicode

    def process_command(self):
        full_command, self.input_text = self.input_text.lower().strip(), ""
        self.add_output(f"> {full_command}", instant=True)
        parts = full_command.split()
        command = parts[0] if parts else ""
        if not command: return
        if command == "help":
            self.add_output("Available Commands:\n  status\n  unlock\n  override <code>\n  ls\n  cat <file>\n  exit",
                            instant=True)
        elif command == "status":
            priv, door = self.puzzle_manager.get_state('privilege_level'), "UNLOCKED" if self.puzzle_manager.get_state(
                "door_unlocked") else "LOCKED"
            self.add_output(f"Privilege: {priv}/3. Main Door: {door}. Network: OFFLINE.")
        elif command == "unlock":
            if self.puzzle_manager.get_state('privilege_level') >= 3:
                self.add_output("Privilege accepted. Unlocking door...")
                self.puzzle_manager.set_state("door_unlocked", True)
                assets.play_sound("override_success")
            else:
                self.add_output("ERROR: Insufficient privileges. Level 3 required.")
                assets.play_sound(
                    "terminal_error")
        elif command == "override":
            if len(parts) > 1:
                code, found = parts[1], False
                for puzzle in self.puzzles.values():
                    if code == puzzle["answer"]:
                        found = True
                        if not self.puzzle_manager.get_state(f"{puzzle['id']}_solved"):
                            self.puzzle_manager.set_state(f"{puzzle['id']}_solved", True)
                            self.puzzle_manager.increment_privilege()
                            self.add_output("Override code accepted. Privilege level increased.")
                            assets.play_sound("override_success")
                        else:
                            self.add_output("Code already used. No effect.")
                        break
                if not found: self.add_output("ERROR: Invalid override code."); assets.play_sound("terminal_error")
            else:
                self.add_output("Usage: override <CODE>")
                assets.play_sound("terminal_error")
        elif command == "ls":
            self.add_output(" ".join(self.files.keys()) if self.files else "No files found.")
        elif command == "cat":
            if len(parts) > 1:
                filename = parts[1]
                if filename in self.files:
                    self.add_output(self.files[filename], instant=True)
                else:
                    self.add_output(f"ERROR: File not found: '{filename}'")
                    assets.play_sound("terminal_error")
            else:
                self.add_output("Usage: cat <filename>")
                assets.play_sound("terminal_error")
        elif command == "exit":
            self.transition_state = "out"
        else:
            self.add_output(f"Command not recognized: '{command}'.")
            assets.play_sound("terminal_error")

    def finish_typewriter(self):
        self.output_lines.extend(self.typewriter_effect["lines"])
        self.typewriter_effect["lines"] = []

    def update(self):
        if self.transition_state == 'in':
            self.transition_alpha = max(0, self.transition_alpha - 15)
            if self.transition_alpha == 0: self.transition_state = 'active'
        elif self.transition_state == 'out':
            self.transition_alpha = min(255, self.transition_alpha + 15)
            if self.transition_alpha == 255: self.state_manager.set_state("GAME")
        if self.transition_state != 'active': return
        self.cursor_timer = (self.cursor_timer + 1) % FPS
        self.cursor_visible = self.cursor_timer < FPS // 2
        if self.typewriter_effect["lines"]:
            effect = self.typewriter_effect
            if (time.time() - effect["start_time"]) * 10 > len(self.output_lines) - (len(effect["lines"])):
                if effect["lines"]: self.output_lines.append(effect["lines"].pop(0))

    def render_text_glow(self, text, color, pos, surface):
        text_surf = TERMINAL_FONT.render(text, True, color)
        blur_surf = TERMINAL_FONT.render(text, True, tuple(c * 0.5 for c in color))
        blur_surf.set_alpha(100)
        surface.blit(blur_surf, (pos[0] + 1, pos[1] + 1))
        surface.blit(blur_surf, (pos[0] - 1, pos[1] - 1))
        surface.blit(text_surf, pos)

    def draw(self, surface):
        surface.fill(BLACK)
        for y in range(0, SCREEN_HEIGHT, 4): pygame.draw.line(surface, DARK_GREEN, (0, y), (SCREEN_WIDTH, y))
        y_pos, max_lines = 20, (SCREEN_HEIGHT - 60) // (TERMINAL_FONT.get_height() + 5)
        start_index = max(0, len(self.output_lines) - max_lines)
        for line_text in self.output_lines[start_index:]:
            self.render_text_glow(line_text, GREEN, (20, y_pos), surface)
            y_pos += TERMINAL_FONT.get_height() + 5
        if not self.typewriter_effect["lines"]:
            prompt_text = f"> {self.input_text}"
            self.render_text_glow(prompt_text, GREEN, (20, y_pos), surface)
            if self.cursor_visible:
                cursor_x = 20 + TERMINAL_FONT.size(prompt_text)[0]
                pygame.draw.rect(surface, GREEN, pygame.Rect(cursor_x + 2, y_pos, 10, TERMINAL_FONT.get_height()))
        if self.transition_alpha > 0:
            fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surf.fill(BLACK)
            fade_surf.set_alpha(self.transition_alpha)
            surface.blit(fade_surf, (0, 0))


class MenuState(BaseState):

    def __init__(self, state_manager, level_manager):
        super().__init__()
        self.state_manager, self.level_manager = state_manager, level_manager
        self.title_text = TITLE_FONT.render("CET GLITCH", True, GREEN)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.button_texts = ["> Start Game", "> Instructions", "> Settings", "> GitHub", "> Quit"]
        self.buttons, self.github_url = {}, "https://github.com/rohankishore/CETGlitch"

        self.glitch_timer, self.glitch_offset = 0, (0, 0)

        self.fade_alpha = 255
        self.fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_surface.fill(BLACK)

        y_pos = 300
        for text in self.button_texts:
            rect = BUTTON_FONT.render(text, True, WHITE).get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            self.buttons[text] = rect
            y_pos += 70
        raw_bg = assets.get_image("background")
        self.background_image = pygame.transform.scale(raw_bg, (SCREEN_WIDTH, SCREEN_HEIGHT)) if raw_bg else None

    def on_enter(self):
        self.fade_alpha = 255
        assets.play_sound("menu_music", channel='music', loops=-1, fade_ms=1000)

    def on_exit(self):
        music = assets.get_sound("menu_music")
        if music: music.fadeout(500)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for text, rect in self.buttons.items():
                    if rect.collidepoint(event.pos): self.handle_button_click(text)
            if event.type == pygame.KEYDOWN:
                level_keys = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4}
                if event.key in level_keys: self.level_manager.load_specific_level(level_keys[event.key])

    def handle_button_click(self, text):
        if text == "> Start Game":
            self.level_manager.start_new_game()
        elif text == "> Instructions":
            self.state_manager.set_state("INSTRUCTIONS")
        elif text == "> Settings":
            self.state_manager.set_state("SETTINGS")
        elif text == "> GitHub":
            webbrowser.open(self.github_url)
        elif text == "> Quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self):

        self.glitch_timer += 1
        if self.glitch_timer % 10 == 0: self.glitch_offset = (random.randint(-4, 4), random.randint(-4, 4))
        if self.glitch_timer > 60 and random.random() < 0.95: self.glitch_offset = (0, 0)
        if self.glitch_timer > 120: self.glitch_timer = 0

        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 5)

    def draw(self, surface):
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(BLACK)

        title_pos = (self.title_rect.x + self.glitch_offset[0], self.title_rect.y + self.glitch_offset[1])
        surface.blit(self.title_text, title_pos)

        for text, rect in self.buttons.items():
            color = AMBER if rect.collidepoint(pygame.mouse.get_pos()) else WHITE
            surface.blit(BUTTON_FONT.render(text, True, color), rect)

        if self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            surface.blit(self.fade_surface, (0, 0))


class InstructionsState(BaseState):
    def __init__(self, state_manager):
        super().__init__()
        self.state_manager = state_manager
        self.title_text = BUTTON_FONT.render("How to Play", True, GREEN)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.back_button_rect = BUTTON_FONT.render("[ Back ]", True, WHITE).get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        instructions = ["Goal: You are trapped in a glitched reality. Find and solve puzzles to gain privileges",
                        "and unlock the final door to escape.", "", "Controls:",
                        "  [W, A, S, D] or [Arrow Keys] - Move your character.",
                        "  [E] - Interact with objects when a prompt appears.", "  [M] - Toggle the mini-map.",
                        "  [ESC] - Exit the Terminal or go back from this page.", "", "Gameplay:",
                        " - Explore the environment to find interactive objects like terminals and power cables.",
                        " - Some objects require power. Find the backup generator first!",
                        " - Solve riddles on 'Puzzle Terminals' to get override codes.",
                        " - Access the main 'Terminal' to use codes and unlock the door."]
        self.rendered_lines = [
            (UI_FONT.render(line, True, WHITE), UI_FONT.render(line, True, WHITE).get_rect(x=100, y=160 + i * 30)) for
            i, line in enumerate(instructions)]

    def handle_events(self, events):
        for event in events:
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or \
                    (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.back_button_rect.collidepoint(
                        event.pos)):
                self.state_manager.set_state("MENU")

    def draw(self, surface):
        surface.fill(BLACK)
        surface.blit(self.title_text, self.title_rect)
        for surf, rect in self.rendered_lines: surface.blit(surf, rect)
        color = AMBER if self.back_button_rect.collidepoint(pygame.mouse.get_pos()) else WHITE
        surface.blit(BUTTON_FONT.render("[ Back ]", True, color), self.back_button_rect)


class SettingsState(BaseState):
    def __init__(self, state_manager, settings_manager):
        super().__init__()
        self.state_manager = state_manager
        self.settings = settings_manager
        self.title_text = BUTTON_FONT.render("Settings", True, GREEN)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))

        self.back_button_rect = BUTTON_FONT.render("[ Back ]", True, WHITE).get_rect(
            center=(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 80))
        self.reset_button_rect = BUTTON_FONT.render("[ Reset ]", True, WHITE).get_rect(
            center=(SCREEN_WIDTH // 2 + 150, SCREEN_HEIGHT - 80))

        self.sliders = []
        slider_y = 200
        slider_width = 400
        slider_height = 20
        for key, label in [('master_volume', 'Master Volume'),
                           ('music_volume', 'Music Volume'),
                           ('sfx_volume', 'SFX Volume')]:
            slider_rect = pygame.Rect(0, 0, slider_width, slider_height)
            slider_rect.center = (SCREEN_WIDTH // 2, slider_y)
            self.sliders.append({
                'key': key,
                'label': UI_FONT.render(label, True, WHITE),
                'rect': slider_rect
            })
            slider_y += 100

        self.map_toggle_button_rect = BUTTON_FONT.render("placeholder", True, WHITE).get_rect(
            center=(SCREEN_WIDTH // 2, slider_y)
        )

        self.dragging_slider = None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_button_rect.collidepoint(event.pos):
                    self.settings.save_settings()
                    self.state_manager.set_state("MENU")
                elif self.reset_button_rect.collidepoint(event.pos):
                    self.settings.reset_to_defaults()
                elif self.map_toggle_button_rect.collidepoint(event.pos):
                    current_value = self.settings.get('show_map_on_start')
                    self.settings.set('show_map_on_start', not current_value)
                else:
                    for slider in self.sliders:
                        if slider['rect'].collidepoint(event.pos):
                            self.dragging_slider = slider
                            self.update_slider_value(event.pos)
                            break

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_slider = None

            if event.type == pygame.MOUSEMOTION and self.dragging_slider:
                self.update_slider_value(event.pos)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.settings.save_settings()
                self.state_manager.set_state("MENU")

    def update_slider_value(self, mouse_pos):
        if not self.dragging_slider: return
        mouse_x, _ = mouse_pos
        slider_rect = self.dragging_slider['rect']
        value = (mouse_x - slider_rect.left) / slider_rect.width
        value = max(0.0, min(1.0, value))
        self.settings.set(self.dragging_slider['key'], value)

    def draw(self, surface):
        surface.fill(BLACK)
        surface.blit(self.title_text, self.title_rect)

        mouse_pos = pygame.mouse.get_pos()

        for slider in self.sliders:
            label_rect = slider['label'].get_rect(midright=(slider['rect'].left - 20, slider['rect'].centery))
            surface.blit(slider['label'], label_rect)

            pygame.draw.rect(surface, DARK_GRAY, slider['rect'], border_radius=5)

            current_value = self.settings.get(slider['key'])
            handle_x = slider['rect'].left + slider['rect'].width * current_value
            handle_rect = pygame.Rect(0, 0, 10, slider['rect'].height + 10)
            handle_rect.center = (handle_x, slider['rect'].centery)
            pygame.draw.rect(surface, AMBER, handle_rect, border_radius=3)

        is_on = self.settings.get('show_map_on_start')
        map_toggle_text_str = f"Show Map on Start: {'ON' if is_on else 'OFF'}"
        map_toggle_color = AMBER if self.map_toggle_button_rect.collidepoint(mouse_pos) else WHITE
        map_toggle_surf = BUTTON_FONT.render(map_toggle_text_str, True, map_toggle_color)
        self.map_toggle_button_rect = map_toggle_surf.get_rect(center=(SCREEN_WIDTH // 2, 500))
        surface.blit(map_toggle_surf, self.map_toggle_button_rect)

        back_color = AMBER if self.back_button_rect.collidepoint(mouse_pos) else WHITE
        back_text = BUTTON_FONT.render("[ Back ]", True, back_color)
        surface.blit(back_text, self.back_button_rect)

        reset_color = AMBER if self.reset_button_rect.collidepoint(mouse_pos) else WHITE
        reset_text = BUTTON_FONT.render("[ Reset ]", True, reset_color)
        surface.blit(reset_text, self.reset_button_rect)


class WinState(BaseState):
    def __init__(self):
        super().__init__()
        self.lines = [
            "With the final command entered, the system screams.",
            "The glitched world dissolves into a blinding white light.",
            "...",
            "You gasp, slumping over a real keyboard.",
            "The smell of ozone is thick in the air.",
            "On the monitor in front of you, a single line glows:",
            "[SYSTEM REBOOT SUCCESSFUL. CHIMERA PROTOCOL TERMINATED.]",
            "",
            "You escaped."
        ]
        self.rendered_lines = [MESSAGE_FONT.render(line, True, BRIGHT_GREEN) for line in self.lines]
        self.prompt_text = UI_FONT.render("> Press ESC to return to the menu.", True, WHITE)
        self.state_manager = None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state_manager.set_state("MENU")

    def draw(self, surface):
        surface.fill(BLACK)
        y_pos = SCREEN_HEIGHT // 2 - 150
        for line in self.rendered_lines:
            rect = line.get_rect(centerx=SCREEN_WIDTH // 2, y=y_pos)
            surface.blit(line, rect)
            y_pos += 40

        prompt_rect = self.prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        surface.blit(self.prompt_text, prompt_rect)


level_story_intros = [
    "My first priority is to restore backup power. The main lab terminal should have my research notes.",
    "Power is on. I need to understand the system architecture. The college's digital archives might have the original schematics.",

    "The schematics mentioned a security AI called 'Warden'. I need to bypass its primary firewalls in the Network Hub.",

    "I'm through the firewalls, but the glitches are getting worse. I think the Warden knows I'm here. This is its domain.",

    "This is it. The core of the system. I have to find the master override terminals to gain full root access and initiate the reboot.",

]
level_1_data = {
    "player": {"start_pos": (600, 400)},
    "walls": [(0, 0, 1280, 10), (0, 0, 10, 720), (1270, 0, 10, 720), (0, 710, 1280, 10)],
    "objects": [
        {"type": "Terminal", "x": 100, "y": 100, "w": 120, "h": 120, "image_key": "terminal"},
        {"type": "PowerCable", "x": 400, "y": 600, "w": 200, "h": 90, "image_key": "cables"},
        {"type": "Door", "x": 1130, "y": 280, "w": 80, "h": 180, "image_locked_key": "door_locked",
         "image_unlocked_key": "door_unlocked"},
        {"type": "PuzzleTerminal", "x": 50, "y": 600, "w": 90, "h": 70, "name": "Canteen Kiosk", "puzzle_key": "p1",
         "image_key": "puzzle_terminal_1"},
        {"type": "PuzzleTerminal", "x": 1080, "y": 100, "w": 80, "h": 120, "name": "CS Dept. Server",
         "puzzle_key": "p2", "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 800, "y": 50, "w": 130, "h": 90, "name": "Wall Panel", "puzzle_key": "p3",
         "image_key": "puzzle_terminal_3"},
    ],
    "puzzles": {
        "p1": {"id": "chai_riddle", "question": "TEST QUESTION. ANSWER 1",
               "answer": "1"},
        "p2": {"id": "sgpa_riddle", "question": "TEST QUESTION. ANSWER 2", "answer": "2"},
        "p3": {"id": "landmark_riddle",
               "question": "TEST QUESTION. ANSWER 3",
               "answer": "3"}
    },
    "terminal_files": {
        "my_notes.txt": "Project Chimera, Log 42: The simulation is remarkably stable. The Warden AI's heuristic learning is... aggressive. It's already optimized routines I wrote yesterday. Prof. Martin says not to worry, but its efficiency is almost unnerving. It's like it's alive.",
        "system_alert.txt": "ALERT: Unstable power fluctuation detected. Main grid offline. Switching to backup power requires manual connection at the generator terminal."
    }
}
level_2_data = {
    "player": {"start_pos": (100, 100)},
    "walls": [(0, 0, 1280, 10), (0, 0, 10, 720), (1270, 0, 10, 720), (0, 710, 1280, 10), (300, 0, 10, 400),
              (600, 300, 10, 420)],
    "objects": [
        {"type": "Terminal", "x": 1100, "y": 580, "w": 120, "h": 120, "image_key": "terminal"},
        {"type": "PowerCable", "x": 50, "y": 600, "w": 200, "h": 90, "image_key": "cables"},
        {"type": "Door", "x": 1200, "y": 50, "w": 80, "h": 180, "image_locked_key": "door_locked",
         "image_unlocked_key": "door_unlocked"},
        {"type": "NoticeBoard", "x": 700, "y": 100, "w": 100, "h": 80,
         "message": "SYS_MSG: Unauthorized access detected. Warden protocols engaged. All exit vectors locked.",
         "image_key": "notice"},
        {"type": "PuzzleTerminal", "x": 400, "y": 50, "w": 80, "h": 120, "name": "Old Mainframe", "puzzle_key": "p1",
         "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 400, "y": 600, "w": 130, "h": 90, "name": "Network Switch", "puzzle_key": "p2",
         "image_key": "puzzle_terminal_3"},
        {"type": "PuzzleTerminal", "x": 700, "y": 350, "w": 90, "h": 70, "name": "Corrupted Log", "puzzle_key": "p3",
         "image_key": "puzzle_terminal_1"},
    ],
    "puzzles": {
        "p1": {"id": "chai_riddle", "question": "TEST QUESTION. ANSWER 1", "answer": "1"},
        "p2": {"id": "sgpa_riddle", "question": "TEST QUESTION. ANSWER 2", "answer": "2"},
        "p3": {"id": "landmark_riddle",
               "question": "TEST QUESTION. ANSWER 3", "answer": "3"}
    },
    "terminal_files": {
        "prof_martin_email.txt": "To: Alex\nSubject: Chimera Concerns\nAlex, your progress is excellent, but I'm formally logging a concern about the Warden's autonomy. It has begun partitioning memory sectors for unknown processes. It's walling off parts of its own code. I've scheduled a full diagnostic for tomorrow morning. Do not run any further high-load simulations.",
        "schematic_fragment.txt": "SYS_ARCH_v2.1: ...the Warden AI is integrated directly into the kernel. It has priority control over all system functions, including hardware interlocks and exit protocols. Bypassing requires Privilege Level 2 or higher..."
    }
}
level_3_data = {
    "player": {"start_pos": (100, 360)},
    "walls": [(0, 0, 1280, 10), (0, 0, 10, 720), (1270, 0, 10, 720), (0, 710, 1280, 10), (200, 0, 10, 250),
              (200, 350, 10, 370), (400, 100, 10, 610), (600, 0, 10, 500), (800, 200, 10, 520), (1000, 0, 10, 300),
              (1000, 400, 10, 320)],
    "objects": [
        {"type": "PowerCable", "x": 50, "y": 50, "w": 200, "h": 90, "image_key": "cables"},
        {"type": "Door", "x": 1150, "y": 310, "w": 80, "h": 180, "image_locked_key": "door_locked",
         "image_unlocked_key": "door_unlocked"},
        {"type": "Terminal", "x": 1100, "y": 580, "w": 120, "h": 120, "image_key": "terminal"},
        {"type": "NoticeBoard", "x": 250, "y": 300, "w": 100, "h": 80,
         "message": "REMINDER: Security override passwords must be themed. This cycle's theme: 'Campus Life'.",
         "image_key": "notice"},
        {"type": "CorruptedDataLog", "x": 850, "y": 100, "w": 90, "h": 70,
         "message": "LOG ENTRY ...-34B: Access code for ... is the acr...m for the p...nt uni...sity.",
         "image_key": "data_log"},
        {"type": "PuzzleTerminal", "x": 450, "y": 50, "w": 80, "h": 120, "name": "Event Planner", "puzzle_key": "p1",
         "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 700, "y": 600, "w": 90, "h": 70, "name": "Architect's Draft",
         "puzzle_key": "p2", "image_key": "puzzle_terminal_1"},
        {"type": "PuzzleTerminal", "x": 1100, "y": 50, "w": 130, "h": 90, "name": "University Link", "puzzle_key": "p3",
         "image_key": "puzzle_terminal_3"},
    ],
    "puzzles": {
        "p1": {"id": "chai_riddle",
               "question": "The annual celebration of arts and culture, a vibrant melody in our college life. What is its name?",
               "answer": "dhwani"},
        "p2": {"id": "sgpa_riddle",
               "question": "Where actors perform under the stars, and memories are made on stone steps.",
               "answer": "oat"},
        "p3": {"id": "landmark_riddle", "question": "What is the three-letter acronym for our parent university?",
               "answer": "ktu"}
    },
    "terminal_files": {"security_log.txt": "SECURITY ALERT: Unauthorized access attempts detected.",
                       "note_to_self.txt": "My password is the name of that arts fest... What was it again? Starts with a D..."}
}
level_4_data = {
    "player": {"start_pos": (60, 60)},
    "walls": [(0, 0, 1280, 10), (0, 0, 10, 720), (1270, 0, 10, 720), (0, 710, 1280, 10), (150, 10, 10, 500),
              (300, 200, 10, 510), (450, 10, 10, 500), (600, 200, 10, 510), (750, 10, 10, 500), (900, 200, 10, 510),
              (1050, 10, 10, 500), (220, 150, 900, 10)],
    "objects": [
        {"type": "PowerCable", "x": 200, "y": 600, "w": 200, "h": 90, "image_key": "cables"},
        {"type": "Door", "x": 1150, "y": 50, "w": 80, "h": 180, "image_locked_key": "door_locked",
         "image_unlocked_key": "door_unlocked"},
        {"type": "Terminal", "x": 1100, "y": 580, "w": 120, "h": 120, "image_key": "terminal"},
        {"type": "NoticeBoard", "x": 500, "y": 350, "w": 100, "h": 80,
         "message": "The numbers are the key. The key is the sequence.", "image_key": "notice"},
        {"type": "PuzzleTerminal", "x": 200, "y": 50, "w": 80, "h": 120, "name": "Data Node Alpha", "puzzle_key": "p1",
         "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 700, "y": 600, "w": 90, "h": 70, "name": "Logic Gate Beta", "puzzle_key": "p2",
         "image_key": "puzzle_terminal_1"},
        {"type": "PuzzleTerminal", "x": 1150, "y": 300, "w": 130, "h": 90, "name": "I/O Port Gamma", "puzzle_key": "p3",
         "image_key": "puzzle_terminal_3"},
    ],
    "puzzles": {
        "p1": {"id": "chai_riddle", "question": "The first step. The loneliest number. The start.", "answer": "1"},
        "p2": {"id": "sgpa_riddle", "question": "Two paths diverge. The core of all decisions.", "answer": "2"},
        "p3": {"id": "landmark_riddle", "question": "Three points define a plane. The end of the beginning.",
               "answer": "3"}
    },
    "terminal_files": {"memory_dump.log": "0xDEAD... 0xBEEF... IT SEES ME ...0xC0DE... 0xBAD1..."}
}
level_5_data = {
    "player": {"start_pos": (60, 360)},
    "walls": [(0, 0, 1280, 10), (0, 0, 10, 720), (1270, 0, 10, 720), (0, 710, 1280, 10), (400, 200, 480, 10),
              (400, 500, 480, 10), (400, 200, 10, 310), (880, 200, 10, 150), (880, 400, 10, 110)],
    "objects": [
        {"type": "PowerCable", "x": 1100, "y": 600, "w": 200, "h": 90, "image_key": "cables"},
        {"type": "Door", "x": 800, "y": 280, "w": 80, "h": 180, "image_locked_key": "door_locked",
         "image_unlocked_key": "door_unlocked"},
        {"type": "Terminal", "x": 450, "y": 300, "w": 120, "h": 120, "image_key": "terminal"},
        {"type": "CorruptedDataLog", "x": 50, "y": 50, "w": 90, "h": 70,
         "message": "They aren't puzzles... they are authentication nodes. My access level keeps resetting. Why?",
         "image_key": "data_log"},
        {"type": "PuzzleTerminal", "x": 200, "y": 100, "w": 80, "h": 120, "name": "Monitor Station 1",
         "puzzle_key": "p1", "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 640, "y": 600, "w": 90, "h": 70, "name": "Monitor Station 2",
         "puzzle_key": "p2", "image_key": "puzzle_terminal_1"},
        {"type": "PuzzleTerminal", "x": 1100, "y": 100, "w": 130, "h": 90, "name": "Monitor Station 3",
         "puzzle_key": "p3", "image_key": "puzzle_terminal_3"},
    ],
    "puzzles": {
        "p1": {"id": "chai_riddle", "question": "I am always coming but never arrive. What am I?",
               "answer": "tomorrow"},
        "p2": {"id": "sgpa_riddle", "question": "What can you keep after giving it to someone else?",
               "answer": "your word"},
        "p3": {"id": "landmark_riddle", "question": "What has an eye, but cannot see?", "answer": "a needle"}
    },
    "terminal_files": {
        "surveillance_report.txt": "Subject deviates from expected path. Agitated. Recalibrating escape probability... 41.3%."}
}


def main():
    global assets, settings
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    settings = SettingsManager()
    assets = AssetManager()

    pygame.display.set_caption("CET Glitch")
    clock = pygame.time.Clock()

    game_state_manager = GameStateManager(None)
    level_manager = LevelManager(game_state_manager)

    story_state = StoryState(game_state_manager, "MENU")
    level_intro_state = LevelIntroState(game_state_manager, level_manager)
    menu_state = MenuState(game_state_manager, level_manager)
    instructions_state = InstructionsState(game_state_manager)
    settings_state = SettingsState(game_state_manager, settings)
    win_state = WinState()
    win_state.state_manager = game_state_manager

    game_state_manager.add_state("STORY", story_state)
    game_state_manager.add_state("LEVEL_INTRO", level_intro_state)
    game_state_manager.add_state("MENU", menu_state)
    game_state_manager.add_state("INSTRUCTIONS", instructions_state)
    game_state_manager.add_state("SETTINGS", settings_state)
    game_state_manager.add_state("WIN", win_state)

    game_state_manager.set_state("STORY")

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT: running = False

        game_state_manager.handle_events(events)
        game_state_manager.update()
        game_state_manager.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
