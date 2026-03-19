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
        # Get the API key from environment variables (loaded from .env earlier)
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Missing api key")
            sys.exit(1)  # Close the game if no api key found
        # Create the Groq client object, we later use
        self.client = Groq(api_key=api_key)

    def send_messages(self, messages):
        # TODO Stage 3: send messages to Groq and return response text
        # Send a list of chat messages to Groq and return the AI's response as a string.
        # 'messages' is a list of dicts in this format: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
        # This is the standard format used by OpenAI-compatible APIs.
        try:
            response = self.client.chat.completions.create(
                model=GROQ_MODEL,  # Choose your model
                messages=messages,  # The full conversation history
                max_tokens=300,  # Limit response length so it stays concise
                temperature=0.9,  # Higher temperature gives more creative and randomness, lower the opposite
            )
            return response.choices[0].message.content
        except Exception as error:
            # If the API call fails for any reason, return a fallback message
            # We append [STATUS:ongoing] so the game doesn't break from a missing status tag
            return f"[AI Error: {error}] [STATUS:ongoing]"

    def generate_character(self):
        # TODO Stage 3: ask AI to generate a character
        # Ask the AI to generate a new character using the character generation prompt.
        # Returns a tuple: (parsed_dict, raw_text)
        # raw_text is the full AI response; parsed_dict is the dictionary with the character attributes
        raw_text = self.send_messages(
            [
                {
                    "role": "system",  # System messages set the AI's overall behavior
                    "content": "You are a creative character generator.",
                },
                {
                    "role": "user",
                    "content": CHARACTER_GENERATION_PROMPT,
                },  # The actual generation request
            ]
        )
        # parse_character_info extracts the attributes into a dictionary
        return parse_character_info(raw_text), raw_text

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
        def do_generation():
            # This function runs on the background thread
            info, raw = (
                self.ai.generate_character()
            )  # call the generation function we made
            self.character_info = info  # Store the parsed character data

            # Extract the fields we want to display
            name = info.get("NAME", "???")  # .get() with a default prevents errors
            job = info.get("job", "unknown")
            personality = info.get("PERSONALITY", "mysterious")

            # Announce the new character in the chat
            self.add_to_chat("system", f"{name} the {job} appears!", SYSTEM_COLOR)
            self.add_to_chat("system", f"Personality: {personality}", SYSTEM_COLOR)

            # Recall {character_description} in the system prompt, this is where we use the raw info to tell the ai how to act
            system_prompt = DATE_SYSTEM_PROMPT_TEMPLATE.format(
                character_description=raw
            )
            # Initialize the conversation history with just the system prompt
            self.conversation_history = [{"role": "system", "content": system_prompt}]

            # Ask the AI to generate an opening greeting, however the user prompt is NOT added to the context
            greeting_request = self.conversation_history + [
                {
                    "role": "user",
                    "content": "(The player just approached you. Greet them in character.)",
                }
            ]
            ai_response = self.ai.send_messages(greeting_request)
            # extract_status_from_response() gets the status from the response
            # it returns the clean display text and the status separately
            clean_text, status = extract_status_from_response(ai_response)

            # Save the greeting to the conversation history
            self.conversation_history.append(
                {"role": "assistant", "content": ai_response}
            )
            # Show the greeting in the chat
            self.add_to_chat("ai", f"{name}: {clean_text}", AI_COLOR)
            # Update the date status, it should be ONGOING from here
            self.date_status = status

        # daemon=True means this thread will be killed if main program is killed
        thread = threading.Thread(target=do_generation, daemon=True)
        thread.start()  # Start doing this in da background

    def _send_player_message(self, message):
        # Send the player's message to the AI in the background
        # Set waiting_for_ai to True to stop the user from more messages when the response is generating
        # TODO Stage 4: move this to a background thread
        self.waiting_for_ai = True
        character_name = self.character_info.get("NAME", "???")  # Get da character name

        def do_send():
            # Add the player's message to the conversation history in API format
            self.conversation_history.append({"role": "user", "content": message})
            # Send the full conversation history so the AI has all context
            ai_response = self.ai.send_messages(self.conversation_history)
            # Save the AI's response to history so future messages retain context
            self.conversation_history.append(
                {"role": "assistant", "content": ai_response}
            )

            # Strip the status tag for display, but keep the status value
            clean_text, status = extract_status_from_response(ai_response)
            self.add_to_chat("ai", f"{character_name}: {clean_text}", AI_COLOR)
            # Update game state based on what the AI decided (ongoing/accepted/rejected)
            self.date_status = status
            # Unblock the input box — player can type again
            self.waiting_for_ai = False

        # Same as above
        thread = threading.Thread(target=do_send, daemon=True)
        thread.start()


    # ─── STAGE 5: EVENT HANDLING ──────────────────────────────────────────────

    def update(self, events):
        # Process all input events that happened since the last frame.
        # TODO Stage 5: add mouse wheel scroll and scene transition returns
        # Returns 1 of 3 strings: "win" or "retry" or "none" to see if the scene needs changing
        for event in events:
            # Check if the user scrolled
            if event.type == pygame.MOUSEWHEEL:
                # event.y is +1 for scroll up, -1 for scroll down
                # We invert it (subtract) so scrolling up moves the view up (less offset)
                self.scroll_offset -= event.y * 30
                # Clamp: scroll_offset can't go below 0 (can't scroll above the top)
                self.scroll_offset = max(0, self.scroll_offset)
                # Clamp: can't scroll below the bottom of all content
                max_scroll = max(
                    0, self._total_chat_height() - self._visible_chat_height()
                )
                self.scroll_offset = min(max_scroll, self.scroll_offset)
                continue  # Skip to the next event — no key handling needed here

            # We only care about key presses from here
            if event.type != pygame.KEYDOWN:
                continue

            # escape just quits the game
            if event.key == pygame.K_ESCAPE:
                pygame.quit()  # Shut down pygame first
                sys.exit()  # Then kill python

            if event.key == pygame.K_RETURN and self.typed_text.strip():
                # .strip() removes whitespace to prevent blank messages
                if self.date_status == "accepted":
                    # Go to da final screen
                    return "win"
                elif self.date_status == "rejected":
                    # You failed gng, start a new datescene
                    return "retry"
                elif self.date_status == "ongoing" and not self.waiting_for_ai:
                    # Send your message cuz its still going
                    message = self.typed_text.strip()
                    self.add_to_chat("user", f"You: {message}", USER_COLOR)
                    self.typed_text = ""  # Reset the input box
                    self._send_player_message(message)  # Use the function above

            elif event.key == pygame.K_BACKSPACE:
                # Remove the last character from the input box
                self.typed_text = self.typed_text[:-1]  # String splicing
            elif event.unicode and event.unicode.isprintable():
                # filter out non unicode characters
                self.typed_text += event.unicode

        return None

    # ─── STAGE 2: DRAWING ─────────────────────────────────────────────────────

    def draw(self):
        # Draws the entire DateScene to the screen
        # This is called every frame, so everything is redrawn from scratch each tick
        self.screen.fill(DARK_BG)
        # TODO Stage 2: draw top bar to show character name
        name = self.character_info.get("NAME", "Loading...")
        job = self.character_info.get("JOB", "")
        title_text = f"{name} the {job}" if job else name

        # Big rectangle on da top as top bar
        pygame.draw.rect(self.screen, TOP_BAR_BG, (0, 0, SCREEN_WIDTH, 40))
        # font.render(text, antialias, color) returns the unicode text as a rendered surface
        # blit() basically draws onto the current surface
        self.screen.blit(self.font_title.render(title_text, True, AI_COLOR), (10, 8))
        self.screen.blit(
            self.font_small.render("[ESC] quit", True, GRAY), (SCREEN_WIDTH - 90, 12)
        )
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
        # Render accepted or rejected banners at the end
        # Overlay on top of the chat area when the date ends
        if self.date_status == "accepted":
            # Center the banner horizontally using its pixel width
            # Logic is pretty self explanatory
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

        # The input box is fixed at the bottom of the screen
        input_y = SCREEN_HEIGHT - 40
        # Draw the input box background
        pygame.draw.rect(self.screen, INPUT_BG, (0, input_y, SCREEN_WIDTH, 40))
        # Draw a horizontal line along the top of the input box to separate it from the rest
        pygame.draw.line(self.screen, GRAY, (0, input_y), (SCREEN_WIDTH, input_y))
        # Little ">" to show where you are typing right now
        self.screen.blit(
            self.font.render(f"> {self.typed_text}", True, WHITE), (10, input_y + 10)
        )
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
        pygame.init()  # Initialize pygame
        # Create the game window
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI Dating Sim")  # Set the window title
        # Clock is used to enforce the FPS cap so the game doesn't run at an insane fps
        self.clock = pygame.time.Clock()
        # initialize the ai client
        self.ai_client = AIClient()
        # Start the date scene
        self.current_scene = DateScene(self.screen, self.ai_client)
        # Record when the game started
        self.timer_start = time.time()

    def run(self):
        # Da main game loop, runs forever, iterates once per frame
        while True:
            # Get all the events that happened every frame
            events = pygame.event.get()

            # Quit the game when the x is pressed
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            # Call the current scene's update function based off the events we got
            result = self.current_scene.update(events)
            if result is not None:
                self.handle_scene_change(
                    result
                )  # Switch to a different scene if we got a flag

            # Call the draw function of the scene each frame
            self.current_scene.draw()
            # .flip() sends the stuff we drew to the actual game window
            pygame.display.flip()

            # Wait until we've used up the time for one frame at our target FPS
            # Without this, the loop would waste a bunch of iterations since we only need 60 fps
            self.clock.tick(FPS)

    def handle_scene_change(self, result):
        # TODO Stage 5: swap scenes based on result string
        # Switch the active scene based on the return of update()
        if result == "win":
            # Player won: show the finish screen with the time spent
            elapsed = time.time() - self.timer_start
            self.current_scene = FinishScene(self.screen, elapsed)

        elif result == "retry":
            # Got rejected: swap in a fresh DateScene with a new AI character
            self.current_scene = DateScene(self.screen, self.ai_client)

        elif result == "restart":
            # Start new game
            self.current_scene = DateScene(self.screen, self.ai_client)
            self.timer_start = time.time()  # Reset the timer for the new run



if __name__ == "__main__":
    game = Game()
    game.run()  # Start the game loop — this never returns until the player quits
