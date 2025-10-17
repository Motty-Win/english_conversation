"""
生成AI英会話アプリケーション - メインモジュール

音声対話による英会話学習アプリのエントリーポイント
"""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from openai import OpenAI

import constants as ct
import functions as ft
from config import initialize_session_state
from mode_handlers import (
    handle_basic_conversation_mode,
    handle_dictation_mode,
    handle_shadowing_mode,
)
from ui_components import (
    display_chat_input,
    display_control_panel,
    display_header,
    display_message_history,
    display_mode_buttons,
    display_welcome_message,
)

# ===== 初期設定 =====

load_dotenv()
st.set_page_config(page_title=ct.APP_NAME)

# 必要なディレクトリの作成
Path(ct.AUDIO_INPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(ct.AUDIO_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# 画像ファイルの存在チェック
if not Path(ct.AI_ICON_PATH).exists():
    st.warning(f"警告: {ct.AI_ICON_PATH} が見つかりません。")
if not Path(ct.USER_ICON_PATH).exists():
    st.warning(f"警告: {ct.USER_ICON_PATH} が見つかりません。")

# セッション状態の初期化
initialize_session_state(st.session_state)

# OpenAI API キーの確認
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("環境変数 'OPENAI_API_KEY' が設定されていません。")
    st.stop()

# OpenAI クライアントの初期化
if "openai_obj" not in st.session_state:
    st.session_state.openai_obj = OpenAI()

# LLM と メモリの初期化
if "llm" not in st.session_state:
    try:
        st.session_state.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )
        st.session_state.memory = ConversationSummaryBufferMemory(
            llm=st.session_state.llm, max_token_limit=1000, return_messages=True
        )
        st.session_state.chain_basic_conversation = ft.create_chain(
            ct.SYSTEM_TEMPLATE_BASIC_CONVERSATION
        )
    except ValueError as e:
        st.error(f"モデル名が正しくありません: {e}")
        st.stop()
    except Exception as e:
        st.error(f"初期化中にエラーが発生しました: {e}")
        st.stop()

# ===== UIレイアウト =====

display_header()
display_control_panel()
display_welcome_message()

st.divider()

display_message_history()
display_mode_buttons()

dictation_chat_message = display_chat_input()

# ディクテーションモード以外でのチャット入力を無効化
if dictation_chat_message and not st.session_state.chat_open_flg:
    st.stop()

# ===== モード別処理の実行 =====

if st.session_state.start_flg:
    # ディクテーションモード
    if st.session_state.mode == ct.MODE_3 and (
        st.session_state.dictation_button_flg
        or st.session_state.dictation_count == 0
        or st.session_state.dictation_chat_message
    ):
        handle_dictation_mode()

    # 日常英会話モード
    elif st.session_state.mode == ct.MODE_1:
        handle_basic_conversation_mode()

    # シャドーイングモード
    elif st.session_state.mode == ct.MODE_2 and (
        st.session_state.shadowing_button_flg
        or st.session_state.shadowing_count == 0
        or st.session_state.shadowing_audio_input_flg
    ):
        handle_shadowing_mode()
