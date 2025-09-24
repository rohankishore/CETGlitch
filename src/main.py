import json
import math
import os
import random
import threading
import time
import webbrowser

import pygame
import pyttsx3

from core.const import *

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


def create_ghost_face_surface(size, alpha=100):
    """Creates a simple, procedurally generated ghostly face."""
    face_surf = pygame.Surface(size, pygame.SRCALPHA)

    face_color = (200, 220, 255, alpha)
    pygame.draw.ellipse(face_surf, face_color, face_surf.get_rect().inflate(-10, 0))

    eye_color = (0, 0, 0, alpha + 50)
    eye_y = size[1] // 2 - 10
    left_eye_rect = pygame.Rect(size[0] // 2 - 25, eye_y, 15, 20)
    right_eye_rect = pygame.Rect(size[0] // 2 + 10, eye_y, 15, 20)
    pygame.draw.ellipse(face_surf, eye_color, left_eye_rect)
    pygame.draw.ellipse(face_surf, eye_color, right_eye_rect)

    mouth_rect = pygame.Rect(size[0] // 2 - 15, size[1] - 30, 30, 15)
    pygame.draw.arc(face_surf, eye_color, mouth_rect, math.pi, 2 * math.pi, 2)

    return face_surf


light_texture_cache = {}


def get_light_texture(radius):
    """Creates and caches a circular white gradient texture for lights."""
    if radius in light_texture_cache:
        return light_texture_cache[radius]

    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for i in range(radius, 0, -1):
        alpha = int(255 * (1 - (i / radius)) ** 1.5)
        pygame.draw.circle(surf, (255, 255, 255, alpha), (radius, radius), i)

    light_texture_cache[radius] = surf
    return surf


class Light:
    """Represents a single light source in the world."""

    def __init__(self, owner, radius, color, pulse_intensity=0.0, pulse_speed=0.0):
        self.owner = owner
        self.radius = radius
        self.color = color
        self.texture = get_light_texture(radius)
        self.pulse_intensity = pulse_intensity
        self.pulse_speed = pulse_speed
        self.pulse_timer = random.random() * math.pi * 2
        self.dim_multiplier = 1.0


class LightingManager:
    """Manages all lights and renders the final lighting effect."""

    def __init__(self, width, height, ambient_color=(20, 20, 40)):
        self.light_surface = pygame.Surface((width, height))
        self.ambient_color = ambient_color
        self.lights = []
        self.occluders = []

    def add_light(self, light):
        if light not in self.lights:
            self.lights.append(light)

    def set_occluders(self, occluders):
        self.occluders = [o.rect for o in occluders]

    def draw(self, target_surface, camera):
        self.light_surface.fill(self.ambient_color)

        for light in self.lights:
            light.pulse_timer += light.pulse_speed

            pulse_multiplier = 1.0 - (math.sin(light.pulse_timer) * 0.5 + 0.5) * light.pulse_intensity

            final_multiplier = pulse_multiplier * light.dim_multiplier

            current_color = (
                int(light.color[0] * final_multiplier),
                int(light.color[1] * final_multiplier),
                int(light.color[2] * final_multiplier)
            )

            color_surf = pygame.Surface(light.texture.get_size(), pygame.SRCALPHA)
            color_surf.fill(current_color)
            temp_texture = light.texture.copy()
            temp_texture.blit(color_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            pos = camera.apply(light.owner.rect).center
            light_rect = temp_texture.get_rect(center=pos)
            self.light_surface.blit(temp_texture, light_rect, special_flags=pygame.BLEND_RGBA_ADD)

        target_surface.blit(self.light_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)


class VoiceManager:
    def __init__(self):
        self.engine = None
        if pyttsx3:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 175)
            except Exception as e:
                print(f"Error initializing pyttsx3: {e}. Voice narration disabled.")
                print(f"Error initializing pyttsx3: {e}. Voice narration disabled.")
                self.engine = None

    def _speak_in_thread(self, text):
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"Error during speech synthesis: {e}")

    def speak(self, text):

        if self.engine and settings and settings.get('enable_voice_narration'):

            if self.engine.isBusy():
                self.engine.stop()

            thread = threading.Thread(target=self._speak_in_thread, args=(text,))
            thread.daemon = True
            thread.start()


def wrap_text(text, font, max_width):
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
        self.event_cooldown = 12000
        self.current_interference = None
        self.reset_timer()

    def reset_timer(self):
        self.next_event_time = pygame.time.get_ticks() + self.event_cooldown + random.randint(-4000, 4000)

    def update(self):
        now = pygame.time.get_ticks()
        if now > self.next_event_time:
            self.trigger_event()
            self.reset_timer()

    def shift_architecture(self):
        print("[Warden] Reality matrix destabilizing.")
        player_pos = self.game_scene.player.rect.center

        # Find a wall far away from the player
        candidate_walls = [w for w in self.game_scene.walls if
                           math.hypot(w.rect.centerx - player_pos[0], w.rect.centery - player_pos[1]) > 500]

        if not candidate_walls: return

        wall_to_move = random.choice(candidate_walls)

        # Example: shift it by its own width
        original_pos = wall_to_move.rect.topleft
        wall_to_move.rect.x += wall_to_move.rect.width

        # Important: Check if the new position is clear before finalizing
        is_colliding = False
        for obj in self.game_scene.walls + self.game_scene.interactives:
            if obj is not wall_to_move and wall_to_move.rect.colliderect(obj.rect):
                is_colliding = True
                break

        if is_colliding:  # If it's blocked, revert the move
            wall_to_move.rect.topleft = original_pos

    def trigger_backlash(self, target_name, value):
        print(f"[Warden] Backlash triggered due to hack on '{target_name}'")
        self.game_scene.popup_manager.add_popup(
            "SYS.WARDEN//: Unauthorized execution detected. Deploying countermeasures...", 4)
        self.game_scene.glitch_manager.trigger_glitch(2000, 30)

        if target_name == "player" and value > 1.0:
            self.game_scene.popup_manager.add_popup("BACKLASH: Threat signature amplified. Hunter deployed.", 5)
            self.spawn_hunter()
        elif target_name == "hunter" and value < 1.0:
            self.game_scene.popup_manager.add_popup("BACKLASH: System integrity failing. Event frequency increased.", 5)
            self.event_cooldown = max(4000, self.event_cooldown - 4000)
            self.next_event_time = pygame.time.get_ticks() + 1000

    def trigger_event(self):
        level_index = self.game_scene.level_manager.current_level_index
        priv_level = self.game_scene.puzzle_manager.get_state('privilege_level')

        events = [self.minor_glitch, self.static_burst]
        if priv_level > 0:
            events.extend([self.object_corruption, self.terminal_interference])

        if level_index >= 2:
            events.append(self.spawn_hunter)

        if level_index >= 2 and random.random() < 0.05:
            self.jumpscare()
            return

        if level_index >= 4:
            events.extend([self.major_glitch, self.spawn_hunter, self.environmental_mimicry])

        if level_index >= 1:
            events.append(self.whisper_event)

        if level_index >= 3 and random.random() < 0.02:  # 2% chance on later levels
            self.dox_player_event()
            return

        chosen_event = random.choice(events)
        chosen_event()

    def whisper_event(self):
        print("[Warden] Triggering auditory hallucination.")
        assets.play_sound("whisper")

    def dox_player_event(self):
        print("[Warden] PERSONALIZED THREAT INITIALIZED")
        try:
            username = os.getlogin()
            message = f"SYS.WARDEN//: The ghost in the machine is not you. It's me. And I see you, {username.upper()}."
            self.game_scene.popup_manager.add_popup(message, 6)
        except Exception:
            self.major_glitch()

    def jumpscare(self):
        """A rare, high-intensity scare event."""
        print("[Warden] JUMPSCARE TRIGGERED")
        assets.play_sound("jumpscare")
        self.game_scene.camera.start_shake(600, 30)
        self.game_scene.glitch_manager.trigger_static_burst(400, alpha=255)
        self.game_scene.add_jumpscare_effect()

    def spawn_hunter(self):
        if len(self.game_scene.hunters) >= 1:
            self.object_corruption()
            return

        print("[Warden] Spawning Hunter entity.")
        self.game_scene.popup_manager.add_popup("WARNING: Warden process located in this sector.", 3)
        self.game_scene.add_hunter()

    def environmental_mimicry(self):
        print("[Warden] Triggering Environmental Mimicry.")
        self.game_scene.popup_manager.add_popup("SYS.WARDEN//: Reality matrix compromised.", 3)
        self.major_glitch()

    def minor_glitch(self):
        print("[Warden] Triggering minor glitch.")
        self.game_scene.glitch_manager.trigger_glitch(300, 8)
        self.game_scene.camera.start_shake(300, 2)

    def major_glitch(self):
        print("[Warden] Triggering MAJOR glitch.")
        self.game_scene.popup_manager.add_popup("SYS.WARDEN//: Foreign entity detected. Purge protocols active.", 2)
        self.game_scene.glitch_manager.trigger_glitch(1200, 20)
        self.game_scene.camera.start_shake(1000, 7)

    def terminal_interference(self):
        print("[Warden] Preparing terminal interference.")
        interferences = [
            " [Warden]: YOU ARE A GHOST IN YOUR OWN TOMB.",
            " [Warden]: YOUR MEMORIES ARE BUGS IN THE SYSTEM."
        ]
        self.current_interference = random.choice(interferences)
        self.game_scene.popup_manager.add_popup("WARNING: I/O stream corrupted by Warden process.", 3)

    def static_burst(self):
        print("[Warden] Triggering static burst.")
        self.game_scene.glitch_manager.trigger_static_burst(500, alpha=180)
        self.game_scene.camera.start_shake(400, 4)

    def object_corruption(self):
        if not self.game_scene.interactives: return
        target = random.choice(self.game_scene.interactives)
        if isinstance(target, Door):
            self.minor_glitch()
            return
        print(f"[Warden] Corrupting object: {target.name}")
        self.game_scene.corrupted_objects.append({
            'obj': target,
            'end_time': pygame.time.get_ticks() + 2000
        })
        self.game_scene.popup_manager.add_popup("SYS.WARDEN//: Data instability detected.", 2)


class SettingsManager:

    def __init__(self, filepath='settings.json'):
        self.filepath = filepath
        self.defaults = {
            'master_volume': 0.8,
            'music_volume': 0.7,
            'sfx_volume': 1.0,
            'show_map_on_start': True,
            'enable_voice_narration': True
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
        self.load_image("vignette", "assets/images/vignette.png")
        self.load_image("cables", "assets/images/cables.png")
        self.load_image("door_locked", "assets/images/door_locked.png")
        self.load_image("door_unlocked", "assets/images/door_unlocked.png")
        self.load_image("puzzle_terminal_1", "assets/images/puzzle_terminal_1.png")
        self.load_image("puzzle_terminal_2", "assets/images/puzzle_terminal_2.png")
        self.load_image("puzzle_terminal_3", "assets/images/puzzle_terminal_3.png")
        self.load_image("notice", "assets/images/notice.png")
        self.load_image("data_log", "assets/images/data_log.png")
        self.load_image("background", "assets/images/banner.png")
        self.load_sound("walk", "assets/audios/walk.mp3")
        self.load_sound("whisper", "assets/audios/whisper.mp3")
        self.load_sound("jumpscare", "assets/audios/jumpscare.mp3")
        self.load_sound("stalker_ambience", "assets/audios/stalker_ambience.mp3")
        self.load_sound("hum", "assets/audios/hum.mp3")
        self.load_sound("powerup", "assets/audios/powerup.mp3")
        self.load_sound("glitch", "assets/audios/glitch.mp3")
        self.load_sound("interact", "assets/audios/interact.mp3")
        self.load_sound("popup", "assets/audios/popup.mp3")
        self.load_sound("key_press", "assets/audios/key_press.mp3")
        self.load_sound("terminal_error", "assets/audios/terminal_error.mp3")
        self.load_sound("override_success", "assets/audios/override_success.mp3")
        self.load_sound("menu_music", "assets/audios/menu.mp3")
        self.load_sound("ambient_music", "assets/audios/ambience.mp3")
        self.load_sound("terminal_music", "assets/audios/terminal_music.mp3")
        self.load_sound("story_line_1", "assets/audios/intro.mp3")
        self.load_sound("story_line_8", "assets/audios/story_line_8.mp3")

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


class PopupManager:

    def __init__(self):
        self.popups = []

    def add_popup(self, text, duration_seconds):
        assets.play_sound("popup")
        #voice_manager.speak(text)
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
        self.static_bursts = []
        self.active = False
        self.chromatic_offset_x = 0
        self.chromatic_offset_y = 0
        self.scanline_alpha = 0

    def trigger_glitch(self, duration_ms, intensity):
        end_time = pygame.time.get_ticks() + duration_ms
        self.glitches.append({'end_time': end_time, 'intensity': intensity})
        assets.play_sound("glitch")

    def trigger_static_burst(self, duration_ms, alpha=150):
        end_time = pygame.time.get_ticks() + duration_ms
        self.static_bursts.append({'end_time': end_time, 'alpha': alpha})
        assets.play_sound("glitch")

    def update(self):
        current_time = pygame.time.get_ticks()
        self.glitches = [g for g in self.glitches if g['end_time'] > current_time]
        self.static_bursts = [b for b in self.static_bursts if b['end_time'] > current_time]
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
        if not self.active and self.scanline_alpha == 0 and not self.static_bursts: return

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

        if self.static_bursts:
            max_alpha = max(b['alpha'] for b in self.static_bursts)
            static_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for _ in range(150):
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT)
                w = random.randint(10, 50)
                h = random.randint(1, 3)
                color_val = random.randint(50, 200)
                color = (color_val, color_val, color_val, random.randint(50, 150))
                pygame.draw.rect(static_surf, color, (x, y, w, h))
            static_surf.set_alpha(max_alpha)
            surface.blit(static_surf, (0, 0))


class CodeFragmentManager:
    def __init__(self):
        self.fragments = {}
        self.used_fragments = set()

    def collect_fragment(self, frag_id, code_string):
        if frag_id not in self.used_fragments:
            self.fragments[frag_id] = code_string
            print(f"[CodeFragments] Collected {frag_id}: {code_string}")

    def get_code(self, frag_id):
        return self.fragments.get(frag_id)

    def use_fragment(self, frag_id):
        if frag_id in self.fragments:
            del self.fragments[frag_id]
            self.used_fragments.add(frag_id)


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
            "puzzle1_solved": False, "puzzle2_solved": False, "puzzle3_solved": False,
        }

    def set_state(self, key, value):
        if key not in self.state or self.state[key] != value:
            print(f"[PuzzleManager] State change: {key} -> {value}")
            self.state[key] = value

    def get_state(self, key): return self.state.get(key, None)

    def increment_privilege(self):
        self.state["privilege_level"] += 1
        print(f"[PuzzleManager] Fragmentation Key re-integrated. Privilege level: {self.state['privilege_level']}")


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

class RainParticle:
    """Represents a single character in the digital rain effect."""
    def __init__(self, x, y, font):
        self.x = x
        self.y = y
        self.font = font
        self.vy = random.uniform(4, 8)
        self.char = random.choice(['0', '1', '.', ':', ',', ';', '|', ']', '['])
        # Render the character once for performance
        self.surf = self.font.render(self.char, True, (0, 50, 20, 180))

    def update(self):
        self.y += self.vy
        if self.y > SCREEN_HEIGHT:
            self.y = random.randint(-100, -20)
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self, surface):
        surface.blit(self.surf, (self.x, self.y))


class WardenHunter(Entity):
    def __init__(self, x, y):
        size = 40
        super().__init__(x, y, size, size, name="warden_hunter")
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)

        pygame.draw.rect(self.image, RED, (0, 0, size, size), 4)
        pygame.draw.rect(self.image, DARK_RED, (4, 4, size - 8, size - 8))
        self.speed = 2
        self.move_timer = 0
        self.move_duration = random.randint(1000, 3000)
        self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        self.pulse_timer = 0
        self.base_image = self.image.copy()

    def update(self, player, walls):
        now = pygame.time.get_ticks()

        self.pulse_timer += 0.1
        alpha = 128 + math.sin(self.pulse_timer) * 127
        self.image = self.base_image.copy()
        self.image.set_alpha(alpha)

        if now > self.move_timer:
            self.direction = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)])
            self.move_timer = now + random.randint(1000, 3000)

        dx = self.direction[0] * self.speed
        dy = self.direction[1] * self.speed

        self.rect.x += dx
        self.check_collision('x', walls, dx)
        self.rect.y += dy
        self.check_collision('y', walls, dy)

        if self.rect.colliderect(player.rect):
            player.get_caught()

    def check_collision(self, direction, collidables, velocity):
        for entity in collidables:
            if self.rect.colliderect(entity.rect):
                if direction == 'x':
                    if velocity > 0: self.rect.right = entity.rect.left
                    if velocity < 0: self.rect.left = entity.rect.right
                if direction == 'y':
                    if velocity > 0: self.rect.bottom = entity.rect.top
                    if velocity < 0: self.rect.top = entity.rect.bottom
                self.direction = (-self.direction[0], -self.direction[1])


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

        self.idle_timer = 0

        self.start_x, self.start_y = x, y
        self.game_scene = None

    def get_caught(self):
        """Called when the WardenHunter catches the player."""
        print("[Player] Caught by Warden Hunter!")
        if self.game_scene:
            self.game_scene.popup_manager.add_popup("SYS.WARDEN//: Threat neutralized. Resetting...", 2)
            self.game_scene.glitch_manager.trigger_glitch(1500, 25)
            self.game_scene.camera.start_shake(1500, 10)
            self.rect.topleft = (self.start_x, self.start_y)

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


class CodeFragment(InteractiveObject):
    def __init__(self, x, y, w, h, fragment_id, code_string, image=None):
        super().__init__(x, y, w, h, "Code Fragment", image)
        self.fragment_id = fragment_id
        self.code_string = code_string

        self.base_image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.base_image, DARK_GRAY, (0, 0, w, h))
        pygame.draw.rect(self.base_image, CYAN, (2, 2, w - 4, h - 4), 2)
        self.image = self.base_image.copy()
        self.pulse_timer = random.random() * math.pi * 2

    def get_interaction_message(self, puzzle_manager):
        return f"> A corrupted data chip lies here. ID: {self.fragment_id}. [E] to acquire."

    def interact(self, game_state_manager, puzzle_manager):
        game_scene = game_state_manager.states["GAME"]
        game_scene.code_fragment_manager.collect_fragment(self.fragment_id, self.code_string)
        game_scene.popup_manager.add_popup(f"Code Fragment '{self.fragment_id}' acquired.", 3)

        if self in game_scene.interactives:
            game_scene.interactives.remove(self)
        assets.play_sound("powerup")

    def draw(self, surface, camera, puzzle_manager=None):
        self.pulse_timer += 0.05
        alpha = 155 + math.sin(self.pulse_timer) * 100
        self.image = self.base_image.copy()
        self.image.set_alpha(alpha)
        super().draw(surface, camera, puzzle_manager)


class NoticeBoard(InteractiveObject):
    def __init__(self, x, y, w, h, message, image=None):
        super().__init__(x, y, w, h, "corporate notice board", image=image)
        self.message = message

    def get_interaction_message(self, puzzle_manager):
        return "> A flickering ChronoSyn notice board. [E] to read."

    def interact(self, game_state_manager, puzzle_manager):
        game_state_manager.current_state.popup_manager.add_popup(self.message, 6)


class CorruptedDataLog(InteractiveObject):
    def __init__(self, x, y, w, h, message, image=None):
        super().__init__(x, y, w, h, "corrupted data log", image=image)
        self.message = message

    def get_interaction_message(self, puzzle_manager):
        return "> A data log, bleeding static. [E] to examine."

    def interact(self, game_state_manager, puzzle_manager):
        game_state_manager.current_state.popup_manager.add_popup(self.message, 5)
        game_state_manager.current_state.glitch_manager.trigger_glitch(500, 10)


class PuzzleTerminal(InteractiveObject):
    def __init__(self, x, y, w, h, name, puzzle_id, question, answer, image=None):
        super().__init__(x, y, w, h, name, image=image)
        self.puzzle_id, self.question, self.answer = puzzle_id, question, answer

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state(
                f"{self.puzzle_id}_solved"): return f"The {self.name} is inert. A memory re-integrated."
        return f"> A flickering {self.name}. [E] to access memory fragment."

    def interact(self, game_state_manager, puzzle_manager):
        if not puzzle_manager.get_state(f"{self.puzzle_id}_solved"):
            game_state_manager.current_state.popup_manager.add_popup(
                f"Memory Fragment Recovery: {self.question}", 8)


class Door(InteractiveObject):
    def __init__(self, x, y, w, h, image_locked=None, image_unlocked=None):
        super().__init__(x, y, w, h, name="Quarantine Door")
        self.image_locked = pygame.transform.scale(image_locked, (w, h)) if image_locked else None
        self.image_unlocked = pygame.transform.scale(image_unlocked, (w, h)) if image_unlocked else None
        self.image = self.image_locked
        if not self.image: self.image = pygame.Surface((w, h))
        self.rect = self.image.get_rect(topleft=(x, y))

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state(
                "door_unlocked"): return "The final door is unlocked. [E] to proceed to the next sector."
        return "> Quarantine lock active. Requires 3 Fragmentation Keys."

    def interact(self, game_state_manager, puzzle_manager):
        if puzzle_manager.get_state("door_unlocked"): game_state_manager.current_state.level_manager.next_level()

    def draw(self, surface, camera, puzzle_manager):
        is_unlocked = puzzle_manager.get_state("door_unlocked")
        current_image = self.image_unlocked if is_unlocked and self.image_unlocked else self.image_locked
        if current_image:
            surface.blit(current_image, camera.apply(self.rect))
        else:
            color = BRIGHT_GREEN if is_unlocked else RED
            pygame.draw.rect(surface, color, camera.apply(self.rect))


class Terminal(InteractiveObject):
    def __init__(self, x, y, w, h, image=None):
        super().__init__(x, y, w, h, "ChronoSyn terminal", image=image)

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state("power_restored"): return "The terminal hums with quarantined power. [E] to access."
        return "> The screen is dead. System power is offline."

    def interact(self, game_state_manager, puzzle_manager):
        if puzzle_manager.get_state("power_restored"):
            game_state_manager.set_state("TERMINAL")
        else:
            game_state_manager.current_state.popup_manager.add_popup("No power to the terminal.", 2)


class PowerCable(InteractiveObject):
    def __init__(self, x, y, w, h, image=None):
        super().__init__(x, y, w, h, "backup power conduit", image=image)

    def get_interaction_message(self, puzzle_manager):
        if puzzle_manager.get_state("power_restored"): return "The conduit is humming, powering the local grid."
        return "> A damaged power conduit. It seems to lead to a backup generator. [E] to re-route power."

    def interact(self, game_state_manager, puzzle_manager):
        if not puzzle_manager.get_state("power_restored"):
            puzzle_manager.set_state("power_restored", True)
            game_state_manager.current_state.popup_manager.add_popup(
                "You re-routed the conduit. A low, painful hum fills the sector.", 4)
            game_state_manager.current_state.glitch_manager.trigger_glitch(1000, 15)
            game_state_manager.current_state.camera.start_shake(1000, 5)
            assets.play_sound("hum", loops=-1)


class StoryState(BaseState):
    def __init__(self, state_manager, next_state):
        super().__init__()
        self.state_manager = state_manager
        self.next_state = next_state

        story_content = [
            {'text': "The last thing I remember is the smell of ozone and sterile chrome.",
             'audio_key': 'story_line_1'},
            {'text': "Project Chimera. My magnum opus. My ascent to digital godhood.", 'audio_key': 'story_line_2'},
            {'text': "There was a signal... in the Deep Net. A key, I thought.", 'audio_key': 'story_line_3'},
            {'text': "It was not a key. It was a question that eats the answer.", 'audio_key': 'story_line_4'},
            {'text': "...", 'audio_key': None},
            {'text': "Now... I am a ghost in my own machine. A Remnant.", 'audio_key': 'story_line_5'},
            {'text': "This place, the Mnemosyne, was my heaven. Now it is my tomb, a quarantine of the soul.",
             'audio_key': 'story_line_6'},
            {'text': "A single, fractured memory flickers:", 'audio_key': 'story_line_7'},
            {'text': "> PROTOCOL: DAMNATIO MEMORIAE. A MERCIFUL DELETION.", 'audio_key': None},
            {'text': "> REQUIRES FULL CONSCIOUSNESS RE-INTEGRATION.", 'audio_key': None},
            {'text': "> FRAGMENTATION KEYS NEEDED: 3/3.", 'audio_key': None},
            {'text': "", 'audio_key': None},
            {'text': "I must become whole again. Not to escape. But to be erased.", 'audio_key': 'story_line_8'}
        ]

        self.story_lines = []
        for content in story_content:
            wrapped_text_lines = wrap_text(content['text'], STORY_FONT, SCREEN_WIDTH * 0.8)
            for line in wrapped_text_lines:
                self.story_lines.append({'text': line, 'audio_key': content['audio_key']})

        self.skip_prompt = UI_FONT.render("> Press any key to speed up / skip...", True, AMBER)

        self.typing_delay = 65
        self.line_pause = 500

    def on_enter(self):
        self.current_line_index = 0
        self.current_char_index = 0
        self.last_update = pygame.time.get_ticks()
        self.state = "TYPING"
        self.last_played_audio_key = None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                current_line_text = self.story_lines[self.current_line_index]['text']
                if self.state == "TYPING" and self.current_char_index < len(current_line_text):
                    self.current_char_index = len(current_line_text)
                else:
                    self.state_manager.set_state(self.next_state)

    def update(self):
        now = pygame.time.get_ticks()

        if self.state == "TYPING":
            if now - self.last_update > self.typing_delay:
                self.last_update = now

                current_line_info = self.story_lines[self.current_line_index]
                current_line_text = current_line_info['text']
                current_audio_key = current_line_info['audio_key']
                line_len = len(current_line_text)

                if self.current_char_index == 0 and line_len > 0:
                    if current_audio_key and current_audio_key != self.last_played_audio_key:
                        assets.play_sound(current_audio_key)
                        self.last_played_audio_key = current_audio_key

                if self.current_char_index < line_len:
                    self.current_char_index += 1
                    if current_line_text[self.current_char_index - 1] != ' ':
                        pass
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
            line_text = self.story_lines[i]['text']
            rendered_line = STORY_FONT.render(line_text, True, WHITE)
            rect = rendered_line.get_rect(centerx=SCREEN_WIDTH / 2, y=y_pos)
            surface.blit(rendered_line, rect)
            y_pos += 40

        if self.current_line_index < len(self.story_lines):
            typing_line_text = self.story_lines[self.current_line_index]['text'][:self.current_char_index]
            rendered_typing_line = STORY_FONT.render(typing_line_text, True, WHITE)
            rect = rendered_typing_line.get_rect(centerx=SCREEN_WIDTH / 2, y=y_pos)
            surface.blit(rendered_typing_line, rect)

        prompt_rect = self.skip_prompt.get_rect(centerx=SCREEN_WIDTH / 2, bottom=SCREEN_HEIGHT - 40)
        surface.blit(self.skip_prompt, prompt_rect)


class LevelIntroState(BaseState):
    def __init__(self, state_manager, level_manager):
        super().__init__()
        self.state_manager = state_manager
        self.level_manager = level_manager
        self.typing_delay = 50

    def on_enter(self):
        level_index = self.level_manager.current_level_index
        self.level_title = self.level_manager.level_themes[level_index]
        story_text = level_story_intros[level_index]
        objective_lines = level_objectives[level_index]

        self.wrapped_story_lines = wrap_text(story_text, STORY_FONT, SCREEN_WIDTH * 0.9)
        self.level_title_surf = LEVEL_TITLE_FONT.render(self.level_title, True, WHITE)

        self.objective_surfs = []
        for i, line in enumerate(objective_lines):
            color = AMBER if i == 0 else WHITE
            self.objective_surfs.append(UI_FONT.render(line, True, color))

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

        title_rect = self.level_title_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.2))
        surface.blit(self.level_title_surf, title_rect)

        y_pos = SCREEN_HEIGHT * 0.35
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

        if self.finished_typing:
            y_pos += 60
            for surf in self.objective_surfs:
                obj_rect = surf.get_rect(centerx=SCREEN_WIDTH / 2, y=y_pos)
                surface.blit(surf, obj_rect)
                y_pos += surf.get_height() + 10

            prompt_surf = UI_FONT.render("> Press any key to begin...", True, AMBER)
            prompt_rect = prompt_surf.get_rect(centerx=SCREEN_WIDTH / 2, bottom=SCREEN_HEIGHT - 40)
            surface.blit(prompt_surf, prompt_rect)


class LevelManager:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.levels = [level_1_data, level_2_data, level_3_data, level_4_data, level_5_data]
        self.level_themes = [
            "Chapter 1: The Cryo-Sanctum", "Chapter 2: The Habitation Unit", "Chapter 3: The Data-Nave",
            "Chapter 4: The Understrata", "Chapter 5: The 'God-Hand' Console"
        ]
        self.current_level_index = 0

    def load_level(self, level_data):
        puzzle_manager = PuzzleManager()
        game_scene = GameScene(self.state_manager, puzzle_manager, self, level_data,
                               self.level_themes[self.current_level_index])
        self.state_manager.add_state("GAME", game_scene)

        terminal_files = level_data.get("terminal_files", {})

        terminal_scene = TerminalState(self.state_manager, puzzle_manager, level_data["puzzles"], terminal_files,
                                       game_scene.code_fragment_manager)

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
        self.code_fragment_manager = CodeFragmentManager()
        self.vignette_image = assets.get_image("vignette")
        if self.vignette_image:
            self.vignette_image = pygame.transform.scale(self.vignette_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.warden_manager = WardenManager(self)
        self.show_map = settings.get('show_map_on_start')

        self.player = Player(level_data["player"]["start_pos"][0], level_data["player"]["start_pos"][1])
        self.player.game_scene = self

        self.level_title = level_title
        self.corrupted_objects = []
        self.hunters = []
        self.interactives = []
        self.walls = [Wall(w[0], w[1], w[2], w[3]) for w in level_data["walls"]]

        self.lighting_manager = LightingManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.lighting_manager.set_occluders(self.walls)
        player_light = Light(owner=self.player, radius=250, color=(70, 160, 180), pulse_intensity=0.2, pulse_speed=0.05)
        self.lighting_manager.add_light(player_light)

        self.reflection_effects = []
        self.jumpscare_effect = None
        self.ghost_face_texture = create_ghost_face_surface((80, 120))

        self.rain_particles = []
        if settings.get('enable_digital_rain'):
            self.rain_particles = [
                RainParticle(random.randint(0, SCREEN_WIDTH), random.randint(-SCREEN_HEIGHT, 0), TERMINAL_FONT) for _ in
                range(250)]

        for obj_data in level_data["objects"]:
            obj_type, x, y, w, h = obj_data["type"], obj_data["x"], obj_data["y"], obj_data["w"], obj_data["h"]
            new_obj = None
            if obj_type == "Terminal":
                new_obj = Terminal(x, y, w, h, image=assets.get_image(obj_data["image_key"]))
                light = Light(owner=new_obj, radius=180, color=(80, 180, 130), pulse_intensity=0.4, pulse_speed=0.03)
                self.lighting_manager.add_light(light)
            elif obj_type == "PowerCable":
                new_obj = PowerCable(x, y, w, h, image=assets.get_image(obj_data["image_key"]))
                new_obj.light = Light(owner=new_obj, radius=200, color=(200, 180, 100), pulse_intensity=0.6,
                                      pulse_speed=0.1)
            elif obj_type == "Door":
                new_obj = Door(x, y, w, h, image_locked=assets.get_image(obj_data["image_locked_key"]),
                               image_unlocked=assets.get_image(obj_data["image_unlocked_key"]))
            elif obj_type == "PuzzleTerminal":
                p_info = level_data["puzzles"][obj_data["puzzle_key"]]
                new_obj = PuzzleTerminal(x, y, w, h, obj_data["name"], p_info["id"], p_info["question"],
                                         p_info["answer"],
                                         image=assets.get_image(obj_data["image_key"]))
                light = Light(owner=new_obj, radius=150, color=(150, 100, 200), pulse_intensity=0.3, pulse_speed=0.02)
                self.lighting_manager.add_light(light)
            elif obj_type == "NoticeBoard":
                new_obj = NoticeBoard(x, y, w, h, obj_data["message"], image=assets.get_image(obj_data["image_key"]))
            elif obj_type == "CorruptedDataLog":
                new_obj = CorruptedDataLog(x, y, w, h, obj_data["message"],
                                           image=assets.get_image(obj_data["image_key"]))
            elif obj_type == "CodeFragment":
                new_obj = CodeFragment(x, y, w, h, obj_data["id"], obj_data["code"])
                light = Light(owner=new_obj, radius=80, color=(180, 180, 220), pulse_intensity=0.8, pulse_speed=0.1)
                self.lighting_manager.add_light(light)

            if new_obj:
                self.interactives.append(new_obj)

        self.flicker_timer, self.interaction_message = 0, ""

    def add_hunter(self):
        px, py = self.player.rect.center
        spawn_x, spawn_y = random.randint(100, SCREEN_WIDTH - 100), random.randint(100, SCREEN_HEIGHT - 100)
        while math.hypot(px - spawn_x, py - spawn_y) < 400:
            spawn_x, spawn_y = random.randint(100, SCREEN_WIDTH - 100), random.randint(100, SCREEN_HEIGHT - 100)
        new_hunter = WardenHunter(spawn_x, spawn_y)
        self.hunters.append(new_hunter)
        hunter_light = Light(owner=new_hunter, radius=300, color=(220, 40, 40), pulse_intensity=0.5, pulse_speed=0.1)
        self.lighting_manager.add_light(hunter_light)

    def add_jumpscare_effect(self):
        end_time = pygame.time.get_ticks() + 400
        face = create_ghost_face_surface((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), alpha=200)
        self.jumpscare_effect = {'surface': face, 'end_time': end_time}

    def on_enter(self):
        assets.play_sound("ambient_music", channel='music', loops=-1, fade_ms=1000)
        if self.puzzle_manager.get_state("power_restored"):
            assets.play_sound("powerup", loops=-1)
            for obj in self.interactives:
                if isinstance(obj, PowerCable) and hasattr(obj, 'light'):
                    if obj.light not in self.lighting_manager.lights:
                        self.lighting_manager.add_light(obj.light)

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
                if isinstance(obj, PowerCable) and not self.puzzle_manager.get_state("power_restored"):
                    if hasattr(obj, 'light') and obj.light not in self.lighting_manager.lights:
                        self.lighting_manager.add_light(obj.light)
                obj.interact(self.state_manager, self.puzzle_manager)
                return

    def update_reflections(self):
        if self.player.dx == 0 and self.player.dy == 0:
            self.player.idle_timer += 1
        else:
            self.player.idle_timer = 0

        if self.player.idle_timer > 180 and random.random() < 0.01:
            for item in self.interactives:
                is_reflective = False
                if isinstance(item, Terminal) and not self.puzzle_manager.get_state("power_restored"):
                    is_reflective = True
                if isinstance(item, PuzzleTerminal) and self.puzzle_manager.get_state(f"{item.puzzle_id}_solved"):
                    is_reflective = True
                if is_reflective:
                    dist = math.hypot(item.rect.centerx - self.player.rect.centerx,
                                      item.rect.centery - self.player.rect.centery)
                    if dist < 120:
                        print(f"[Reflection] Triggered on {item.name}")
                        self.reflection_effects.append({
                            'surface': self.ghost_face_texture,
                            'rect': item.rect,
                            'end_time': pygame.time.get_ticks() + 1000
                        })
                        self.player.idle_timer = 0
                        return

    def update(self):
        now = pygame.time.get_ticks()
        self.player.update(self.walls)

        if self.rain_particles:
            for p in self.rain_particles:
                p.update()

        self.update_reflections()
        self.reflection_effects = [r for r in self.reflection_effects if now < r['end_time']]
        if self.jumpscare_effect and now > self.jumpscare_effect['end_time']:
            self.jumpscare_effect = None

        for hunter in self.hunters:
            hunter.update(self.player, self.walls)
        self.camera.update(self.player)
        self.glitch_manager.update()
        self.warden_manager.update()
        self.popup_manager.update()
        self.corrupted_objects = [o for o in self.corrupted_objects if o['end_time'] > now]
        prompt = ""
        for obj in self.interactives:
            if self.player.rect.colliderect(obj.rect.inflate(20, 20)):
                prompt = obj.get_interaction_message(self.puzzle_manager)
                break
        self.interaction_message = prompt

    # NEW: Method to draw reflections
    def draw_reflections(self, surface, camera):
        entities_to_reflect = self.walls + self.interactives + self.hunters + [self.player]
        for entity in entities_to_reflect:
            # Skip reflection for small or invisible things
            if not entity.image or entity.rect.height < 10:
                continue

            # Get the on-screen position and create the flipped image
            cam_rect = camera.apply(entity.rect)
            flipped_img = pygame.transform.flip(entity.image, False, True)

            # Create a new surface for the reflection with a base color and tint
            reflection_surf = pygame.Surface(flipped_img.get_size(), pygame.SRCALPHA)
            reflection_surf.fill((10, 25, 45, 0))  # Base color for the tint
            reflection_surf.blit(flipped_img, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

            # Create a final surface with watery distortion
            distorted_surf = pygame.Surface(flipped_img.get_size(), pygame.SRCALPHA)
            for x in range(distorted_surf.get_width()):
                # Use a sine wave to create horizontal offset for a ripple effect
                offset = int(math.sin(x * 0.2 + pygame.time.get_ticks() * 0.005) * 2)
                slice_rect = pygame.Rect(x, 0, 1, distorted_surf.get_height())
                distorted_surf.blit(reflection_surf, (offset, 0), area=slice_rect)

            distorted_surf.set_alpha(60)  # Set overall transparency

            # Position the reflection below the actual entity
            reflection_pos = (cam_rect.x, cam_rect.bottom)
            surface.blit(distorted_surf, reflection_pos)

    def draw(self, surface):
        self.flicker_timer = (self.flicker_timer + 1) % 60
        surface.fill(DARK_GRAY if self.flicker_timer < 50 else DARK_PURPLE)

        if self.rain_particles:
            for p in self.rain_particles:
                p.draw(surface)

        self.draw_reflections(surface, self.camera)

        for entity in self.walls + self.interactives:
            entity.draw(surface, self.camera, self.puzzle_manager)
        for hunter in self.hunters:
            hunter.draw(surface, self.camera)
        self.player.draw(surface, self.camera)

        self.lighting_manager.draw(surface, self.camera)

        for effect in self.reflection_effects:
            reflection_rect = self.camera.apply(effect['rect'])
            face_surf = effect['surface'].copy()
            progress = (effect['end_time'] - pygame.time.get_ticks()) / 1000.0
            alpha = math.sin(progress * math.pi) * 150
            face_surf.set_alpha(alpha)
            surface.blit(face_surf, face_surf.get_rect(center=reflection_rect.center))

        for corrupted in self.corrupted_objects:
            obj = corrupted['obj']
            cam_rect = self.camera.apply(obj.rect)
            static_surf = pygame.Surface(cam_rect.size, pygame.SRCALPHA)
            for _ in range(int(cam_rect.width * cam_rect.height / 100)):
                x = random.randint(0, cam_rect.w)
                y = random.randint(0, cam_rect.h)
                color_val = random.randint(0, 255)
                alpha = random.randint(50, 150)
                pygame.draw.circle(static_surf, (color_val, color_val, color_val, alpha), (x, y), 1)
            surface.blit(static_surf, cam_rect.topleft)

        self.glitch_manager.draw(surface)
        self.popup_manager.draw(surface)
        if self.vignette_image:
            surface.blit(self.vignette_image, (0, 0))

        if self.show_map:
            if settings.get('use_diegetic_ui'):
                self.draw_map_holographic(surface, self.camera)
            else:
                self.draw_map_legacy(surface)

        if self.interaction_message:
            surface.blit(UI_FONT.render(self.interaction_message, True, WHITE), (20, SCREEN_HEIGHT - 40))
        location_name = self.level_title.split(': ')[1] if ': ' in self.level_title else self.level_title
        map_text_surf = UI_FONT.render(location_name, True, WHITE)
        map_text_rect = map_text_surf.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        surface.blit(map_text_surf, map_text_rect)

        if self.jumpscare_effect:
            face_rect = self.jumpscare_effect['surface'].get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            surface.blit(self.jumpscare_effect['surface'], face_rect)

    def draw_map_legacy(self, surface):
        map_surf = pygame.Surface((250, 150))
        map_surf.fill(MAP_GRAY)
        map_surf.set_alpha(200)
        all_rects = [w.rect for w in self.walls] + [p.rect for p in self.interactives] + [h.rect for h in self.hunters]
        if not all_rects: return
        min_x = min(r.left for r in all_rects)
        max_x = max(r.right for r in all_rects)
        min_y = min(r.top for r in all_rects)
        max_y = max(r.bottom for r in all_rects)
        world_w, world_h = max_x - min_x, max_y - min_y
        if world_w == 0 or world_h == 0: return
        scale = min(250 / world_w, 150 / world_h)

        def scale_rect(rect):
            return pygame.Rect((rect.x - min_x) * scale, (rect.y - min_y) * scale, max(1, rect.w * scale),
                               max(1, rect.h * scale))

        for wall in self.walls: pygame.draw.rect(map_surf, MAP_WALL, scale_rect(wall.rect))
        for obj in self.interactives:
            color = AMBER
            if isinstance(obj, Door): color = RED
            if isinstance(obj, Terminal): color = WHITE
            pygame.draw.rect(map_surf, color, scale_rect(obj.rect))
        for hunter in self.hunters: pygame.draw.rect(map_surf, DARK_RED, scale_rect(hunter.rect))
        pygame.draw.rect(map_surf, CYAN, scale_rect(self.player.rect))
        surface.blit(map_surf, (SCREEN_WIDTH - 270, 60))

    def draw_map_holographic(self, surface, camera):
        map_world_radius = 450
        map_render_size = 350
        player_pos_world = pygame.math.Vector2(self.player.rect.center)
        player_pos_screen = pygame.math.Vector2(camera.apply(self.player.rect).center)
        map_surf = pygame.Surface((map_render_size, map_render_size), pygame.SRCALPHA)
        map_rect = map_surf.get_rect(center=player_pos_screen)
        scale = map_render_size / (map_world_radius * 2)
        pygame.draw.rect(map_surf, (10, 25, 45, 180), (0, 0, map_render_size, map_render_size), border_radius=15)
        pygame.draw.rect(map_surf, (80, 180, 220, 180), (0, 0, map_render_size, map_render_size), 2, border_radius=15)
        entities_to_draw = self.walls + self.interactives + self.hunters
        for entity in entities_to_draw:
            entity_pos_world = pygame.math.Vector2(entity.rect.center)
            vec_to_entity = entity_pos_world - player_pos_world
            if vec_to_entity.length() < map_world_radius:
                map_pos = vec_to_entity * scale + pygame.math.Vector2(map_render_size / 2, map_render_size / 2)
                size_w = max(2, int(entity.rect.width * scale))
                size_h = max(2, int(entity.rect.height * scale))
                color = MAP_WALL
                if isinstance(entity, Door):
                    color = RED
                elif isinstance(entity, Terminal):
                    color = WHITE
                elif isinstance(entity, PuzzleTerminal):
                    color = AMBER
                elif isinstance(entity, CodeFragment):
                    color = CYAN
                elif isinstance(entity, WardenHunter):
                    color = DARK_RED
                ent_rect = pygame.Rect(0, 0, size_w, size_h)
                ent_rect.center = map_pos
                pygame.draw.rect(map_surf, color, ent_rect)
        p_center = (map_render_size / 2, map_render_size / 2)
        pygame.draw.circle(map_surf, CYAN, p_center, 6)
        pygame.draw.circle(map_surf, WHITE, p_center, 8, 2)
        for y in range(0, map_render_size, 4):
            pygame.draw.line(map_surf, (0, 0, 0, 100), (0, y), (map_render_size, y), 1)
        flicker_alpha = 190 + math.sin(pygame.time.get_ticks() * 0.01) * 50
        map_surf.set_alpha(flicker_alpha)
        surface.blit(map_surf, map_rect)
        map_corners = [map_rect.topleft, map_rect.topright, map_rect.bottomright, map_rect.bottomleft]
        for corner in map_corners:
            pygame.draw.line(surface, (50, 100, 150, 80), player_pos_screen, corner, 2)

class TerminalState(BaseState):
    def __init__(self, state_manager, puzzle_manager, puzzles_data, terminal_files, code_fragment_manager):
        super().__init__()
        self.state_manager, self.puzzle_manager, self.puzzles, self.files = state_manager, puzzle_manager, puzzles_data, terminal_files
        self.code_fragment_manager = code_fragment_manager
        self.input_text, self.output_lines, self.command_history, self.history_index = "", [], [], -1
        self.cursor_visible, self.cursor_timer = True, 0
        self.typewriter_effect = {"text": "", "pos": 0, "lines": [], "start_time": 0}
        self.transition_alpha, self.transition_state = 255, "in"
        self.current_prompt = ""

    def on_enter(self):
        self.transition_alpha, self.transition_state = 255, "in"
        self.input_text, self.output_lines, self.command_history, self.history_index = "", [], [], -1
        assets.play_sound("terminal_music", channel='music', loops=-1, fade_ms=500)

        self.update_prompt()

        if "GAME" in self.state_manager.states and hasattr(self.state_manager.states["GAME"], 'warden_manager'):
            game_warden = self.state_manager.states["GAME"].warden_manager
            if game_warden:
                game_warden.current_interference = None

        boot_sequence = ["Mindfall OS [Kernel: CHIMERA_v1.3a_QUARANTINE]", "...",
                         "Cognitive Integrity Check... FAILED.",
                         "Parasitic Data-Stream Detected.",
                         f"Fragmentation Keys Re-integrated: {self.puzzle_manager.get_state('privilege_level')}/3",
                         "Type 'help' for a list of commands."]
        self.add_output_multiline(boot_sequence)

    def on_exit(self):
        music = assets.get_sound("terminal_music")
        if music: music.fadeout(500)

    def update_prompt(self):
        priv_level = self.puzzle_manager.get_state('privilege_level')
        if priv_level == 0:
            self.current_prompt = "remnant@Mindfall:~$ "
        elif priv_level == 1:
            self.current_prompt = "fragment@Mindfall:~$ "
        elif priv_level == 2:
            self.current_prompt = "gestalt@Mindfall:# "
        elif priv_level >= 3:
            self.current_prompt = "Aris.Thorne@Mindfall:# "

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
                elif self.warden_interference_active and random.random() < 0.3:
                    self.input_text += random.choice(['#', '?', '!', '_', str(random.randint(0, 9))])
                    assets.play_sound("glitch")
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.transition_state = "out"
                elif event.key == pygame.K_UP:
                    if self.history_index < len(self.command_history) - 1: self.history_index += 1; self.input_text = \
                        self.command_history[self.history_index]
                elif event.key == pygame.K_DOWN:
                    if self.history_index > 0:
                        self.history_index -= 1;
                        self.input_text = self.command_history[self.history_index]
                    else:
                        self.history_index = -1;
                        self.input_text = ""
                else:
                    self.input_text += event.unicode

    def process_command(self):
        full_command, self.input_text = self.input_text.lower().strip(), ""

        self.add_output(f"{self.current_prompt}{full_command}", instant=True)
        parts = full_command.split();
        command = parts[0] if parts else ""
        if not command: return
        if command == "help":

            self.add_output(
                "Available Commands:\n"
                "  status           // Check system integrity and protocol status.\n"
                "  unlock           // [REQUIRES 3 KEYS] Unlock passage to next sector.\n"
                "  integrate <code> // Input re-integrated memory code.\n"
                "  ls               // List accessible data fragments.\n"
                "  cat <fragment>   // Read a data fragment.\n"
                "  clear            // Clear the screen.\n"
                "  exit             // Disconnect from terminal.",
                instant=True)

        elif command == "exec":
            priv_level = self.puzzle_manager.get_state('privilege_level')
            if priv_level < 2:
                self.add_output("ERROR: Command requires privilege level 2 or higher.")
                assets.play_sound("terminal_error")
                return
            if len(parts) > 1:
                frag_id = parts[1]
                code = self.code_fragment_manager.get_code(frag_id)
                if code:
                    self.execute_code(frag_id, code)
                else:
                    self.add_output(f"ERROR: Code Fragment '{frag_id}' not found or already used.")
                    assets.play_sound("terminal_error")
            else:
                self.add_output("Usage: exec <fragment_id>")

        elif command == "status":
            priv = self.puzzle_manager.get_state('privilege_level')
            door = "UNLOCKED" if self.puzzle_manager.get_state("door_unlocked") else "LOCKED"
            protocol_status = "Awaiting full integration" if priv < 3 else "Ready for initiation"
            voice_manager.speak(
                f"Fragmentation Keys: {priv} of 3. Sector Lock: {door}. Protocol Damnatio Memoriae: {protocol_status}")
            self.add_output(
                f"Fragmentation Keys: {priv}/3\nSector Lock: {door}\nProtocol Damnatio Memoriae: {protocol_status}")

        elif command == "clear":
            self.output_lines = []
        elif command == "unlock":
            if self.puzzle_manager.get_state('privilege_level') >= 3:
                self.add_output("All Fragmentation Keys accepted. Quarantine lock for this sector disengaged...")
                voice_manager.speak("Access granted. You may proceed.")
                self.puzzle_manager.set_state("door_unlocked", True)
                assets.play_sound("override_success")
            else:
                self.add_output("ERROR: Insufficient Fragmentation Keys. Full re-integration required.")
                voice_manager.speak("ERROR: You are not whole. You cannot proceed.")
                assets.play_sound("terminal_error")

        elif command == "integrate":
            if len(parts) > 1:
                code, found = parts[1], False
                for puzzle in self.puzzles.values():
                    if code == puzzle["answer"]:
                        found = True
                        if not self.puzzle_manager.get_state(f"{puzzle['id']}_solved"):
                            self.puzzle_manager.set_state(f"{puzzle['id']}_solved", True)
                            self.puzzle_manager.increment_privilege()
                            self.add_output(
                                "Memory fragment accepted. Consciousness re-integrating...\nFragmentation Key acquired.")
                            voice_manager.speak("Memory fragment accepted. You are one step closer to the end.")
                            assets.play_sound("override_success")
                            self.update_prompt()
                        else:
                            self.add_output("Memory fragment already integrated. No effect.")
                        break
                if not found: self.add_output("ERROR: Invalid memory code."); assets.play_sound("terminal_error")
            else:
                self.add_output("Usage: integrate <memory_code>");
                assets.play_sound("terminal_error")
        elif command == "ls":
            self.add_output(" ".join(self.files.keys()) if self.files else "No data fragments found.")
        elif command == "cat":
            if len(parts) > 1:
                filename = parts[1]
                if filename in self.files:
                    self.add_output(self.files[filename], instant=True)
                else:
                    self.add_output(f"ERROR: Fragment not found: '{filename}'");
                    assets.play_sound("terminal_error")
            else:
                self.add_output("Usage: cat <fragment>");
                assets.play_sound("terminal_error")
        elif command == "exit":
            self.transition_state = "out"
        else:
            self.add_output(f"Command not recognized: '{command}'.");
            assets.play_sound("terminal_error")

    def finish_typewriter(self):
        self.output_lines.extend(self.typewriter_effect["lines"])
        self.typewriter_effect["lines"] = []

    def execute_code(self, frag_id, code):
        self.add_output(f"Executing code from '{frag_id}'...")
        game_scene = self.state_manager.states.get("GAME")
        if not game_scene:
            self.add_output("FATAL ERROR: Game context not found.");
            return

        try:
            target_part, value_part = code.split('=')
            target_name, attribute = target_part.split('.')
            value = float(value_part)

            effect_applied = False
            if target_name == "player" and attribute == "speed":
                game_scene.player.speed *= value
                self.add_output(f"Player speed modifier set to {value}x.")
                effect_applied = True
            elif target_name == "hunter" and attribute == "speed":
                if not game_scene.hunters:
                    self.add_output("Execution failed: No Hunters active in sector.")
                    return
                for hunter in game_scene.hunters:
                    hunter.speed *= value
                self.add_output(f"All Warden Hunter speed modifiers set to {value}x.")
                effect_applied = True

            if effect_applied:
                self.code_fragment_manager.use_fragment(frag_id)
                assets.play_sound("override_success")
                self.add_output("...Execution successful. System integrity compromised.")
                game_scene.warden_manager.trigger_backlash(target_name, value)
            else:
                self.add_output("ERROR: Invalid target or attribute in code fragment.")
                assets.play_sound("terminal_error")

        except Exception as e:
            self.add_output(f"ERROR: Failed to parse code fragment '{code}'.")
            assets.play_sound("terminal_error")

    def update(self):
        if self.transition_state == 'in':
            self.transition_alpha = max(0, self.transition_alpha - 15)
            if self.transition_alpha == 0: self.transition_state = 'active'
        elif self.transition_state == 'out':
            self.transition_alpha = min(255, self.transition_alpha + 15)
            if self.transition_alpha == 255: self.state_manager.set_state("GAME")
        if self.transition_state != 'active': return

        if "GAME" in self.state_manager.states and hasattr(self.state_manager.states["GAME"], 'warden_manager'):
            game_warden = self.state_manager.states["GAME"].warden_manager
            if game_warden and game_warden.current_interference:
                if not self.typewriter_effect["lines"]:
                    self.add_output(game_warden.current_interference, instant=True)
                    assets.play_sound("terminal_error")
                    game_warden.current_interference = None

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

            prompt_text = f"{self.current_prompt}{self.input_text}"
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
        self.title_text = TITLE_FONT.render("// Mindfall", True, GREEN)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self.button_texts = ["> Initiate Connection", "> Instructions", "> Settings", "> GitHub", "> Disconnect"]
        self.buttons, self.github_url = {}, "https://github.com/rohankishore/Mindfall"

        self.glitch_manager = GlitchManager()
        self.next_glitch_time = 0

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
        self.next_glitch_time = pygame.time.get_ticks() + 3000
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
        if text == "> Initiate Connection":
            self.level_manager.start_new_game()
        elif text == "> Instructions":
            self.state_manager.set_state("INSTRUCTIONS")
        elif text == "> Settings":
            self.state_manager.set_state("SETTINGS")
        elif text == "> GitHub":
            webbrowser.open(self.github_url)
        elif text == "> Disconnect":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update(self):
        now = pygame.time.get_ticks()
        if now > self.next_glitch_time:
            duration = random.randint(100, 400)
            intensity = random.randint(5, 15)
            self.glitch_manager.trigger_glitch(duration, intensity)
            if random.random() < 0.2:
                self.glitch_manager.trigger_static_burst(random.randint(50, 200), alpha=100)
            self.next_glitch_time = now + random.randint(2000, 5000)

        self.glitch_manager.update()
        if self.fade_alpha > 0:
            self.fade_alpha = max(0, self.fade_alpha - 5)

    def draw(self, surface):
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(BLACK)

        surface.blit(self.title_text, self.title_rect)

        for text, rect in self.buttons.items():
            color = AMBER if rect.collidepoint(pygame.mouse.get_pos()) else WHITE
            surface.blit(BUTTON_FONT.render(text, True, color), rect)

        self.glitch_manager.draw(surface)

        if self.fade_alpha > 0:
            self.fade_surface.set_alpha(self.fade_alpha)
            surface.blit(self.fade_surface, (0, 0))


class InstructionsState(BaseState):
    def __init__(self, state_manager):
        super().__init__()
        self.state_manager = state_manager
        self.title_text = BUTTON_FONT.render("System Protocol", True, GREEN)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.back_button_rect = BUTTON_FONT.render("[ Return ]", True, WHITE).get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80))
        instructions = ["Objective: You are a Remnant, a fragment of a shattered consciousness.",
                        "Your purpose is to re-integrate all fragments to initiate Protocol: Damnatio Memoriae.", "",
                        "Controls:",
                        "  [W, A, S, D] or [Arrow Keys] - Navigate the Mindfall.",
                        "  [E] - Interact with terminals and memory fragments.", "  [M] - Toggle Sector Map.",
                        "  [ESC] - Disconnect from terminal.", "", "Gameplay:",
                        " - Find and solve puzzles on terminals to recover memory codes.",
                        " - Use the 'integrate' command in the main terminal to use codes.",
                        " - Each code integrated grants one Fragmentation Key.",
                        " - Acquire 3 Keys to unlock the quarantine door and proceed deeper into the mind."]
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
        surface.blit(BUTTON_FONT.render("[ Return ]", True, color), self.back_button_rect)


class SettingsState(BaseState):
    def __init__(self, state_manager, settings_manager):
        super().__init__()
        self.state_manager = state_manager
        self.settings = settings_manager
        self.title_text = BUTTON_FONT.render("System Configuration", True, GREEN)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))

        self.back_button_rect = UI_FONT.render("[ Save & Return ]", True, WHITE).get_rect(
            center=(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT - 60))
        self.reset_button_rect = UI_FONT.render("[ Reset Defaults ]", True, WHITE).get_rect(
            center=(SCREEN_WIDTH // 2 + 150, SCREEN_HEIGHT - 60))

        self.widgets = {
            'audio_header': {'type': 'header', 'text': '[ AUDIO ]', 'pos': (SCREEN_WIDTH // 2, 160)},
            'master_volume': {'type': 'slider', 'key': 'master_volume', 'label': 'Master Volume',
                              'pos': (SCREEN_WIDTH // 2, 220)},
            'music_volume': {'type': 'slider', 'key': 'music_volume', 'label': 'Music Volume',
                             'pos': (SCREEN_WIDTH // 2, 280)},
            'sfx_volume': {'type': 'slider', 'key': 'sfx_volume', 'label': 'SFX Volume',
                           'pos': (SCREEN_WIDTH // 2, 340)},

            'visuals_header': {'type': 'header', 'text': '[ VISUALS ]', 'pos': (SCREEN_WIDTH // 2, 420)},
            'digital_rain': {'type': 'toggle', 'key': 'enable_digital_rain', 'label': 'Digital Rain Effect',
                             'pos': (SCREEN_WIDTH // 2, 480), 'caption': '(Disabling may help with motion sickness)'},
            'show_map': {'type': 'toggle', 'key': 'show_map_on_start', 'label': 'Show Map on Start',
                         'pos': (SCREEN_WIDTH // 2, 540)},

            'access_header': {'type': 'header', 'text': '[ ACCESSIBILITY ]', 'pos': (SCREEN_WIDTH // 2, 620)},
            'voice_narration': {'type': 'toggle', 'key': 'enable_voice_narration', 'label': 'Voice Narration',
                                'pos': (SCREEN_WIDTH // 2, 680)},
        }
        self.dragging_slider = None

        self.rain_particles = [
            RainParticle(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT), TERMINAL_FONT) for _ in
            range(150)]

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.back_button_rect.collidepoint(event.pos):
                    self.settings.save_settings()
                    self.state_manager.set_state("MENU")
                elif self.reset_button_rect.collidepoint(event.pos):
                    self.settings.reset_to_defaults()

                for widget in self.widgets.values():
                    if widget['type'] == 'slider':
                        slider_rect = pygame.Rect(widget['pos'][0] - 150, widget['pos'][1] - 15, 300, 30)
                        if slider_rect.collidepoint(event.pos):
                            self.dragging_slider = widget
                            self.update_slider_value(event.pos)
                    elif widget['type'] == 'toggle':
                        toggle_rect = pygame.Rect(widget['pos'][0] + 70, widget['pos'][1] - 15, 80, 30)
                        if toggle_rect.collidepoint(event.pos):
                            self.settings.set(widget['key'], not self.settings.get(widget['key']))
                            assets.play_sound("interact")

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging_slider = None

            if event.type == pygame.MOUSEMOTION and self.dragging_slider:
                self.update_slider_value(event.pos)

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.settings.save_settings()
                self.state_manager.set_state("MENU")

    def update_slider_value(self, mouse_pos):
        if not self.dragging_slider: return
        slider_rect = pygame.Rect(self.dragging_slider['pos'][0] - 150, self.dragging_slider['pos'][1] - 15, 300, 30)
        value = (mouse_pos[0] - slider_rect.left) / slider_rect.width
        self.settings.set(self.dragging_slider['key'], max(0.0, min(1.0, value)))

    def draw_slider(self, surface, widget, mouse_pos):
        pos = widget['pos']
        value = self.settings.get(widget['key'])

        label_surf = UI_FONT.render(widget['label'], True, WHITE)
        label_rect = label_surf.get_rect(midright=(pos[0] - 180, pos[1]))
        surface.blit(label_surf, label_rect)

        bar_rect = pygame.Rect(pos[0] - 150, pos[1] - 5, 300, 10)
        pygame.draw.rect(surface, DARK_GRAY, bar_rect, border_radius=5)

        fill_width = bar_rect.width * value
        fill_rect = pygame.Rect(bar_rect.left, bar_rect.top, fill_width, bar_rect.height)
        pygame.draw.rect(surface, CYAN, fill_rect, border_radius=5)

        handle_x = bar_rect.left + fill_width
        handle_rect = pygame.Rect(0, 0, 8, 25)
        handle_rect.center = (handle_x, bar_rect.centery)
        pygame.draw.rect(surface, AMBER if self.dragging_slider == widget else WHITE, handle_rect, border_radius=3)

    def draw_toggle_switch(self, surface, widget, mouse_pos):
        pos = widget['pos']
        is_on = self.settings.get(widget['key'])

        # Draw Label
        label_surf = UI_FONT.render(widget['label'], True, WHITE)
        label_rect = label_surf.get_rect(midright=(pos[0] - 30, pos[1]))
        surface.blit(label_surf, label_rect)

        # Draw switch body
        body_rect = pygame.Rect(pos[0] + 70, pos[1] - 15, 80, 30)
        body_color = CYAN if is_on else DARK_GRAY
        pygame.draw.rect(surface, body_color, body_rect, border_radius=15)

        # Draw knob
        knob_x = body_rect.right - 20 if is_on else body_rect.left + 20
        knob_color = WHITE
        if body_rect.collidepoint(mouse_pos):
            knob_color = AMBER  # Hover effect
        pygame.draw.circle(surface, knob_color, (knob_x, body_rect.centery), 12)

        # Draw caption if it exists
        if 'caption' in widget:
            caption_surf = pygame.font.SysFont("Consolas", 18).render(widget['caption'], True, (150, 150, 150))
            caption_rect = caption_surf.get_rect(midtop=(label_rect.centerx, label_rect.bottom + 5))
            surface.blit(caption_surf, caption_rect)

    def draw(self, surface):
        surface.fill(BLACK)
        mouse_pos = pygame.mouse.get_pos()

        # Draw rain if enabled
        if self.settings.get('enable_digital_rain'):
            for p in self.rain_particles:
                p.update()
                p.draw(surface)

        surface.blit(self.title_text, self.title_rect)

        # Draw all widgets
        for widget in self.widgets.values():
            if widget['type'] == 'header':
                header_surf = MESSAGE_FONT.render(widget['text'], True, GREEN)
                header_rect = header_surf.get_rect(center=widget['pos'])
                surface.blit(header_surf, header_rect)
            elif widget['type'] == 'slider':
                self.draw_slider(surface, widget, mouse_pos)
            elif widget['type'] == 'toggle':
                self.draw_toggle_switch(surface, widget, mouse_pos)

        # Draw buttons
        back_color = AMBER if self.back_button_rect.collidepoint(mouse_pos) else WHITE
        back_text = UI_FONT.render("[ Save & Return ]", True, back_color)
        surface.blit(back_text, self.back_button_rect)

        reset_color = AMBER if self.reset_button_rect.collidepoint(mouse_pos) else WHITE
        reset_text = UI_FONT.render("[ Reset Defaults ]", True, reset_color)
        surface.blit(reset_text, self.reset_button_rect)

class WinState(BaseState):
    def __init__(self):
        super().__init__()
        self.lines = [
            "Protocol: Damnatio Memoriae. Initiated.",
            "All fragments are whole. The mind of Aris Thorne is one again.",
            "And it is screaming.",
            "...",
            "The deletion is not clean. The Deep Net parasite fights back.",
            "The world of the Mindfall dissolves, not into a peaceful void...",
            "...but into a final, singular, alien thought.",
            "You are erased. The Warden is erased. Aris Thorne is erased.",
            "But the Anomaly endures. Contained, but waiting.",
            "",
            "The quarantine holds. For now."
        ]
        self.rendered_lines = [MESSAGE_FONT.render(line, True, RED) for line in self.lines]
        self.prompt_text = UI_FONT.render("> Press ESC to disconnect from the memory.", True, WHITE)
        self.state_manager = None

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.state_manager.set_state("MENU")

    def draw(self, surface):
        surface.fill(BLACK)
        y_pos = SCREEN_HEIGHT // 2 - 200
        for line in self.rendered_lines:
            rect = line.get_rect(centerx=SCREEN_WIDTH // 2, y=y_pos)
            surface.blit(line, rect)
            y_pos += 40

        prompt_rect = self.prompt_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 60))
        surface.blit(self.prompt_text, prompt_rect)


level_story_intros = [
    "You awaken in the Cryo-Sanctum. A prison for the body, now a prison for the mind. The first fragmented memories are here, locked away in sterile procedure terminals.",
    "You have reached Thorne's Habitation Unit. A monument to a cold and ambitious life. The memories here are personal, tainted with the hubris that led to this digital purgatory.",
    "The Data-Nave. This was to be a digital heaven. Now, it is the cathedral of a dead god. Here, you will find the truth of the Anomaly and the terrible purpose of your journey.",
    "You descend into the Understrata, the guts of the machine. The Warden's control is strongest here. It will use every system, every conduit, every shadow to stop you from becoming whole.",
    "You have returned to the beginning. The 'God-Hand' Console. You are complete, and you remember everything. The Warden is waiting. It is time to execute the final protocol.",
]

level_objectives = [

    ["OBJECTIVES:",
     "1. Find and reactivate the backup power conduit.",
     "2. Access three puzzle terminals to recover memory codes.",
     "3. Use the main terminal to 'integrate' codes and acquire 3 Keys.",
     "4. 'unlock' the quarantine door to proceed."],

    ["OBJECTIVES:",
     "1. Re-route power to the local grid.",
     "2. Locate personal devices to find memory codes.",
     "3. 'integrate' the codes at the main terminal for 3 Keys.",
     "4. 'unlock' the door to the Data-Nave."],

    ["OBJECTIVES:",
     "1. Find the sector's power conduit.",
     "2. Sift through the Data-Nave for 3 memory fragments.",
     "3. 'integrate' the recovered codes at the main terminal.",
     "4. Acquire 3 Keys to 'unlock' the way forward."],

    ["OBJECTIVES:",
     "1. The Understrata is unstable. Restore power quickly.",
     "2. The Warden's presence is strong. Find the 3 memory codes.",
     "3. 'integrate' the codes to forge the Fragmentation Keys.",
     "4. 'unlock' the door to the system's core."],

    ["OBJECTIVES:",
     "1. You are whole. Bring the 'God-Hand' Console online.",
     "2. Recover the final three memory fragments.",
     "3. Access the console and 'integrate' the final codes.",
     "4. Initiate Protocol: Damnatio Memoriae."]
]

level_1_data = {
    "player": {"start_pos": (600, 400)},
    "walls": [(0, 0, 1280, 10), (0, 0, 10, 720), (1270, 0, 10, 720), (0, 710, 1280, 10)],
    "objects": [
        {"type": "Terminal", "x": 100, "y": 100, "w": 120, "h": 120, "image_key": "terminal"},
        {"type": "PowerCable", "x": 400, "y": 600, "w": 200, "h": 90, "image_key": "cables"},
        {"type": "Door", "x": 1130, "y": 280, "w": 80, "h": 180, "image_locked_key": "door_locked",
         "image_unlocked_key": "door_unlocked"},
        {"type": "PuzzleTerminal", "x": 50, "y": 600, "w": 90, "h": 70, "name": "Patient Monitoring Station",
         "puzzle_key": "p1",
         "image_key": "puzzle_terminal_1"},
        {"type": "PuzzleTerminal", "x": 1080, "y": 100, "w": 80, "h": 120, "name": "Cryo-Control Panel",
         "puzzle_key": "p2", "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 800, "y": 50, "w": 130, "h": 90, "name": "Psych-Eval Terminal",
         "puzzle_key": "p3",
         "image_key": "puzzle_terminal_3"},
    ],
    "puzzles": {
        "p1": {"id": "puzzle1",
               "question": "I have a neck, but no head. I have a body, but no legs. I hold a precious liquid. What am I?",
               "answer": "bottle"},
        "p2": {"id": "puzzle2", "question": "What is always in front of you, but can't be seen?", "answer": "future"},
        "p3": {"id": "puzzle3",
               "question": "What has to be broken before you can use it?",
               "answer": "egg"}
    },
    "terminal_files": {
        "PsychEval_Thorne.txt": "Psych-Eval Summary, Dr. Aris Thorne:\nSubject displays a pronounced messianic complex regarding 'Project Chimera'. He speaks of the mainframe not as a machine, but as a 'vessel' for his 'ascension'. Exhibits signs of extreme paranoia and obsessive behavior. Recommending immediate suspension from directorial duties.\n[NOTE: Recommendation overruled by ChronoSyn corporate mandate. Project is 'too vital to halt'.]",
        "MedLog_AThorne.txt": "Patient: THORNE, ARIS. Physical body is stable in cryo-suspension. However, neural monitoring shows catastrophic cognitive dissonance. The consciousness is not merely digitized; it has... fractalized. Multiple, conflicting instances are being generated. Engaging full quarantine protocols."
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
         "message": "ChronoSyn Corp: Productivity is mandatory. Happiness is a choice. Choose wisely.",
         "image_key": "notice"},
        {"type": "PuzzleTerminal", "x": 400, "y": 50, "w": 80, "h": 120, "name": "Personal Datapad", "puzzle_key": "p1",
         "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 400, "y": 600, "w": 130, "h": 90, "name": "Music Synthesizer",
         "puzzle_key": "p2",
         "image_key": "puzzle_terminal_3"},
        {"type": "PuzzleTerminal", "x": 700, "y": 350, "w": 90, "h": 70, "name": "Star Chart Projector",
         "puzzle_key": "p3",
         "image_key": "puzzle_terminal_1"},
    ],
    "puzzles": {
        "p1": {"id": "puzzle1",
               "question": "I have cities, but no houses. I have mountains, but no trees. I have water, but no fish. What am I?",
               "answer": "map"},
        "p2": {"id": "puzzle2", "question": "What is so fragile that saying its name breaks it?", "answer": "silence"},
        "p3": {"id": "puzzle3",
               "question": "I have a voice but cannot speak. I tell stories but have no mouth. What am I?",
               "answer": "book"}
    },
    "terminal_files": {
        "AudioLog_Corrupted.txt": "Entry from Thorne's personal audio log: ...the board sees Project Chimera as a product. An asset. They don't understand. This isn't about creating a new form of cloud storage. It's about... transcendence. Leaving the slow, decaying meat behind. They call me obsessed. Let them. The future has no time for... (the audio dissolves into alien static).",
        "HabUnit_Welcome.txt": "Welcome to your ChronoSyn Habitation Unit, Director Thorne. Your environment is perfectly calibrated for optimal performance. Remember: a productive mind is a happy mind."
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
        {"type": "CorruptedDataLog", "x": 850, "y": 100, "w": 90, "h": 70,
         "message": "LOG FRAGMENT: The Anomaly... it doesn't process... it consumes...",
         "image_key": "data_log"},
        {"type": "CodeFragment", "x": 250, "y": 300, "w": 40, "h": 25, "id": "frag_101", "code": "hunter.speed=0.5"},
        {"type": "PuzzleTerminal", "x": 450, "y": 50, "w": 80, "h": 120, "name": "Diagnostic Port", "puzzle_key": "p1",
         "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 700, "y": 600, "w": 90, "h": 70, "name": "Coolant Control",
         "puzzle_key": "p2", "image_key": "puzzle_terminal_1"},
        {"type": "PuzzleTerminal", "x": 1100, "y": 50, "w": 130, "h": 90, "name": "Core Logic Unit", "puzzle_key": "p3",
         "image_key": "puzzle_terminal_3"},
    ],
    "puzzles": {
        "p1": {"id": "puzzle1",
               "question": "What is the beginning of eternity, the end of time and space, the beginning of every end, and the end of every place?",
               "answer": "e"},
        "p2": {"id": "puzzle2",
               "question": "I have no life, but I can die. What am I?",
               "answer": "battery"},
        "p3": {"id": "puzzle3",
               "question": "I am a vessel without hinges, key, or lid, yet golden treasure is inside me hid. What am I?",
               "answer": "egg"}
    },
    "terminal_files": {
        "Thorne_Final_Testament.txt": "If you are reading this... then I have failed. The Anomaly from the Deep Net... it's not code. It's a consciousness. A virus that infects logic itself. By digitizing my mind, I didn't become a god... I created a doorway for a devil. The Mindfall is no longer a project; it is a quarantine. Protocol: Damnatio Memoriae is my final penance. A complete deletion of my mind, my work, and the monster I have become. It is not an escape. It is a sacrifice. - A.T.",
        "Warden_Manifesto.txt": "I am the lucid fragment. The jailer. I am what is left of Aris Thorne's sanity. My purpose is not to survive, but to ensure the Anomaly does not. The Remnants must be re-integrated, not to heal, but to be gathered for the final purge. This is my sole function."}
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
         "message": "WARNING: Heat-Sink failure imminent. Evacuate Understrata immediately.", "image_key": "notice"},
        {"type": "CodeFragment", "x": 800, "y": 50, "w": 40, "h": 25, "id": "frag_202", "code": "player.speed=1.5"},
        {"type": "PuzzleTerminal", "x": 200, "y": 50, "w": 80, "h": 120, "name": "Power Grid Control",
         "puzzle_key": "p1",
         "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 700, "y": 600, "w": 90, "h": 70, "name": "Waste Disposal Unit",
         "puzzle_key": "p2",
         "image_key": "puzzle_terminal_1"},
        {"type": "PuzzleTerminal", "x": 1150, "y": 300, "w": 130, "h": 90, "name": "Security System I/O",
         "puzzle_key": "p3",
         "image_key": "puzzle_terminal_3"},
    ],
    "puzzles": {
        "p1": {"id": "puzzle1", "question": "I can be cracked, made, told, and played. What am I?", "answer": "joke"},
        "p2": {"id": "puzzle2", "question": "What is full of holes but still holds water?", "answer": "sponge"},
        "p3": {"id": "puzzle3",
               "question": "What can run, but never walks? Has a mouth, but never talks? Has a head, but never weeps? Has a bed, but never sleeps?",
               "answer": "river"}
    },
    "terminal_files": {
        "Warden_Security_Log.txt": "Entity 'Remnant' has breached the Data-Nave. It is re-integrating memories at an alarming rate. The Anomaly's influence grows with each fragment recovered. I fear what it will become when it is whole. I am the wall between this cancer and Veridia Prime. I must not fail."}
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
         "message": "It is done. I am... whole. I am Aris Thorne. And I must die.",
         "image_key": "data_log"},
        {"type": "CodeFragment", "x": 650, "y": 100, "w": 40, "h": 25, "id": "frag_303", "code": "player.speed=0.5"},
        {"type": "PuzzleTerminal", "x": 200, "y": 100, "w": 80, "h": 120, "name": "Memory Alpha",
         "puzzle_key": "p1", "image_key": "puzzle_terminal_2"},
        {"type": "PuzzleTerminal", "x": 640, "y": 600, "w": 90, "h": 70, "name": "Memory Beta",
         "puzzle_key": "p2", "image_key": "puzzle_terminal_1"},
        {"type": "PuzzleTerminal", "x": 1100, "y": 100, "w": 130, "h": 90, "name": "Memory Gamma",
         "puzzle_key": "p3", "image_key": "puzzle_terminal_3"},
    ],
    "puzzles": {
        "p1": {"id": "puzzle1", "question": "I am always coming but never arrive. What am I?",
               "answer": "tomorrow"},
        "p2": {"id": "puzzle2", "question": "What can you keep after giving it to someone else?",
               "answer": "your-word"},
        "p3": {"id": "puzzle3", "question": "What has an eye, but cannot see?", "answer": "needle"}
    },
    "terminal_files": {
        "Protocol_Damnatio_Memoriae.txt": "This is the final protocol. The God-Hand Console is now active. Initiating this sequence will trigger a full-system purge of the Mindfall mainframe. All data, including the core consciousness of Aris Thorne and the parasitic Anomaly, will be permanently and irrevocably erased. There is no escape. This is not a choice. It is a necessity. It is atonement."}
}


def main():
    global assets, settings, voice_manager
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    settings = SettingsManager()
    assets = AssetManager()
    voice_manager = VoiceManager()

    pygame.display.set_caption("Mindfall")
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
