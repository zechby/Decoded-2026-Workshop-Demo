def word_wrap(text, font, max_width):
    """Break text into lines that fit within max_width pixels."""
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)
    return lines


def extract_status_from_response(text):
    """
    AI responses end with a hidden tag like [STATUS:accepted].
    Strips the tag and returns (cleaned_text, status_string).
    """
    for status in ["accepted", "rejected", "ongoing"]:
        tag = f"[STATUS:{status}]"
        if tag in text:
            return text.replace(tag, "").strip(), status
    return text.strip(), "ongoing"


def parse_character_info(text):
    """Parse the structured character info from the AI's generation response."""
    info = {}
    for line in text.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            info[key.strip().upper()] = value.strip()
    return info
