"""
English Conversation Practice App

A simple Streamlit application for practicing English conversation with AI.
Features:
- Voice input with multiple duration options (3s, 5s, 10s)
- AI-powered speech recognition using OpenAI Whisper
- Natural conversation with GPT-4o-mini
- Text-to-speech responses
"""

import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import sounddevice as sd
import scipy.io.wavfile as wav
import numpy as np

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(page_title="English Conversation Practice")

# Create directories
Path("audio/input").mkdir(parents=True, exist_ok=True)
Path("audio/output").mkdir(parents=True, exist_ok=True)

# Check API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("OPENAI_API_KEY not found in environment variables.")
    st.stop()

# Initialize OpenAI client
if "client" not in st.session_state:
    st.session_state.client = OpenAI()

# Initialize messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize recording state
if "recording_duration" not in st.session_state:
    st.session_state.recording_duration = 0

# UI
st.title("🗣️ 英会話練習アプリ")
st.markdown("AIと英会話の練習をしましょう！")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Recording interface
st.markdown("---")
st.markdown("### 🎤 音声入力")
st.info("録音時間を選んでください: 3秒（短い）、5秒（普通）、10秒（長い）")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🎙️ 3秒録音", use_container_width=True, type="secondary"):
        st.session_state.recording_duration = 3
        st.rerun()

with col2:
    if st.button("🎙️ 5秒録音", use_container_width=True, type="primary"):
        st.session_state.recording_duration = 5
        st.rerun()

with col3:
    if st.button("🎙️ 10秒録音", use_container_width=True, type="secondary"):
        st.session_state.recording_duration = 10
        st.rerun()

# ===== RECORDING PROCESSING =====
if st.session_state.recording_duration > 0:
    duration = st.session_state.recording_duration
    st.session_state.recording_duration = 0
    audio_file_path = f"audio/input/recording_{int(time.time())}.wav"

    try:
        # Step 1: Record audio from microphone
        with st.spinner(f"🔴 {duration}秒間録音中... 話してください！"):
            sample_rate = 16000  # 16kHz is optimal for Whisper
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,  # Mono
                dtype='int16'
            )
            sd.wait()  # Wait until recording is finished

        # Step 2: Save audio to file
        wav.write(audio_file_path, sample_rate, recording)
        st.success("✅ 録音完了！")

        # Step 3: Validate audio signal
        max_amplitude = np.max(np.abs(recording))
        if max_amplitude < 100:
            st.error("⚠️ 音声が検出されませんでした。マイクの設定を確認してください。")
            os.remove(audio_file_path)
            st.stop()

        # Step 4: Transcribe audio to text using Whisper
        with st.spinner("🔄 音声を認識中..."):
            with open(audio_file_path, "rb") as f:
                transcript = st.session_state.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                )
            user_text = transcript.text.strip()
            os.remove(audio_file_path)

            if not user_text or len(user_text) < 2:
                st.error("音声を認識できませんでした。もう一度はっきりと話してください。")
                st.stop()

        # Step 5: Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_text})

        # Step 6: Generate AI response
        with st.spinner("💭 AI が考え中..."):
            # Build conversation history for API
            api_messages = [
                {"role": "system", "content": "You are a friendly English conversation partner. Keep responses to 2-3 sentences."}
            ]
            for msg in st.session_state.messages:
                api_messages.append({"role": msg["role"], "content": msg["content"]})

            response = st.session_state.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=api_messages,  # type: ignore
                temperature=0.7,
            )
            ai_text = response.choices[0].message.content or "申し訳ございません、応答できませんでした。"

        # Step 7: Add AI message to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_text})

        # Step 8: Generate speech from AI text
        with st.spinner("🔊 音声を生成中..."):
            speech = st.session_state.client.audio.speech.create(
                model="tts-1",
                voice="nova",  # Female voice
                input=ai_text,
            )

            output_file = f"audio/output/output_{int(time.time())}.mp3"
            with open(output_file, "wb") as f:
                f.write(speech.content)

        # Step 9: Save audio to session state for playback after rerun
        with open(output_file, "rb") as audio_file:
            st.session_state.current_audio = audio_file.read()

        # Clean up temporary file
        if os.path.exists(output_file):
            os.remove(output_file)

        st.rerun()

    except Exception as e:
        st.error(f"エラー: {e}")
        if os.path.exists(audio_file_path):
            os.remove(audio_file_path)

# ===== AUDIO PLAYBACK =====
# Play AI response audio after page rerun (ensures full playback without interruption)
if "current_audio" in st.session_state and st.session_state.current_audio is not None:
    st.markdown("---")
    st.markdown("### 🔊 AIの音声応答")
    st.audio(st.session_state.current_audio, format="audio/mp3", autoplay=True)
    st.session_state.current_audio = None  # Clear after playing
