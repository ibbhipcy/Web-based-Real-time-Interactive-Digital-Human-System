# Multi-modal Interactive Digital Character System

## Project Overview
This project is a web-based, real-time interactive digital character system that bridges static AI image generation with dynamic human-computer interaction. It provides an end-to-end pipeline allowing users to generate personalized 3D avatars from text prompts and communicate with them via low-latency voice or text. Furthermore, the system integrates a semantic emotion feedback loop, enabling the digital character's facial expressions and body movements to evolve dynamically based on the context of the conversation.

## System Architecture & Core Modules

The architecture is decoupled into four primary functional modules, orchestrated by a Flask backend:

1.  **Generation Pipeline (`Draw/`, `Video/`):** 
    *   Utilizes Seedream for Text-to-Image generation based on user-defined attributes (hair, clothing, facial features).
    *   Utilizes Veo for Image-to-Video animation, bringing the static avatar to life.
2.  **Interaction Pipeline (`Listen/`, `Language/`, `Audio/`):**
    *   Utilizes OpenAI Whisper for Speech-to-Text (ASR).
    *   Utilizes GPT-4.1 for context-aware dialogue generation.
    *   Utilizes TTS models for voice synthesis.
3.  **Feedback Loop (Asynchronous Processing):**
    *   A background threading system that analyzes conversation semantics every 5 rounds to extract the current emotional tone.
    *   Dynamically prompts the video generation model to create new animations matching the emotion, which are then hot-swapped on the frontend.
4.  **Frontend Interface (`templates/`):**
    *   Built with vanilla JavaScript, utilizing the Fetch API and Stream API for real-time rendering of text and audio streams.

## Technical Highlights

### 1. Streaming Sentence Segmentation & Latency Optimization
Traditional LLM interactions require waiting for the entire text block to generate before initiating TTS, causing noticeable delays. This project implements Server-Sent Events (SSE) to stream the LLM response. By utilizing regular expressions (re.split) to monitor punctuation marks in the character stream, the system segments the text in real-time and triggers concurrent TTS API calls. This approach reduces the Time-to-First-Token (TTFT) to 1-2 seconds, achieving near real-time conversational fluidity.

### 2. Semantic Emotion & Action Feedback
To avoid static, repetitive animations, the system employs Python's threading module. Every 5 conversation rounds, a background thread summarizes the emotional context (e.g., happy, sad, angry) via the LLM. It then modifies the video generation prompt and invokes the Veo API asynchronously. The frontend polls for updates and seamlessly replaces the video source without blocking the main chat thread, ensuring an immersive and responsive experience.

### 3. Concurrency Control & Local Caching
*   **Caching:** To reduce redundant API costs and latency, an MD5 hash-based caching system (in-memory dictionary + JSON persistence) is implemented for TTS generation. Identical text inputs retrieve audio from the local cache instantly.
*   **Concurrency:** Multi-threaded HTTP requests initially caused connection conflicts (ResponseNotReady errors). The underlying HTTP client was refactored to instantiate connections within the function scope and close them immediately after use, ensuring complete thread safety during concurrent video generation tasks.

### 4. Multimedia Processing
*   **ASR:** User audio files are temporarily saved with timestamped filenames and deleted immediately after transcription to prevent disk bloating.
*   **FFmpeg Integration:** The system automatically utilizes FFmpeg to strip the original audio track from generated videos, ensuring a clean overlay of the synthesized TTS audio.

## Directory Structure

    ├── app.py                     # Flask backend server and API routing
    ├── requirements.txt           # Python dependencies
    ├── templates/
    │   └── index.html             # Frontend UI and stream handling
    ├── Draw/                      # Text-to-Image generation module
    │   └── h_seedream40_character_real.py
    ├── Video/                     # Image-to-Video generation module
    │   └── h_veo.py
    ├── Language/                  # LLM dialogue and streaming module
    │   └── h_streamTalk.py
    ├── Audio/                     # Text-to-Speech and caching module
    │   └── h_tts.py
    ├── Listen/                    # Speech-to-Text (ASR) module
    │   └── h_asr.py
    └── README.md

## Setup and Installation

### Prerequisites
*   Python 3.9+
*   FFmpeg (required for video audio processing)
*   API Keys for: GPT-4.1, Seedream, Veo, Whisper (OpenAI), and TTS.

### Installation
1. Clone the repository:
       git clone https://github.com/yourusername/interactive-digital-character.git
       cd interactive-digital-character
2. Install the required dependencies:
       pip install -r requirements.txt

### Configuration
During development, the external AI APIs were integrated via **Hongyun (宏云)**, an API service provider. 

Search for `API_KEY = "YOUR_API_KEY_HERE"` in the following files and replace them with your actual credentials (and update the base URL if you are using a different provider):
*   `Language/h_streamTalk.py`
*   `Audio/h_tts.py`
*   `Draw/h_seedream40_character_real.py`
*   `Video/h_veo.py`
*   `Listen/h_asr.py` (Requires an OpenAI API Key)

### Execution
Run the Flask application:
    python app.py
Access the interface by navigating to `http://localhost:5000` in your web browser.

## Demonstration
A video demonstration of the complete workflow and interactive features can be viewed at: 
[Insert YouTube or Bilibili Video Link Here]

## Author
[Zheng Kaixin]
*This project was developed independently as a personal portfolio piece.*

> **Important Note**
> 
> While the core architecture and code logic of this project are fully functional, some external AI API services integrated in this demo may no longer be active or have changed their access policies.
> 
> If you encounter errors related to API requests (such as 404 or Auth errors), please be aware that this is likely due to expired third-party endpoints rather than the core logic of the project. The codebase is provided as a technical demonstration of multimodal integration, SSE streaming, and asynchronous processing.
