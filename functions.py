import streamlit as st
import os
import time
from pathlib import Path
import wave
import pyaudio
from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError
from audiorecorder import audiorecorder
import numpy as np
from scipy.io.wavfile import write
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
import constants as ct
import subprocess


def record_audio(audio_input_file_path):
    """
    音声入力を受け取って音声ファイルを作成
    """

    audio = audiorecorder(
        start_prompt="発話開始",
        pause_prompt="やり直す",
        stop_prompt="発話終了",
        start_style={"color": "white", "background-color": "black"},
        pause_style={"color": "gray", "background-color": "white"},
        stop_style={"color": "white", "background-color": "black"},
    )

    if len(audio) > 0:
        audio.export(audio_input_file_path, format="wav")
    else:
        st.stop()


def transcribe_audio(audio_input_file_path):
    """
    音声入力ファイルから文字起こしテキストを取得
    Args:
        audio_input_file_path: 音声入力ファイルのパス
    """
    with open(audio_input_file_path, "rb") as audio_input_file:
        transcript = st.session_state.openai_obj.audio.transcriptions.create(
            model="whisper-1", file=audio_input_file, language="en"
        )

    # 音声入力ファイルを削除
    os.remove(audio_input_file_path)

    return transcript


def save_to_wav(mp3_content: bytes, wav_file_path: str):
    """
    MP3 バイナリデータを WAV ファイルに変換して保存する。

    Args:
        mp3_content (bytes): MP3 バイナリデータ
        wav_file_path (str): 保存先の WAV ファイルパス
    """
    try:
        # MP3 バイナリデータを一時ファイルに保存
        temp_mp3_path = "temp_audio.mp3"
        with open(temp_mp3_path, "wb") as temp_mp3_file:
            temp_mp3_file.write(mp3_content)

        # ffmpeg を使用して MP3 を WAV に変換
        command = [
            "ffmpeg",
            "-y",  # 上書き許可
            "-i",
            temp_mp3_path,  # 入力ファイル
            wav_file_path,  # 出力ファイル
        ]
        result = subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # 一時ファイルを削除
        os.remove(temp_mp3_path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"ffmpeg による変換中にエラーが発生しました: {e.stderr.decode()}"
        )
    except Exception as e:
        raise RuntimeError(f"WAV ファイルの保存中にエラーが発生しました: {e}")


def play_wav(audio_output_file_path, speed=1.0):
    """
    音声ファイルの読み上げ
    Args:
        audio_output_file_path: 音声ファイルのパス
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
    """

    # 音声ファイルの読み込み
    audio = AudioSegment.from_wav(audio_output_file_path)

    # 速度を変更
    if speed != 1.0:
        # frame_rateを変更することで速度を調整
        modified_audio = audio._spawn(
            audio.raw_data, overrides={"frame_rate": int(audio.frame_rate * speed)}
        )
        # 元のframe_rateに戻すことで正常再生させる（ピッチを保持したまま速度だけ変更）
        modified_audio = modified_audio.set_frame_rate(audio.frame_rate)

        modified_audio.export(audio_output_file_path, format="wav")

    # PyAudioで再生
    with wave.open(audio_output_file_path, "rb") as play_target_file:
        p = pyaudio.PyAudio()
        stream = p.open(
            format=p.get_format_from_width(play_target_file.getsampwidth()),
            channels=play_target_file.getnchannels(),
            rate=play_target_file.getframerate(),
            output=True,
        )

        data = play_target_file.readframes(1024)
        while data:
            stream.write(data)
            data = play_target_file.readframes(1024)

        stream.stop_stream()
        stream.close()
        p.terminate()

    # LLMからの回答の音声ファイルを削除
    os.remove(audio_output_file_path)


def create_chain(system_template):
    """
    LLMによる回答生成用のChain作成
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_template),
            MessagesPlaceholder(variable_name="history"),
            HumanMessagePromptTemplate.from_template("{input}"),
        ]
    )
    chain = ConversationChain(
        llm=st.session_state.llm, memory=st.session_state.memory, prompt=prompt
    )

    return chain


def create_problem_and_play_audio():
    """
    問題生成と音声ファイルの再生
    Args:
        chain: 問題文生成用のChain
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
        openai_obj: OpenAIのオブジェクト
    """

    # 問題文を生成するChainを実行し、問題文を取得
    problem = st.session_state.chain_create_problem.predict(input="")

    # LLMからの回答を音声データに変換
    llm_response_audio = st.session_state.openai_obj.audio.speech.create(
        model="tts-1", voice="alloy", input=problem
    )

    # 音声ファイルの作成
    audio_output_file_path = (
        f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
    )
    save_to_wav(llm_response_audio.content, audio_output_file_path)

    # 音声ファイルの読み上げ
    play_wav(audio_output_file_path, st.session_state.speed)

    return problem, llm_response_audio


def create_evaluation():
    """
    ユーザー入力値の評価生成
    """

    llm_response_evaluation = st.session_state.chain_evaluation.predict(input="")

    return llm_response_evaluation


def translate_text(text: str) -> str:
    """
    Translate the given text into Japanese using OpenAI's GPT model.

    Args:
        text (str): The text to translate.

    Returns:
        str: The translated text in Japanese.
    """
    import streamlit as st

    try:
        response = st.session_state.openai_obj.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a translator. Translate the following text into Japanese.",
                },
                {"role": "user", "content": text},
            ],
        )
        translated_text = response.choices[0].message.content
        return translated_text.strip()
    except Exception as e:
        return f"翻訳中にエラーが発生しました: {e}"
