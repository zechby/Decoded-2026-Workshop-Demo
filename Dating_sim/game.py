import pygame
import sys
import os
import time
import threading
from groq import Groq
from Dating_sim.helpers import word_wrap, extract_status_from_response, parse_character_info
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROK_API_KEY")


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GROQ_MODEL = "llama-3.3-70b-versatile"

# UI Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BG = (20, 24, 30)
GRAY = (140, 140, 140)
INPUT_BG = (50, 56, 66)
USER_COLOR = (80, 160, 255)
AI_COLOR = (220, 180, 100)
SYSTEM_COLOR = (160, 160, 160)
RED_ACCENT = (255, 100, 100)
TOP_BAR_BG = (40, 44, 52)

# prompts
CHARACTER_GENERATION_PROMPT = """You are a character generator for a dating sim game. Generate a unique character with:
- A first name
- A job (Teacher, Cybersecurity analyst, Foley artist, Plumber, Marine biologist, Tattoo artist, Park ranger, Ethical hacker, LEGO master builder, Snake milker,etc.)
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


# GROQ CONNECTION


class AIClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Missing api key")
            sys.exit(1)
        self.client = Groq(api_key=api_key)

    def send_messages(self, messages):
        """Send a list of chat messages to Groq and return the AI's response text."""
        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                max_tokens=300,
                temperature=0.9,
            )
            return response.choices[0].message.content
        except Exception as error:
            return f"[AI Error: {error}] [STATUS:ongoing]"  # Default status to ongoing

    def generate_character(self):
        """Ask the AI to generate a fresh character. Returns (info_dict, raw_text)."""
        raw_text = self.send_messages(
            [
                {
                    "role": "system",
                    "content": "You are a creative character generator.",
                },
                {"role": "user", "content": CHARACTER_GENERATION_PROMPT},
            ]
        )
        return parse_character_info(raw_text), raw_text


# DATE SCENE


class DateScene:
    def __init__(self, screen, ai_client):
        self.screen = screen
        self.ai = ai_client

        # Fonts
        self.font = pygame.font.SysFont("comic_sans", 16)
        self.font_title = pygame.font.SysFont("comic_sans", 22, bold=True)
        self.font_small = pygame.font.SysFont("comic_sans", 14)

        # Chat state
        self.chat_log = []  # What's shown on screen: [(sender, text, color)]
        self.conversation_history = []  # What's sent to the AI API
        self.typed_text = ""
        self.scroll_offset = 0
        self.date_status = (
            "loading"  # 4 States "loading" → "ongoing" → "accepted" or "rejected"
        )
        self.waiting_for_ai = False

        # Character info (filled once AI generates it)
        self.character_info = {}

        # Start generating a character in the background
        self.add_to_chat("system", "Finding someone for you to meet...", SYSTEM_COLOR)
        self._start_character_generation()

    def add_to_chat(self, sender, text, color):
        """Add a message to the chat log and scroll to the bottom."""
        self.chat_log.append((sender, text, color))
        total = self._total_chat_height()
        visible = self._visible_chat_height()
        self.scroll_offset = max(0, total - visible)

    def _visible_chat_height(self):
        return SCREEN_HEIGHT - 120

    def _total_chat_height(self):
        total = 0
        for _, text, _ in self.chat_log:
            lines = word_wrap(text, self.font, SCREEN_WIDTH - 40)
            total += len(lines) * 20 + 8
        return total

    # AI call in background

    def _start_character_generation(self):
        """Generate a character on a background thread so the game doesn't freeze."""

        def do_generation():
            info, raw = self.ai.generate_character()
            self.character_info = info

            name = info.get("NAME", "???")
            job = info.get("job", "unknown")
            personality = info.get("PERSONALITY", "mysterious")

            self.add_to_chat("system", f"{name} the {job} appears!", SYSTEM_COLOR)
            self.add_to_chat("system", f"Personality: {personality}", SYSTEM_COLOR)

            # Set up conversation
            system_prompt = DATE_SYSTEM_PROMPT_TEMPLATE.format(
                character_description=raw
            )
            self.conversation_history = [{"role": "system", "content": system_prompt}]

            # Get opening greeting
            greeting_request = self.conversation_history + [
                {
                    "role": "user",
                    "content": "(The player just approached you. Greet them in character.)",
                }
            ]
            ai_response = self.ai.send_messages(greeting_request)
            clean_text, status = extract_status_from_response(ai_response)

            self.conversation_history.append(
                {"role": "assistant", "content": ai_response}
            )
            self.add_to_chat("ai", f"{name}: {clean_text}", AI_COLOR)
            self.date_status = status

        thread = threading.Thread(target=do_generation, daemon=True)
        thread.start()

    def _send_player_message(self, message):
        """Send the player's typed message to the AI on a background thread."""
        self.waiting_for_ai = True
        character_name = self.character_info.get("NAME", "???")

        def do_send():
            self.conversation_history.append({"role": "user", "content": message})
            ai_response = self.ai.send_messages(self.conversation_history)
            self.conversation_history.append(
                {"role": "assistant", "content": ai_response}
            )

            clean_text, status = extract_status_from_response(ai_response)
            self.add_to_chat("ai", f"{character_name}: {clean_text}", AI_COLOR)
            self.date_status = status
            self.waiting_for_ai = False

        thread = threading.Thread(target=do_send, daemon=True)
        thread.start()

    def update(self, events):
        for event in events:
            # Mouse wheel scrolling
            if event.type == pygame.MOUSEWHEEL:
                self.scroll_offset -= event.y * 30
                self.scroll_offset = max(0, self.scroll_offset)
                max_scroll = max(
                    0, self._total_chat_height() - self._visible_chat_height()
                )
                self.scroll_offset = min(max_scroll, self.scroll_offset)
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.key == pygame.K_RETURN and self.typed_text.strip():
                if self.date_status == "accepted":
                    return "win"
                elif self.date_status == "rejected":
                    return "retry"
                elif self.date_status == "ongoing" and not self.waiting_for_ai:
                    message = self.typed_text.strip()
                    self.add_to_chat("user", f"You: {message}", USER_COLOR)
                    self.typed_text = ""
                    self._send_player_message(message)

            elif event.key == pygame.K_BACKSPACE:
                self.typed_text = self.typed_text[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.typed_text += event.unicode

        return None

    def draw(self):
        self.screen.fill(DARK_BG)

        # Top bar with character name
        name = self.character_info.get("NAME", "Loading...")
        job = self.character_info.get("JOB", "")
        title_text = f"{name} the {job}" if job else name

        pygame.draw.rect(self.screen, TOP_BAR_BG, (0, 0, SCREEN_WIDTH, 40))
        self.screen.blit(self.font_title.render(title_text, True, AI_COLOR), (10, 8))
        self.screen.blit(
            self.font_small.render("[ESC] quit", True, GRAY), (SCREEN_WIDTH - 90, 12)
        )

        # Chat messages
        chat_top = 44  # Offset from the top banner
        chat_height = self._visible_chat_height()
        chat_surface = pygame.Surface((SCREEN_WIDTH, chat_height))
        chat_surface.fill(DARK_BG)

        y = -self.scroll_offset
        for _, text, color in self.chat_log:
            lines = word_wrap(text, self.font, SCREEN_WIDTH - 40)
            for line in lines:
                if -20 < y < chat_height + 20:
                    chat_surface.blit(self.font.render(line, True, color), (20, y))
                y += 20
            y += 8

        self.screen.blit(chat_surface, (0, chat_top))

        # Status banners
        if self.date_status == "accepted":
            banner = self.font_title.render(
                "They agreed to date you!", True, (255, 100, 150)
            )
            self.screen.blit(
                banner,
                (SCREEN_WIDTH // 2 - banner.get_width() // 2, SCREEN_HEIGHT - 78),
            )
            hint = self.font_small.render("[ENTER] to continue", True, WHITE)
            self.screen.blit(
                hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 55)
            )

        elif self.date_status == "rejected":
            banner = self.font_title.render("They rejected you!", True, RED_ACCENT)
            self.screen.blit(
                banner,
                (SCREEN_WIDTH // 2 - banner.get_width() // 2, SCREEN_HEIGHT - 78),
            )
            hint = self.font_small.render("[ENTER] to try someone new", True, WHITE)
            self.screen.blit(
                hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 55)
            )

        # Text input box
        input_y = SCREEN_HEIGHT - 40
        pygame.draw.rect(self.screen, INPUT_BG, (0, input_y, SCREEN_WIDTH, 40))
        pygame.draw.line(self.screen, GRAY, (0, input_y), (SCREEN_WIDTH, input_y))
        self.screen.blit(
            self.font.render(f"> {self.typed_text}", True, WHITE), (10, input_y + 10)
        )


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
        time_surface = self.font_big.render(
            f"Time: {minutes:02d}:{seconds:02d}", True, WHITE
        )
        self.screen.blit(
            time_surface, (SCREEN_WIDTH // 2 - time_surface.get_width() // 2, 260)
        )

        hint = self.font_small.render(
            "[ ENTER to play again  |  ESC to quit ]", True, GRAY
        )
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 400))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Dating Sim")
        self.clock = pygame.time.Clock()
        self.ai_client = AIClient()

        self.current_scene = DateScene(self.screen, self.ai_client)
        self.timer_start = time.time()

    def run(self):
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            result = self.current_scene.update(events)
            if result is not None:
                self.handle_scene_change(result)

            self.current_scene.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

    def handle_scene_change(self, result):
        if result == "win":
            elapsed = time.time() - self.timer_start
            self.current_scene = FinishScene(self.screen, elapsed)

        elif result == "retry":
            # Got rejected — generate a new character and try again
            self.current_scene = DateScene(self.screen, self.ai_client)

        elif result == "restart":
            self.current_scene = DateScene(self.screen, self.ai_client)
            self.timer_start = time.time()


if __name__ == "__main__":
    game = Game()
    game.run()
