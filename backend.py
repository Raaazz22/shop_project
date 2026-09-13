"""
backend.py

All non-UI logic: API key handling, Gemini, Replicate clients,
and the functions that actually call those services.

Import from this file in app.py.
"""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

load_dotenv(override=True)


# ============================================================
# OPTIONAL DEPENDENCIES
# ============================================================

try:
    import replicate
except ImportError:
    replicate = None

try:
    from google import genai
except ImportError:
    genai = None


# ============================================================
# API KEYS
# ============================================================
def get_secret(key: str, default: str = "") -> str:

    value = os.environ.get(key)

    if value:
        return value

    try:
        value = st.secrets.get(key)

        if value:
            return value

    except Exception:
        pass

    return default

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
REPLICATE_API_KEY = get_secret("REPLICATE_API_TOKEN")


# ============================================================
# CLIENTS
# ============================================================

@st.cache_resource
def get_replicate_client():

    if not REPLICATE_API_KEY or replicate is None:
        return None

    return replicate.Client(
        api_token=REPLICATE_API_KEY,
        timeout=600
    )


@st.cache_resource
def get_gemini_client():

    if not GEMINI_API_KEY or genai is None:
        return None

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# FILE HELPERS
# ============================================================

def save_uploaded_file(uploaded_file) -> str:
    """Save a Streamlit UploadedFile to a temporary file."""

    try:

        suffix = Path(uploaded_file.name).suffix

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_file.write(
                uploaded_file.getbuffer()
            )

            return temp_file.name

    except Exception as e:

        raise RuntimeError(
            f"Unable to save uploaded file: {e}"
        )


# ============================================================
# IMAGE ENHANCEMENT
# Replicate — PrunaAI P-Image Edit
# ============================================================

def enhance_image(
    image_path: str,
    prompt: str,
    output_path: str = "enhanced.jpg"
) -> str:

    client = get_replicate_client()

    if client is None:
        raise RuntimeError(
            "REPLICATE_API_TOKEN is not configured."
        )

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    try:

        with open(image_path, "rb") as image_file:

            output = client.run(
                "prunaai/p-image-edit",
                input={
                    "images": [image_file],
                    "prompt": prompt,
                    "aspect_ratio": "match_input_image",
                    "turbo": True,
                },
            )

        if output is None:
            raise RuntimeError(
                "The image generation service returned no output."
            )

        with open(output_path, "wb") as output_file:
            output_file.write(output.read())

        return output_path

    except FileNotFoundError:
        raise

    except Exception as e:
        raise RuntimeError(
            f"Image enhancement failed: {e}"
        )

# ============================================================
# PASSPORT PHOTO
# Replicate — PrunaAI P-Image Edit
# ============================================================

def create_passport_photo(
    image_path: str,
    background_color: str,
    output_path: str = "passport_photo.jpg"
) -> str:

    client = get_replicate_client()

    if client is None:
        raise RuntimeError(
            "REPLICATE_API_TOKEN is not configured."
        )

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    prompt = f"""
Create a professional passport-style photograph from image 1.

Requirements:

1. Preserve the person's exact identity and facial features.
2. Do not change the person's face.
3. Keep the person's natural skin tone.
4. Keep the person photorealistic.
5. Make the person front-facing.
6. Center the face and upper shoulders.
7. Remove the original background completely.
8. Use a clean solid {background_color} background.
9. Remove all distracting objects from the background.
10. Use even, natural studio lighting.
11. Keep natural facial proportions.
12. Do not add another person.
13. Do not add text.
14. Do not add a logo.
15. Do not add a watermark.
16. Do not make the person look cartoon-like or AI-generated.
17. Create a clean professional Indian passport/document-style photograph.
"""

    try:

        # Pass the open file handle directly — same as enhance_image().
        # Do NOT pre-upload via client.files.create() and pass the
        # returned File object into `input`; replicate.run() JSON-encodes
        # the whole input dict, and a File object isn't JSON serializable.
        # Passing the file handle lets the replicate library handle the
        # upload internally and substitute the correct URL automatically.
        with open(image_path, "rb") as image_file:

            output = client.run(
                "prunaai/p-image-edit",
                input={
                    "images": [image_file],
                    "prompt": prompt,
                    "aspect_ratio": "match_input_image",
                    "turbo": True,
                },
            )

        if output is None:
            raise RuntimeError(
                "The passport photo service returned no output."
            )

        with open(
            output_path,
            "wb"
        ) as output_file:

            output_file.write(
                output.read()
            )

        return output_path

    except FileNotFoundError:
        raise

    except Exception as e:

        raise RuntimeError(
            f"Passport photo generation failed: {e}"
        )

# ============================================================
# IMAGE -> TEXT
# Gemini
# ============================================================

def image_data_extraction(
    image_path: str
) -> str:

    client = get_gemini_client()

    if client is None:

        if genai is None:

            raise RuntimeError(
                "google-genai is not installed. "
                "Run: pip install google-genai"
            )

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    if not os.path.exists(image_path):

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    try:

        uploaded_file = client.files.upload(
            file=image_path
        )

        prompt = """
Analyze the uploaded image carefully.

Your task is to extract text from the image.

Rules:

1. Extract ALL readable text.
2. Preserve the original wording accurately.
3. Preserve the original order of the content.
4. Preserve headings, paragraphs, lists and labels.
5. If there is a table, represent it in a readable table format.
6. If there are multiple sections, keep them separated.
7. Do not invent or guess missing text.
8. If text is unclear, mark it as [unclear].
9. If the image contains no readable text, say:
   "No readable text found in the image."
10. Return only the extracted text and useful structure.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                uploaded_file,
                prompt
            ]
        )

        if not response or not response.text:

            raise RuntimeError(
                "No text was extracted from the image."
            )

        return response.text

    except FileNotFoundError:
        raise

    except Exception as e:

        raise RuntimeError(
            f"Gemini image text extraction failed: {e}"
        )


# ============================================================
# CHAT SUPPORT
# Gemini
# ============================================================

def chat_with_ai(
    messages
) -> str:

    client = get_gemini_client()

    if client is None:

        if genai is None:

            raise RuntimeError(
                "google-genai is not installed. "
                "Run: pip install google-genai"
            )

        raise RuntimeError(
            "GEMINI_API_KEY is not configured."
        )

    try:

        # Gemini does not use the OpenAI-style
        # system/user message format directly.
        #
        # Convert messages into a Gemini-friendly
        # conversation format.

        system_instruction = ""

        conversation = []

        for message in messages:

            role = message.get(
                "role",
                "user"
            )

            content = message.get(
                "content",
                ""
            )

            if role == "system":

                system_instruction += (
                    content + "\n"
                )

            elif role == "user":

                conversation.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": content
                            }
                        ]
                    }
                )

            elif role == "assistant":

                conversation.append(
                    {
                        "role": "model",
                        "parts": [
                            {
                                "text": content
                            }
                        ]
                    }
                )

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=conversation,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.5,
                "max_output_tokens": 500,
            }
        )

        if not response or not response.text:

            raise RuntimeError(
                "No response received from Gemini."
            )

        return response.text

    except Exception as e:

        raise RuntimeError(
            f"Chat service failed: {e}"
        )