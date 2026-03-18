import pygame
import sys
import os
import time
import threading
from groq import Groq
from helpers import (
    word_wrap,
    extract_status_from_response,
    parse_character_info,
)
from dotenv import load_dotenv

load_dotenv()

# Constants
# Fixed values within the program so theres not random numbers floating around

SCREEN_WIDTH = 800  # Width of the game window in pixels
SCREEN_HEIGHT = 600  # Height of the game window in pixels
FPS = 60  # Target frames per second
GROQ_MODEL = "llama-3.3-70b-versatile"  # Name of AI model we want to use

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BG = (20, 24, 30)  # The dark background color for the chat screen
GRAY = (140, 140, 140)  # Used for subtle hints and dividers
INPUT_BG = (50, 56, 66)  # Background color of the text input box
USER_COLOR = (80, 160, 255)  # Blue — color used for the player's messages
AI_COLOR = (220, 180, 100)  # Gold — color used for the AI character's messages
SYSTEM_COLOR = (160, 160, 160)  # Gray — color for system messages
RED_ACCENT = (255, 100, 100)  # Red — used for rejection banners
TOP_BAR_BG = (40, 44, 52)  # Slightly lighter dark color for the top name bar

# Prompts
# These are the text instructions sent to the AI to control its behavior

# This prompt tells the AI to generate a new random character with specific fields
# The format at the end is important — parse_character_info() will split this by "NAME:", "JOB:" etc
CHARACTER_GENERATION_PROMPT = """You are a character generator for a dating sim game. Generate a unique character with:
- A first name
- A job (Teacher, Cybersecurity analyst, Plumber, Marine biologist, Tattoo artist, Park ranger, Pizza maker, LEGO master builder, Snake charmer,etc.)
- A personality (2-3 strong traits, make them interesting and varied)
- A short backstory (2-3 sentences)
- Their dating dealbreakers and what they find attractive

Respond in EXACTLY this format (no extra text):
NAME: <n>
JOB: <job>
PERSONALITY: <personality>
BACKSTORY: <backstory>
LIKES: <what attracts them>
DEALBREAKERS: <what repels them>"""

# This is a template for the "system prompt" — the hidden instructions that define how the AI behaves
# The [STATUS:...] tags at the end of every AI message are how we know when the date ends.
# Feel free to change it around a bit
DATE_SYSTEM_PROMPT_TEMPLATE = """You are a character in a dating sim game. Stay in character at ALL times.

Your character:
{character_description}

You are open to dating but not a pushover. The player needs to show genuine interest
in you as a person. Be charming and flirty if they treat you well, but don't just
agree immediately. It should take a few good exchanges before you agree.

RULES:
- Respond in character with 1-3 sentences. Keep it conversational and snappy.
- Track your internal affection level (hidden from player).
- At the END of every message, append one of these tags (REQUIRED, always include):
  [STATUS:ongoing] - conversation continues
  [STATUS:accepted] - you agree to date the player (only after genuine convincing)
  [STATUS:rejected] - you reject the player (they said something truly awful or you're fed up)
- The status tag must be the very last thing in your message.
- Never mention or explain the status tags. They are invisible to the player.
- Be creative, funny, and engaging. Each character should feel distinct."""


# ─── STAGE 3: AI CLIENT ───────────────────────────────────────────────────────
# AI client class responsible for communicating with the GROQ api
class AIClient:
    def __init__(self):
        # TODO Stage 3: load API key and connect to Groq
        # We aint doing that yet so its empty
        self.client = None

    def send_messages(self, messages):
        # TODO Stage 3: send messages to Groq and return response text
        # Currently hardcoded
        return "Hi there! Nice to meet you. [STATUS:ongoing]"

    def generate_character(self):
        # TODO Stage 3: ask AI to generate a character
        # Currently hardcoded
        fake = "NAME: Alex\nJOB: Barista\nPERSONALITY: Friendly, witty\nBACKSTORY: Alex loves coffee.\nLIKES: Good conversation\nDEALBREAKERS: Rudeness"
        return parse_character_info(fake), fake


# ─── DATE SCENE ───────────────────────────────────────────────────────────────
# Date scene that basically handles everything, chat log, input and allat

class DateScene:
    def __init__(self, screen, ai_client):
        self.screen = screen  # The pygame Surface representing the entire window
        self.ai = (
            ai_client  # The AIClient instance we created above for making API calls
        )

        # Set fonts
        self.font = pygame.font.SysFont("comic_sans", 16)  # Main chat text
        self.font_title = pygame.font.SysFont(
            "comic_sans", 22, bold=True
        )  # Top bar title
        self.font_small = pygame.font.SysFont("comic_sans", 14)  # Hints and small text

        # chat_log is a list of (sender, text, color) tuples for display purposes only
        self.chat_log = []
        # conversation_history is the full message list sent to the AI API each time
        # All new messages from the ai and the user are appended at the end to provide full context
        self.conversation_history = []
        # The text the player is currently typing in the input box
        self.typed_text = ""
        # How many pixels the chat has been scrolled down (for when messages overflow)
        self.scroll_offset = 0
        # Tracks where we are in the date: "loading","ongoing","accepted","rejected"
        self.date_status = "loading"
        # Flag to prevent sending another message while waiting for the AI to respond
        self.waiting_for_ai = False

        # filled in once the AI generates a character (name, job, etc.)
        self.character_info = {}

        # add a loading message at the start
        self.add_to_chat("system", "Finding someone for you to meet...", SYSTEM_COLOR)
        # Start da character generation on a background thread
        self._start_character_generation()

    def add_to_chat(self, sender, text, color):
        # Lil helper to add da messages to the chatlog
        # Also croll to the bottom so the new message is always visible.
        self.chat_log.append((sender, text, color))
        total = self._total_chat_height()  # Total pixel height of all messages
        visible = self._visible_chat_height()  # How tall the visible chat area is
        # Scroll to the bottom: max(0, ...) prevents negative scroll
        self.scroll_offset = max(0, total - visible)

    def _visible_chat_height(self):
        # 40 for top bar and 80 for input bar
        return SCREEN_HEIGHT - 40 - 80

    def _total_chat_height(self):
        # Calculate the total height in pixels of all messages in the chat log so far
        # We need this to know when to enable scrolling and how far to scroll
        total = 0
        for _, text, _ in self.chat_log:
            # word wrap just makes long text fit in the screen width
            lines = word_wrap(text, self.font, SCREEN_WIDTH - 40)
            # Each line is 20px tall, plus 8px of padding between messages
            total += len(lines) * 20 + 8
        return total
    
    # ─── STAGE 4: THREADING ───────────────────────────────────────────────────

    def _start_character_generation(self):
        # Starts the AI character generation on a separate thread
        # If we called this directly, the game window would freeze cuz generation takes time
        # Threading lets us do work behind the scenes while the game keeps running
        # TODO Stage 4: move this to a background thread
        # Placeholder: hardcoded character so the UI has something to show
        self.character_info = {
            "NAME": "Alex",
            "JOB": "Barista",
            "PERSONALITY": "Friendly, witty, slightly sarcastic"
        }
        self.add_to_chat("system", "Alex the Barista appears!", SYSTEM_COLOR)
        self.add_to_chat("ai", "Alex: Hey there! Can I help you with something?", AI_COLOR)
        self.date_status = "ongoing"

    def _send_player_message(self, message):
        # Send the player's message to the AI in the background
        # Set waiting_for_ai to True to stop the user from more messages when the response is generating
        # TODO Stage 4: move this to a background thread
        # Placeholder: hardcoded response
        self.add_to_chat("ai", "Alex: That's interesting!", AI_COLOR)
        self.waiting_for_ai = False

    # ─── STAGE 5: EVENT HANDLING ──────────────────────────────────────────────

    def update(self, events):
        # Process all input events that happened since the last frame.
        # TODO Stage 5: add mouse wheel scroll and scene transition returns
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_RETURN and self.typed_text.strip():
                if self.date_status == "ongoing" and not self.waiting_for_ai:
                    message = self.typed_text.strip()
                    self.add_to_chat("user", f"You: {message}", USER_COLOR)
                    self.typed_text = ""
                    self._send_player_message(message)
            elif event.key == pygame.K_BACKSPACE:
                self.typed_text = self.typed_text[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.typed_text += event.unicode
        return None

    # ─── STAGE 2: DRAWING ─────────────────────────────────────────────────────

    def draw(self):
        # Draws the entire DateScene to the screen
        # This is called every frame, so everything is redrawn from scratch each tick
        self.screen.fill(DARK_BG)

        # TODO Stage 2: draw top bar to show character name

        # We draw the chat onto a separate off-screen Surface first, then stamp it onto the screen.
        # This is needed for scrolling: we can position the chat_surface up or down to show
        # different parts, which is simpler than clipping every individual message.        
        chat_top = 44  # offset from the top bar
        chat_height = self._visible_chat_height()
        # Create a new Surface the size of the visible chat area
        chat_surface = pygame.Surface((SCREEN_WIDTH, chat_height))
        chat_surface.fill(DARK_BG)

        # y starts at negative scroll_offset so scrolled-up content starts above the visible area
        y = -self.scroll_offset
        for _, text, color in self.chat_log:
            lines = word_wrap(
                text, self.font, SCREEN_WIDTH - 40
            )  # Split into displayable lines
            for line in lines:
                # Only bother rendering lines that are at least partially visible
                # This avoids drawing stuff outside of our visible range
                if -20 < y < chat_height + 20:
                    chat_surface.blit(self.font.render(line, True, color), (20, y))
                y += 20  # Move down one line height
            y += 8  # Extra padding between different messages

        # Draw the completed chat surface onto the main screen starting at chat_top
        self.screen.blit(chat_surface, (0, chat_top))
        # ──────────────────────────────────────────────────────────────────────

        # TODO Stage 2: draw accepted/rejected status banners

        # TODO Stage 2: draw text input box


# ─── Final Scene ────────────────────────────────────────────────

class FinishScene:
    def __init__(self, screen, total_seconds):
        self.screen = screen
        self.total_seconds = total_seconds
        self.font_big = pygame.font.SysFont("comic_sans", 42, bold=True)
        self.font_medium = pygame.font.SysFont("comic_sans", 24)
        self.font_small = pygame.font.SysFont("comic_sans", 18)

    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "restart"
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
        return None

    def draw(self):
        self.screen.fill(DARK_BG)
        title = self.font_big.render("YOU WIN!", True, (255, 200, 100))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))
        subtitle = self.font_medium.render("You got a date!", True, (255, 100, 150))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 170))
        minutes = int(self.total_seconds // 60)
        seconds = int(self.total_seconds % 60)
        time_surface = self.font_big.render(f"Time: {minutes:02d}:{seconds:02d}", True, WHITE)
        self.screen.blit(time_surface, (SCREEN_WIDTH // 2 - time_surface.get_width() // 2, 260))
        hint = self.font_small.render("[ ENTER to play again  |  ESC to quit ]", True, GRAY)
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 400))


# ─── GAME (STAGE 1 + STAGE 5) ────────────────────────────────────────────────

class Game:
    def __init__(self):
        # TODO Stage 1: initialise pygame, create window, clock, AI client, first scene
        pass

    def run(self):
        # TODO Stage 1: main game loop
        pass

    def handle_scene_change(self, result):
        # TODO Stage 5: swap scenes based on result string
        pass


if __name__ == "__main__":
    game = Game()
    game.run()
