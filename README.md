# English Conversation Practice App

A simple Streamlit application for practicing English conversation with AI using voice input and output.

## Features

- **Voice Input**: Record your voice with flexible duration options (3s, 5s, or 10s)
- **Speech Recognition**: Powered by OpenAI Whisper for accurate transcription
- **AI Conversation**: Natural conversation with GPT-4o-mini
- **Text-to-Speech**: AI responses are spoken aloud with a natural voice
- **Chat History**: View your entire conversation history

## Requirements

- Python 3.8+
- OpenAI API key
- Microphone

## Installation

1. Clone the repository
   ```bash
   git clone https://github.com/Motty-Win/english_conversation.git
   cd english_conversation
   ```

2. Create and activate virtual environment
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your OpenAI API key
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the Streamlit app:

```bash
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`.

### How to Use

1. Click one of the recording buttons:
   - **Record 3s**: For short responses
   - **Record 5s**: For normal conversation (recommended)
   - **Record 10s**: For longer responses

2. Speak clearly in English when recording starts

3. The AI will transcribe your speech, respond with text and voice

4. Continue the conversation naturally!

## Project Structure

```
english_conversation/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── .env                # OpenAI API key (create this)
├── audio/              # Audio files directory
│   ├── input/          # Temporary input recordings
│   └── output/         # Temporary output speech
└── images/             # UI images
```

## Technologies Used

- **Streamlit**: Web application framework
- **OpenAI Whisper**: Speech-to-text
- **OpenAI GPT-4o-mini**: Conversational AI
- **OpenAI TTS**: Text-to-speech
- **sounddevice**: Audio recording
- **scipy**: Audio file processing

## Notes

- Make sure your microphone is properly configured and accessible
- The app requires an active internet connection
- Audio files are automatically cleaned up after processing

## License

MIT License
