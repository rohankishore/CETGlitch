import random
import time
import webbrowser

import pygame
from moviepy.editor import VideoFileClip

SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FPS = 60

# Colors
BLACK = (0, 0, 0)
DARK_PURPLE = (30, 0, 30)
DARK_GRAY = (10, 10, 10)
GREEN = (0, 255, 0)
RED = (255, 100, 100)
WHITE = (220, 220, 220)
CYAN = (0, 200, 200)
AMBER = (255, 191, 0)
BRIGHT_GREEN = (100, 255, 100)
MAP_GRAY = (50, 50, 50)
MAP_WALL = (100, 100, 100)
POPUP_BG = (20, 20, 40, 220)

pygame.font.init()
UI_FONT = pygame.font.SysFont("Consolas", 24)
MESSAGE_FONT = pygame.font.SysFont("Consolas", 32)
TERMINAL_FONT = pygame.font.SysFont("Lucida Console", 20)
POPUP_FONT = pygame.font.SysFont("Consolas", 28)
# Fonts for the menu
TITLE_FONT = pygame.font.SysFont("Lucida Console", 96)
BUTTON_FONT = pygame.font.SysFont("Consolas", 48)


class PopupManager:
    """Manages displaying and timing out popup messages."""

    def __init__(self):
        self.popups = []

    def add_popup(self, text, duration_seconds):
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
    """Manages the current state of the game."""

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
    """A template for all game states."""

    def __init__(self): pass

    def on_enter(self): pass

    def on_exit(self): pass

    def handle_events(self, events): pass

    def update(self): pass

    def draw(self, surface): pass


class GlitchManager:
    """Creates intense, screen-wide visual distortion effects."""

    def __init__(self):
        self.glitches = []
        self.active = False

    def trigger_glitch(self, duration_ms, intensity):
        end_time = pygame.time.get_ticks() + duration_ms
        self.glitches.append({'end_time': end_time, 'intensity': intensity})
        self.active = True

    def update(self):
        current_time = pygame.time.get_ticks()
        self.glitches = [g for g in self.glitches if g['end_time'] > current_time]
        self.active = bool(self.glitches)

    def draw(self, surface):
        if not self.active: return
        intensity = max(g['intensity'] for g in self.glitches) if self.glitches else 0
        for _ in range(intensity):
            slice_height = random.randint(1, 3)
            y = random.randint(0, SCREEN_HEIGHT - slice_height)
            slice_rect = pygame.Rect(0, y, SCREEN_WIDTH, slice_height)
            if not surface.get_locked():
                subsurface = surface.subsurface(slice_rect).copy()
                offset = random.randint(-20, 20)
                surface.blit(subsurface, (offset, y))


class Camera:
    """Manages the game's viewport and screen shake."""

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
    """Tracks the state of puzzles and game progression."""

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
    """Base class for all game objects that can now handle images."""

    def __init__(self, x, y, w, h, name="", image_path=None):
        super().__init__()
        self.name = name
        self.image = None
        if image_path:
            try:
                original_image = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(original_image, (w, h))
            except pygame.error as e:
                print(f"Error loading image '{image_path}': {e}")
        if not self.image:
            self.image = pygame.Surface((w, h))
            self.image.fill(DARK_PURPLE)
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, surface, camera, puzzle_manager=None):
        surface.blit(self.image, camera.apply(self.rect))


class Player(Entity):
    """Represents the player character, now with walking sounds."""

    def __init__(self, x, y):
        # --- CORRECTED: Call the parent Entity's __init__ method. ---
        # This was the main bug. Without this call, the Player object would
        # not have self.image or self.rect, causing a crash.
        super().__init__(x, y, 32, 40, name="player")
        self.speed = 5
        self.image.fill(CYAN)
        self.dx, self.dy = 0, 0
        self.walking_sound = None
        self.is_walking = False
        try:
            self.walking_sound = pygame.mixer.Sound("assets/audios/walk.mp3")
        except pygame.error as e:
            print(f"Warning: Could not load walking sound: {e}")

    def update(self, walls):
        self.get_input()
        self.move(walls)
        self.update_sound()

    def get_input(self):
        keys = pygame.key.get_pressed()
        self.dx, self.dy = 0, 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: self.dx -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.dx += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]: self.dy -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: self.dy += self.speed

    def update_sound(self):
        if not self.walking_sound: return
        is_moving_now = self.dx != 0 or self.dy != 0
        if is_moving_now and not self.is_walking:
            self.is_walking = True
            self.walking_sound.play(loops=-1)
        elif not is_moving_now and self.is_walking:
            self.is_walking = False
            self.walking_sound.stop()

    def stop_sound(self):
        if self.walking_sound and self.is_walking:
            self.is_walking = False
            self.walking_sound.stop()

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
    def __init__(self, x, y, w, h, message, image_path=None):
        super().__init__(x, y, w, h, "notice board", image_path=image_path)
        self.message = message

    def get_interaction_message(self, puzzle_manager):
        return "An old, dusty notice board. [E] to read."

    def interact(self, game_state_manager, puzzle_manager):
        game_state_manager.current_state.popup_manager.add_popup(self.message, 6)


class CorruptedDataLog(InteractiveObject):
    def __init__(self, x, y, w, h, message, image_path=None):
        super().__init__(x, y, w, h, "corrupted data log", image_path=image_path)
        self.message = message

    def get_interaction_message(self, puzzle_manager):
        return "A data log, flickering erratically. [E] to examine."

    def interact(self, game_state_manager, puzzle_manager):
        game_state_manager.current_state.popup_manager.add_popup(self.message, 5)
        game_state_manager.current_state.glitch_manager.trigger_glitch(500, 10)


class PuzzleTerminal(InteractiveObject):
    def __init__(self, x, y, w, h, name, puzzle_id, question, answer, image_path=None):
        super().__init__(x, y, w, h, name, image_path=image_path)
        self.puzzle_id = puzzle_id
        self.question = question
        self.answer = answer

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state(f"{self.puzzle_id}_solved"): return f"The {self.name} is offline."
        return f"A flickering {self.name}. [E] to read."

    def interact(self, game_state_manager, puzzle_manager):
        if not puzzle_manager.get_state(f"{self.puzzle_id}_solved"):
            game_state_manager.current_state.popup_manager.add_popup(
                f"{self.question} The answer is the override code.", 8)


class Door(InteractiveObject):
    def __init__(self, x, y, w, h, image_path_locked=None, image_path_unlocked=None):
        super().__init__(x, y, w, h, name="door")
        self.image_locked = None
        self.image_unlocked = None
        try:
            if image_path_locked:
                img_lock = pygame.image.load(image_path_locked).convert_alpha()
                self.image_locked = pygame.transform.scale(img_lock, (w, h))
            if image_path_unlocked:
                img_unlock = pygame.image.load(image_path_unlocked).convert_alpha()
                self.image_unlocked = pygame.transform.scale(img_unlock, (w, h))
        except pygame.error as e:
            print(f"Error loading door image: {e}")
        self.image = self.image_locked if self.image_locked else pygame.Surface((w, h))
        self.rect = self.image.get_rect(topleft=(x, y))

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state("door_unlocked"): return "The door is unlocked. [E] to leave."
        return "It's locked. A digital keypad is dark."

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
    def __init__(self, x, y, w, h, image_path=None):
        super().__init__(x, y, w, h, "old terminal", image_path=image_path)

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state("power_restored"): return "The terminal hums with power. [E] to access."
        return "The screen is dead. Power seems to be out."

    def interact(self, game_state_manager, puzzle_manager):
        if puzzle_manager.get_state("power_restored"):
            game_state_manager.set_state("TERMINAL")
        else:
            game_state_manager.current_state.popup_manager.add_popup("No power to the terminal.", 2)


class PowerCable(InteractiveObject):
    def __init__(self, x, y, w, h, image_path=None):
        super().__init__(x, y, w, h, "pile of cables", image_path=image_path)

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state("power_restored"): return "The cables are connected to the backup generator."
        return "A tangled mess. One seems to lead to a backup generator. [E] to connect."

    def interact(self, game_state_manager, puzzle_manager):
        if not puzzle_manager.get_state("power_restored"):
            puzzle_manager.set_state("power_restored", True)
            game_state_manager.current_state.popup_manager.add_popup(
                "You connected the main cable. A low hum fills the room.", 4)
            game_state_manager.current_state.glitch_manager.trigger_glitch(1000, 15)
            game_state_manager.current_state.camera.start_shake(1000, 5)


class LevelManager:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.levels = [level_1_data, level_2_data, level_3_data]
        self.current_level_index = 0

    def load_level(self, level_data):
        puzzle_manager = PuzzleManager()
        game_scene = GameScene(self.state_manager, puzzle_manager, self, level_data)
        self.state_manager.add_state("GAME", game_scene)
        terminal_files = level_data.get("terminal_files", {})
        terminal_scene = TerminalState(self.state_manager, puzzle_manager, level_data["puzzles"], terminal_files)
        self.state_manager.add_state("TERMINAL", terminal_scene)

    def start_new_game(self):
        self.current_level_index = 0
        self.load_level(self.levels[self.current_level_index])
        self.state_manager.set_state("GAME")

    def load_specific_level(self, level_index):
        if 0 <= level_index < len(self.levels):
            print(f"DEBUG: Loading level {level_index + 1}")
            self.current_level_index = level_index
            self.load_level(self.levels[level_index])
            self.state_manager.set_state("GAME")
        else:
            print(f"Error: Level index {level_index} is out of bounds.")

    def next_level(self):
        self.current_level_index += 1
        if self.current_level_index < len(self.levels):
            print(f"Loading level {self.current_level_index + 1}...")
            self.load_level(self.levels[self.current_level_index])
            self.state_manager.set_state("GAME")
        else:
            print("All levels completed!")
            self.state_manager.set_state("WIN")


class GameScene(BaseState):
    def __init__(self, state_manager, puzzle_manager, level_manager, level_data):
        super().__init__()
        self.state_manager = state_manager
        self.puzzle_manager = puzzle_manager
        self.level_manager = level_manager
        self.glitch_manager = GlitchManager()
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.popup_manager = PopupManager()
        self.show_map = False
        player_pos = level_data["player"]["start_pos"]
        self.player = Player(player_pos[0], player_pos[1])
        self.interactives = []
        for obj_data in level_data["objects"]:
            obj_type = obj_data["type"]
            x, y, w, h = obj_data["x"], obj_data["y"], obj_data["w"], obj_data["h"]
            image_path = obj_data.get("image")
            if obj_type == "Terminal":
                self.interactives.append(Terminal(x, y, w, h, image_path=image_path))
            elif obj_type == "PowerCable":
                self.interactives.append(PowerCable(x, y, w, h, image_path=image_path))
            elif obj_type == "Door":
                self.interactives.append(Door(x, y, w, h,
                                              image_path_locked=obj_data.get("image_locked"),
                                              image_path_unlocked=obj_data.get("image_unlocked")))
            elif obj_type == "PuzzleTerminal":
                p_info = level_data["puzzles"][obj_data["puzzle_key"]]
                self.interactives.append(
                    PuzzleTerminal(x, y, w, h, obj_data["name"], p_info["id"], p_info["question"], p_info["answer"],
                                   image_path=image_path))
            elif obj_type == "NoticeBoard":
                self.interactives.append(NoticeBoard(x, y, w, h, obj_data["message"], image_path=image_path))
            elif obj_type == "CorruptedDataLog":
                self.interactives.append(CorruptedDataLog(x, y, w, h, obj_data["message"], image_path=image_path))
        self.walls = [Wall(w[0], w[1], w[2], w[3]) for w in level_data["walls"]]
        self.flicker_timer = 0
        self.interaction_message = ""

    def on_exit(self):
        self.player.stop_sound()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e: self.try_interact()
                if event.key == pygame.K_m: self.show_map = not self.show_map

    def try_interact(self):
        for obj in self.interactives:
            if self.player.rect.colliderect(obj.rect.inflate(20, 20)):
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
            prompt_text = UI_FONT.render(self.interaction_message, True, WHITE)
            surface.blit(prompt_text, (20, SCREEN_HEIGHT - 40))
        map_prompt = UI_FONT.render("[M] Map", True, WHITE)
        surface.blit(map_prompt, (SCREEN_WIDTH - 120, 20))
        if self.show_map: self.draw_map(surface)

    def draw_map(self, surface):
        map_surf = pygame.Surface((250, 150))
        map_surf.fill(MAP_GRAY)
        map_surf.set_alpha(200)
        all_rects = [w.rect for w in self.walls] + [p.rect for p in self.interactives]
        if not all_rects: return
        min_x = min(r.left for r in all_rects)
        max_x = max(r.right for r in all_rects)
        min_y = min(r.top for r in all_rects)
        max_y = max(r.bottom for r in all_rects)
        world_w = max_x - min_x
        world_h = max_y - min_y
        if world_w == 0 or world_h == 0: return
        map_w, map_h = 250, 150
        scale = min(map_w / world_w, map_h / world_h)

        def scale_rect(rect):
            scaled_x = (rect.x - min_x) * scale
            scaled_y = (rect.y - min_y) * scale
            scaled_w = rect.w * scale
            scaled_h = rect.h * scale
            return pygame.Rect(scaled_x, scaled_y, scaled_w, scaled_h)

        for wall in self.walls: pygame.draw.rect(map_surf, MAP_WALL, scale_rect(wall.rect))
        for obj in self.interactives:
            color = AMBER
            if isinstance(obj, Door): color = BRIGHT_GREEN
            if isinstance(obj, Terminal): color = WHITE
            pygame.draw.rect(map_surf, color, scale_rect(obj.rect))
        pygame.draw.rect(map_surf, CYAN, scale_rect(self.player.rect))
        surface.blit(map_surf, (SCREEN_WIDTH - 270, 60))


# --- MODIFIED: TerminalState now has text wrapping ---
class TerminalState(BaseState):
    def __init__(self, state_manager, puzzle_manager, puzzles_data, terminal_files):
        super().__init__()
        self.state_manager = state_manager
        self.puzzle_manager = puzzle_manager
        self.puzzles = puzzles_data
        self.files = terminal_files
        self.input_text = ""
        self.output_lines = []
        self.cursor_visible = True
        self.cursor_timer = 0
        self.typewriter_effect = {"text": "", "pos": 0, "surf": None, "start_time": 0, "lines": []}
        self.command_history = []
        self.history_index = -1

    def on_enter(self):
        self.input_text = ""
        self.output_lines = []
        self.command_history = []
        self.history_index = -1
        boot_sequence = [
            "CET OS v1.3a [Kernel: GL-0xDEADBEEF]",
            "...",
            "System Integrity Check... FAILED.",
            "Memory Corruption Detected.",
            f"User privilege level: {self.puzzle_manager.get_state('privilege_level')}",
            "Type 'help' for a list of commands."
        ]
        self.add_output_multiline(boot_sequence)

    # --- NEW: Helper method for text wrapping ---
    def _wrap_text(self, text, font, max_width):
        """Wraps a single line of text to a given width."""
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            # Test if adding the new word exceeds the width
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                # If it exceeds, finalize the current line and start a new one
                lines.append(current_line.strip())
                current_line = word + " "
        lines.append(current_line.strip())  # Add the last line
        return lines

    def add_output(self, text, instant=False):
        if instant:
            lines = text.split('\n')
            for line in lines:
                self.output_lines.append(TERMINAL_FONT.render(line, True, GREEN))
        else:
            surf = pygame.Surface(TERMINAL_FONT.size(text), pygame.SRCALPHA)
            self.typewriter_effect = {"text": text, "pos": 0, "surf": surf, "start_time": time.time(), "lines": []}
            self.output_lines.append(surf)

    def add_output_multiline(self, lines_list):
        self.typewriter_effect = {"text": "", "pos": 0, "surf": None, "start_time": time.time(), "lines": lines_list}

    def handle_events(self, events):
        if self.typewriter_effect["text"] or self.typewriter_effect["lines"]: return
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.input_text.strip():
                        self.command_history.insert(0, self.input_text)
                        self.history_index = -1
                    self.process_command()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.state_manager.set_state("GAME")
                elif event.key == pygame.K_UP:
                    if self.history_index < len(self.command_history) - 1:
                        self.history_index += 1
                        self.input_text = self.command_history[self.history_index]
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
        full_command = self.input_text.lower().strip()
        self.add_output(f"> {self.input_text}", instant=True)
        self.input_text = ""
        parts = full_command.split()
        command = parts[0] if parts else ""
        if not command: return

        if command == "help":
            help_text = (
                "Available Commands:\n"
                "  status       - Show system and door status.\n"
                "  unlock       - Attempt to unlock the main door (requires level 3).\n"
                "  override <code> - Enter a code to gain privileges (e.g., 'override 1234').\n"
                "  ls           - List available files.\n"
                "  cat <file>   - Display the content of a file (e.g., 'cat log.txt').\n"
                "  exit         - Close the terminal."
            )

            # --- MODIFIED: Use the text wrapper for the help command ---
            max_width = SCREEN_WIDTH - 40  # 20px padding on each side
            wrapped_text = []
            for line in help_text.split('\n'):
                wrapped_lines = self._wrap_text(line, TERMINAL_FONT, max_width)
                wrapped_text.extend(wrapped_lines)

            # Add the fully wrapped text instantly for better readability
            self.add_output("\n".join(wrapped_text), instant=True)

        elif command == "status":
            priv = self.puzzle_manager.get_state('privilege_level')
            door = "UNLOCKED" if self.puzzle_manager.get_state("door_unlocked") else "LOCKED"
            self.add_output(f"Privilege: {priv}/3. Main Door: {door}. Network: OFFLINE.", instant=False)
        elif command == "unlock":
            if self.puzzle_manager.get_state('privilege_level') >= 3:
                self.add_output("Privilege accepted. Unlocking door...", instant=False)
                self.puzzle_manager.set_state("door_unlocked", True)
            else:
                self.add_output(f"ERROR: Insufficient privileges. Level 3 required.", instant=False)
        elif command == "override":
            if len(parts) > 1:
                code = parts[1]
                found_puzzle = False
                for key, puzzle in self.puzzles.items():
                    if code == puzzle["answer"]:
                        found_puzzle = True
                        if not self.puzzle_manager.get_state(f"{puzzle['id']}_solved"):
                            self.puzzle_manager.set_state(f"{puzzle['id']}_solved", True)
                            self.puzzle_manager.increment_privilege()
                            self.add_output("Override code accepted. Privilege level increased.", instant=False)
                        else:
                            self.add_output("Code already used. No effect.", instant=False)
                        break
                if not found_puzzle: self.add_output("ERROR: Invalid override code.", instant=False)
            else:
                self.add_output("Usage: override <CODE>", instant=False)
        elif command == "ls":
            if self.files:
                self.add_output(" ".join(self.files.keys()), instant=False)
            else:
                self.add_output("No files found.", instant=False)
        elif command == "cat":
            if len(parts) > 1:
                filename = parts[1]
                if filename in self.files:
                    # --- MODIFIED: Use text wrapper for file content as well ---
                    max_width = SCREEN_WIDTH - 40
                    wrapped_text = []
                    for line in self.files[filename].split('\n'):
                        wrapped_lines = self._wrap_text(line, TERMINAL_FONT, max_width)
                        wrapped_text.extend(wrapped_lines)
                    self.add_output("\n".join(wrapped_text), instant=True)
                else:
                    self.add_output(f"ERROR: File not found: '{filename}'", instant=False)
            else:
                self.add_output("Usage: cat <filename>", instant=False)
        elif command == "exit":
            self.state_manager.set_state("GAME")
        else:
            self.add_output(f"Command not recognized: '{command}'. Type 'help'.", instant=False)

    def update(self):
        self.cursor_timer = (self.cursor_timer + 1) % FPS
        self.cursor_visible = self.cursor_timer < FPS // 2
        if self.typewriter_effect["lines"]:
            effect = self.typewriter_effect
            elapsed_lines = int((time.time() - effect["start_time"]) * 4)
            if elapsed_lines > len(self.output_lines):
                if effect["lines"]:
                    next_line = effect["lines"].pop(0)
                    self.output_lines.append(TERMINAL_FONT.render(next_line, True, GREEN))
            if not effect["lines"]:
                self.typewriter_effect["lines"] = []
        elif self.typewriter_effect["text"]:
            effect = self.typewriter_effect
            elapsed = (time.time() - effect["start_time"]) * 30
            new_pos = min(len(effect["text"]), int(elapsed))
            if new_pos > effect["pos"]:
                effect["pos"] = new_pos
                rendered_text = TERMINAL_FONT.render(effect["text"][:effect["pos"]], True, GREEN)
                effect["surf"].fill((0, 0, 0, 0))
                effect["surf"].blit(rendered_text, (0, 0))
            if effect["pos"] >= len(effect["text"]): self.typewriter_effect["text"] = ""

    def draw(self, surface):
        surface.fill(BLACK)
        for y in range(0, SCREEN_HEIGHT, 4): pygame.draw.line(surface, (0, 15, 0), (0, y), (SCREEN_WIDTH, y))
        y_pos = 20
        max_lines = (SCREEN_HEIGHT - 50) // (TERMINAL_FONT.get_height() + 5)
        start_index = max(0, len(self.output_lines) - max_lines)
        for line_surf in self.output_lines[start_index:]:
            if line_surf: surface.blit(line_surf, (20, y_pos)); y_pos += TERMINAL_FONT.get_height() + 5
        if not (self.typewriter_effect["text"] or self.typewriter_effect["lines"]):
            prompt_surf = TERMINAL_FONT.render(f"> {self.input_text}", True, GREEN)
            surface.blit(prompt_surf, (20, y_pos))
            if self.cursor_visible:
                cursor_x = 20 + prompt_surf.get_width()
                cursor_rect = pygame.Rect(cursor_x + 2, y_pos, 10, TERMINAL_FONT.get_height())
                pygame.draw.rect(surface, GREEN, cursor_rect)


class WinState(BaseState):
    def __init__(self):
        super().__init__()
        self.win_text = MESSAGE_FONT.render("You escaped the glitch.", True, BRIGHT_GREEN)
        self.win_rect = self.win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    def draw(self, surface): surface.fill(BLACK); surface.blit(self.win_text, self.win_rect)


class CutsceneState(BaseState):
    def __init__(self, state_manager, video_path, next_state):
        super().__init__()
        self.state_manager = state_manager
        self.video_path = video_path
        self.next_state = next_state
        self.clip = None
        self.start_time = 0
        self.finished = False
        self.load_error = False
        self.prompt_font = pygame.font.SysFont("Consolas", 22)
        self.error_font = pygame.font.SysFont("Consolas", 28)
        self.skip_text = self.prompt_font.render("Press [ESC] or [SPACE] to skip", True, WHITE)
        self.skip_rect = self.skip_text.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20))
        self.error_msg_1 = self.error_font.render("Video file could not be loaded.", True, RED)
        self.error_msg_2 = self.prompt_font.render("Press any key to continue.", True, WHITE)
        self.error_rect_1 = self.error_msg_1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        self.error_rect_2 = self.error_msg_2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))

    def on_enter(self):
        self.finished = False
        self.load_error = False
        try:
            self.clip = VideoFileClip(self.video_path)
            self.clip = self.clip.resize((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.start_time = pygame.time.get_ticks()
            if self.clip.audio:
                self.clip.audio.preview(fps=44100)
        except Exception as e:
            print(f"FATAL: Could not load video '{self.video_path}'. Error: {e}")
            self.load_error = True
            self.clip = None

    def on_exit(self):
        if self.clip:
            if self.clip.audio:
                pygame.mixer.quit()
                pygame.mixer.init()
            self.clip.close()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.load_error:
                    self.state_manager.set_state(self.next_state)
                    return
                if event.key in [pygame.K_ESCAPE, pygame.K_SPACE]:
                    self.finished = True

    def update(self):
        if self.load_error: return
        if self.finished:
            self.state_manager.set_state(self.next_state)
            return
        if self.clip:
            current_video_time = (pygame.time.get_ticks() - self.start_time) / 1000.0
            if current_video_time >= self.clip.duration:
                self.finished = True

    def draw(self, surface):
        surface.fill(BLACK)
        if self.load_error:
            surface.blit(self.error_msg_1, self.error_rect_1)
            surface.blit(self.error_msg_2, self.error_rect_2)
            return
        if self.clip and not self.finished:
            current_video_time = (pygame.time.get_ticks() - self.start_time) / 1000.0
            if current_video_time < self.clip.duration:
                try:
                    frame = self.clip.get_frame(current_video_time)
                    frame_surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                    surface.blit(frame_surface, (0, 0))
                except Exception as e:
                    print(f"Error rendering video frame: {e}")
                    self.finished = True
            surface.blit(self.skip_text, self.skip_rect)


class MenuState(BaseState):
    def __init__(self, state_manager, level_manager):
        super().__init__()
        self.state_manager = state_manager
        self.level_manager = level_manager
        self.title_text = TITLE_FONT.render("CET GLITCH", True, GREEN)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.button_texts = ["Start Game", "Instructions", "GitHub", "Quit"]
        self.buttons = {}
        self.github_url = "https://github.com/rohankishore/"
        y_pos = 300
        for text in self.button_texts:
            text_surf = BUTTON_FONT.render(text, True, WHITE)
            text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            self.buttons[text] = text_rect
            y_pos += 80
        self.background_image = None
        try:
            raw_image = pygame.image.load("assets/cet.png").convert()
            self.background_image = pygame.transform.scale(raw_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except pygame.error as e:
            print(f"Warning: Could not load background image 'assets/cet.png': {e}")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for text, rect in self.buttons.items():
                    if rect.collidepoint(event.pos):
                        self.handle_button_click(text)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_3:
                    print("DEBUG: Key '3' pressed. Skipping to Level 3.")
                    self.level_manager.load_specific_level(2)

    def handle_button_click(self, text):
        if text == "Start Game":
            self.level_manager.start_new_game()
        elif text == "Instructions":
            self.state_manager.set_state("INSTRUCTIONS")
        elif text == "GitHub":
            try:
                webbrowser.open(self.github_url)
            except Exception as e:
                print(f"Could not open GitHub URL: {e}")
        elif text == "Quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def draw(self, surface):
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(BLACK)
        surface.blit(self.title_text, self.title_rect)
        mouse_pos = pygame.mouse.get_pos()
        for text, rect in self.buttons.items():
            color = AMBER if rect.collidepoint(mouse_pos) else WHITE
            text_surf = BUTTON_FONT.render(text, True, color)
            surface.blit(text_surf, rect)


class InstructionsState(BaseState):
    def __init__(self, state_manager):
        super().__init__()
        self.state_manager = state_manager
        self.title_text = BUTTON_FONT.render("How to Play", True, GREEN)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.back_button_rect = BUTTON_FONT.render("[ Back ]", True, WHITE).get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        instructions = [
            "Goal: You are trapped in a glitched reality. Find and solve puzzles to gain privileges",
            "and unlock the final door to escape.",
            "",
            "Controls:",
            "  [W, A, S, D] or [Arrow Keys] - Move your character.",
            "  [E] - Interact with objects when a prompt appears.",
            "  [M] - Toggle the mini-map.",
            "  [ESC] - Exit the Terminal or go back from this page.",
            "",
            "Gameplay:",
            " - Explore the environment to find interactive objects like terminals and power cables.",
            " - Some objects require power. Find the backup generator first!",
            " - Solve riddles on 'Puzzle Terminals' to get override codes.",
            " - Access the main 'Terminal' to use codes and unlock the door.",
        ]
        self.rendered_lines = []
        y_pos = 160
        for line in instructions:
            line_surf = UI_FONT.render(line, True, WHITE)
            line_rect = line_surf.get_rect(x=100, y=y_pos)
            self.rendered_lines.append((line_surf, line_rect))
            y_pos += 30

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state_manager.set_state("MENU")
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_button_rect.collidepoint(event.pos):
                    self.state_manager.set_state("MENU")

    def draw(self, surface):
        surface.fill(BLACK)
        surface.blit(self.title_text, self.title_rect)
        for surf, rect in self.rendered_lines:
            surface.blit(surf, rect)
        mouse_pos = pygame.mouse.get_pos()
        color = AMBER if self.back_button_rect.collidepoint(mouse_pos) else WHITE
        back_text = BUTTON_FONT.render("[ Back ]", True, color)
        surface.blit(back_text, self.back_button_rect)


# Level Data...
level_1_data = {
    "player": {"start_pos": (600, 400)},
    "walls": [(0, 0, SCREEN_WIDTH, 10), (0, 0, 10, SCREEN_HEIGHT), (SCREEN_WIDTH - 10, 0, 10, SCREEN_HEIGHT),
              (0, SCREEN_HEIGHT - 10, SCREEN_WIDTH, 10)],
    "objects": [
        {"type": "Terminal", "x": 100, "y": 100, "w": 120, "h": 120, "image": "assets/terminal.png"},
        {"type": "PowerCable", "x": 400, "y": SCREEN_HEIGHT - 120, "w": 200, "h": 90, "image": "assets/cables.png"},
        {"type": "Door", "x": SCREEN_WIDTH - 150, "y": 280, "w": 80, "h": 180, "image_locked": "assets/door_locked.png",
         "image_unlocked": "assets/door_unlocked.png"},
        {"type": "PuzzleTerminal", "x": 50, "y": 600, "w": 90, "h": 70, "name": "Canteen", "puzzle_key": "p1",
         "image": "assets/puzzle_terminal_1.png"},
        {"type": "PuzzleTerminal", "x": SCREEN_WIDTH - 200, "y": 100, "w": 80, "h": 120, "name": "CS Dept. Server",
         "puzzle_key": "p2", "image": "assets/puzzle_terminal_2.png"},
        {"type": "PuzzleTerminal", "x": 800, "y": 50, "w": 130, "h": 90, "name": "Wall Panel", "puzzle_key": "p3",
         "image": "assets/puzzle_terminal_3.png"},
    ],
    "puzzles": {
        "p1": {"id": "chai_riddle", "question": "What is the price of one chai at the Canteen?", "answer": "7"},
        "p2": {"id": "sgpa_riddle", "question": "The place where there are swings in the campus", "answer": "gazebo"},
        "p3": {"id": "landmark_riddle",
               "question": "I stand tall and circular, a hub of knowledge and late-night study sessions. What am I?",
               "answer": "library"}
    }
}
level_2_data = {
    "player": {"start_pos": (100, 100)},
    "walls": [(0, 0, SCREEN_WIDTH, 10), (0, 0, 10, SCREEN_HEIGHT), (SCREEN_WIDTH - 10, 0, 10, SCREEN_HEIGHT),
              (0, SCREEN_HEIGHT - 10, SCREEN_WIDTH, 10), (300, 0, 10, 400), (600, 300, 10, 420)],
    "objects": [
        {"type": "Terminal", "x": 1100, "y": 580, "w": 120, "h": 120, "image": "assets/terminal.png"},
        {"type": "PowerCable", "x": 50, "y": 600, "w": 200, "h": 90, "image": "assets/cables.png"},
        {"type": "Door", "x": 1200, "y": 50, "w": 80, "h": 180, "image_locked": "assets/door_locked.png",
         "image_unlocked": "assets/door_unlocked.png"},
        {"type": "PuzzleTerminal", "x": 400, "y": 50, "w": 80, "h": 120, "name": "Old Mainframe", "puzzle_key": "p1",
         "image": "assets/puzzle_terminal_2.png"},
        {"type": "PuzzleTerminal", "x": 400, "y": 600, "w": 130, "h": 90, "name": "Network Switch", "puzzle_key": "p2",
         "image": "assets/puzzle_terminal_3.png"},
        {"type": "PuzzleTerminal", "x": 700, "y": 350, "w": 90, "h": 70, "name": "Corrupted Log", "puzzle_key": "p3",
         "image": "assets/puzzle_terminal_1.png"},
    ],
    "puzzles": {
        "p1": {"id": "chai_riddle", "question": "How many departments are in CET?", "answer": "9"},
        "p2": {"id": "sgpa_riddle", "question": "What year was CET established?", "answer": "1987"},
        "p3": {"id": "landmark_riddle",
               "question": "I am a college festival of lights, sounds, and celebration. What am I?", "answer": "dyuthi"}
    }
}
level_3_data = {
    "player": {"start_pos": (100, SCREEN_HEIGHT / 2)},
    "walls": [
        (0, 0, SCREEN_WIDTH, 10), (0, 0, 10, SCREEN_HEIGHT), (SCREEN_WIDTH - 10, 0, 10, SCREEN_HEIGHT),
        (0, SCREEN_HEIGHT - 10, SCREEN_WIDTH, 10),
        (200, 0, 10, 250), (200, 350, 10, 370), (400, 100, 10, SCREEN_HEIGHT - 110),
        (600, 0, 10, 500), (800, 200, 10, 520), (1000, 0, 10, 300), (1000, 400, 10, 320),
    ],
    "objects": [
        {"type": "PowerCable", "x": 50, "y": 50, "w": 200, "h": 90, "image": "assets/cables.png"},
        {"type": "Door", "x": 1150, "y": 310, "w": 80, "h": 180, "image_locked": "assets/door_locked.png",
         "image_unlocked": "assets/door_unlocked.png"},
        {"type": "Terminal", "x": 1100, "y": 580, "w": 120, "h": 120, "image": "assets/terminal.png"},
        {"type": "NoticeBoard", "x": 250, "y": 300, "w": 100, "h": 80,
         "message": "REMINDER: Security override passwords must be themed. This cycle's theme: 'Campus Life'.",
         "image": "assets/notice.png"},
        {"type": "CorruptedDataLog", "x": 850, "y": 100, "w": 90, "h": 70,
         "message": "LOG ENTRY ...-34B: Access code for ... is the acr...m for the p...nt uni...sity.",
         "image": "assets/data_log.png"},
        {"type": "PuzzleTerminal", "x": 450, "y": 50, "w": 80, "h": 120, "name": "Event Planner", "puzzle_key": "p1",
         "image": "assets/puzzle_terminal_2.png"},
        {"type": "PuzzleTerminal", "x": 700, "y": 600, "w": 90, "h": 70, "name": "Architect's Draft",
         "puzzle_key": "p2", "image": "assets/puzzle_terminal_1.png"},
        {"type": "PuzzleTerminal", "x": 1100, "y": 50, "w": 130, "h": 90, "name": "University Link", "puzzle_key": "p3",
         "image": "assets/puzzle_terminal_3.png"},
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
    "terminal_files": {
        "security_log.txt": "SECURITY ALERT: Unauthorized access attempts detected. Multiple uses of the 'override' command with invalid codes. System integrity is compromised. All personnel should be vigilant.",
        "note_to_self.txt": "My password is so easy to remember. It's just the name of that arts fest... the one with all the music. What was it again? Starts with a D..."
    }
}


def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CET Glitch")
    clock = pygame.time.Clock()

    game_state_manager = GameStateManager(None)
    level_manager = LevelManager(game_state_manager)

    intro_cutscene = CutsceneState(game_state_manager, "assets/videos/start.mp4", "GAME")
    menu_state = MenuState(game_state_manager, level_manager)
    instructions_state = InstructionsState(game_state_manager)

    game_state_manager.add_state("MENU", menu_state)
    game_state_manager.add_state("INSTRUCTIONS", instructions_state)
    game_state_manager.add_state("CUTSCENE", intro_cutscene)
    game_state_manager.add_state("WIN", WinState())

    # Set the initial state to the main menu
    game_state_manager.set_state("MENU")

    running = True
    while running:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

        game_state_manager.handle_events(events)
        game_state_manager.update()
        game_state_manager.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()