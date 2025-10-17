"""
英会話アプリケーション用のユーティリティ関数群

このモジュールは音声処理、LLM連携、翻訳などの機能を提供します。
"""

import os
import subprocess
import time
import wave
from typing import Tuple

import pyaudio
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from langchain.chains import ConversationChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from openai import BadRequestError
from openai.types.audio import Transcription
from pydub import AudioSegment

import constants as ct


def record_audio(audio_input_file_path: str) -> None:
    """
    音声入力を受け取って音声ファイルを作成する

    Args:
        audio_input_file_path: 保存先の音声ファイルパス

    Note:
        音声が録音されなかった場合、Streamlitの実行を停止します。
    """
    audio = audio_recorder(
        text="発話開始",
        icon_size="2x",
        recording_color="#e8b62c",
        neutral_color="#6c757d",
        pause_threshold=3.0,  # 3秒の無音で録音終了
        sample_rate=16000,
    )

    if audio is not None and len(audio) > 0:
        with open(audio_input_file_path, "wb") as f:
            f.write(audio)
    else:
        st.stop()


def transcribe_audio(audio_input_file_path: str) -> Transcription:
    """
    音声ファイルから文字起こしテキストを取得する

    Args:
        audio_input_file_path: 音声入力ファイルのパス

    Returns:
        OpenAI Whisperの文字起こし結果オブジェクト

    Note:
        処理完了後、音声入力ファイルは自動的に削除されます。
    """
    try:
        # 音声ファイルの存在と内容を確認
        if not os.path.exists(audio_input_file_path):
            st.error("音声ファイルが見つかりません。")
            st.stop()

        file_size = os.path.getsize(audio_input_file_path)
        if file_size == 0:
            os.remove(audio_input_file_path)
            st.error("音声ファイルが空です。録音ボタンを押して音声を録音してください。")
            st.stop()

        # 音声ファイルの長さを確認
        audio = AudioSegment.from_file(audio_input_file_path)
        duration_seconds = len(audio) / 1000.0  # ミリ秒から秒に変換

        # 音声が短すぎる場合はエラーを表示
        if duration_seconds < 0.1:
            os.remove(audio_input_file_path)
            st.error(f"録音時間が短すぎます（{duration_seconds:.2f}秒）。最低0.1秒以上の音声を録音してください。")
            st.info("「発話開始」ボタンを押して、音声を録音してから停止ボタンを押してください。")
            st.stop()

        with open(audio_input_file_path, "rb") as audio_input_file:
            transcript = st.session_state.openai_obj.audio.transcriptions.create(
                model="whisper-1", file=audio_input_file, language="en"
            )

        # 音声入力ファイルを削除
        os.remove(audio_input_file_path)

        return transcript

    except BadRequestError as e:
        # 音声入力ファイルを削除
        if os.path.exists(audio_input_file_path):
            os.remove(audio_input_file_path)

        if "audio_too_short" in str(e):
            st.error("録音時間が短すぎます。最低0.1秒以上の音声を録音してください。")
            st.info("「発話開始」ボタンを押して、音声を録音してから停止ボタンを押してください。")
        else:
            st.error(f"音声認識中にエラーが発生しました: {e}")
        st.stop()
    except Exception as e:
        # その他のエラー処理
        if os.path.exists(audio_input_file_path):
            os.remove(audio_input_file_path)
        st.error(f"音声処理中にエラーが発生しました: {e}")
        st.stop()


def save_to_wav(audio_content: bytes, wav_file_path: str) -> None:
    """
    音声バイナリデータをWAVファイルに変換して保存する

    Args:
        audio_content: 音声バイナリデータ（MP3など）
        wav_file_path: 保存先のWAVファイルパス

    Raises:
        RuntimeError: ffmpegによる変換が失敗した場合

    Note:
        ffmpegがシステムにインストールされている必要があります。
    """
    temp_mp3_path = "temp_audio.mp3"

    try:
        # 音声バイナリデータを一時ファイルに保存
        with open(temp_mp3_path, "wb") as temp_mp3_file:
            temp_mp3_file.write(audio_content)

        # ffmpegを使用してWAVに変換
        command = [
            "ffmpeg",
            "-y",  # 上書き許可
            "-i",
            temp_mp3_path,  # 入力ファイル
            wav_file_path,  # 出力ファイル
        ]
        subprocess.run(
            command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # 一時ファイルを削除
        os.remove(temp_mp3_path)

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"ffmpegによる変換中にエラーが発生しました: {e.stderr.decode()}"
        )
    except Exception as e:
        raise RuntimeError(f"WAVファイルの保存中にエラーが発生しました: {e}")


def play_wav(audio_output_file_path: str, speed: float = 1.0) -> None:
    """
    WAV音声ファイルを再生する

    Args:
        audio_output_file_path: 音声ファイルのパス
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速）

    Note:
        再生完了後、音声ファイルは自動的に削除されます。
        速度変更時もピッチは保持されます。
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

        # 音声データをストリーミング再生
        data = play_target_file.readframes(1024)
        while data:
            stream.write(data)
            data = play_target_file.readframes(1024)

        stream.stop_stream()
        stream.close()
        p.terminate()

    # 音声ファイルを削除
    os.remove(audio_output_file_path)


def create_chain(system_template: str) -> ConversationChain:
    """
    LLMによる回答生成用のConversationChainを作成する

    Args:
        system_template: システムプロンプトテンプレート

    Returns:
        設定済みのConversationChain

    Note:
        st.session_state.llm と st.session_state.memory を使用します。
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


def create_problem_and_play_audio() -> Tuple[str, bytes]:
    """
    問題文を生成し、音声で読み上げる

    Returns:
        Tuple[str, Any]: (問題文, 音声レスポンスオブジェクト)

    Note:
        - st.session_state.chain_create_problemを使用して問題文を生成
        - st.session_state.speedで再生速度を調整
        - 音声は女性の声(nova)で生成されます
    """
    # 問題文を生成
    problem = st.session_state.chain_create_problem.predict(input="")

    # LLMからの回答を音声データに変換（女性の声に固定）
    llm_response_audio = st.session_state.openai_obj.audio.speech.create(
        model="tts-1", voice="nova", input=problem
    )

    # 音声ファイルの作成と再生
    audio_output_file_path = (
        f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
    )
    save_to_wav(llm_response_audio.content, audio_output_file_path)
    play_wav(audio_output_file_path, st.session_state.speed)

    return problem, llm_response_audio


def create_evaluation() -> str:
    """
    ユーザー入力値の評価を生成する

    Returns:
        評価結果のテキスト

    Note:
        st.session_state.chain_evaluationを使用します。
    """
    llm_response_evaluation = st.session_state.chain_evaluation.predict(input="")
    return llm_response_evaluation


def translate_text(text: str) -> str:
    """
    指定されたテキストを日本語に翻訳する

    Args:
        text: 翻訳対象のテキスト

    Returns:
        日本語に翻訳されたテキスト

    Note:
        OpenAI GPT-4o-miniモデルを使用して翻訳を行います。
    """
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
