"""
UI コンポーネントモジュール

Streamlit UIコンポーネントの表示を担当
"""

from typing import Optional

import streamlit as st

import constants as ct


def display_header() -> None:
    """ヘッダーとタイトルを表示"""
    st.markdown(f"## {ct.APP_NAME}")


def display_welcome_message() -> None:
    """ウェルカムメッセージと操作説明を表示"""
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(
            "こちらは生成AIによる音声英会話の練習アプリです。何度も繰り返し練習し、英語力をアップさせましょう。"
        )
        st.markdown("**【操作説明】**")
        st.success(
            """
        - モードと再生速度を選択し、「開始」ボタンを押して英会話を始めましょう。
        - モードは「日常英会話」「シャドーイング」「ディクテーション」から選べます。
            - 日常英会話: AIと音声会話を行い、適宜文法添削を受けることができます。
            - シャドーイング: AIがランダムな英文を読み上げ、それを真似て発話。AIが照合・評価を行います。
            - ディクテーション: AIがランダムな英文を読み上げ、チャット欄に入力。AIが照合・評価を行います。
        - 発話後、3秒間沈黙することで音声入力が完了します。
        """
        )


def display_control_panel() -> None:
    """
    コントロールパネル（ボタン、セレクトボックス）を表示

    Returns:
        None（セッション状態を直接更新）
    """
    col1, col2, col3, col4 = st.columns([2, 2, 3, 3])

    with col1:
        if st.session_state.start_flg:
            st.button("開始", use_container_width=True, type="primary")
        else:
            st.session_state.start_flg = st.button(
                "開始", use_container_width=True, type="primary"
            )

    with col2:
        st.session_state.speed = st.selectbox(
            label="再生速度",
            options=ct.PLAY_SPEED_OPTION,
            index=3,
            label_visibility="collapsed",
        )

    with col3:
        st.session_state.mode = st.selectbox(
            label="モード",
            options=[ct.MODE_1, ct.MODE_2, ct.MODE_3],
            label_visibility="collapsed",
        )
        _handle_mode_change()
        st.session_state.pre_mode = st.session_state.mode

    with col4:
        st.session_state.englv = st.selectbox(
            label="英語レベル",
            options=ct.ENGLISH_LEVEL_OPTION,
            label_visibility="collapsed",
        )


def display_message_history() -> None:
    """メッセージ履歴を表示"""
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message(message["role"], avatar=ct.AI_ICON_PATH):
                st.markdown(message["content"])
        elif message["role"] == "user":
            with st.chat_message(message["role"], avatar=ct.USER_ICON_PATH):
                st.markdown(message["content"])
        else:
            st.divider()


def display_mode_buttons() -> None:
    """モード実行用のボタンを表示"""
    if st.session_state.shadowing_flg:
        st.session_state.shadowing_button_flg = st.button("シャドーイング開始")
    if st.session_state.dictation_flg:
        st.session_state.dictation_button_flg = st.button("ディクテーション開始")


def display_chat_input() -> Optional[str]:
    """
    チャット入力欄を表示

    Returns:
        入力されたメッセージ（入力がない場合はNone）
    """
    if st.session_state.chat_open_flg:
        st.info(
            "AIが読み上げた音声を、画面下部のチャット欄からそのまま入力・送信してください。"
        )

    st.session_state.dictation_chat_message = st.chat_input(
        "※「ディクテーション」選択時以外は送信不可"
    )

    return st.session_state.dictation_chat_message


# ===== プライベートヘルパー関数 =====


def _handle_mode_change() -> None:
    """モード変更時の処理"""
    if st.session_state.mode == st.session_state.pre_mode:
        return

    # 共通処理
    st.session_state.start_flg = False
    st.session_state.chat_open_flg = False

    # モード別の初期化
    if st.session_state.mode == ct.MODE_1:  # 日常英会話
        st.session_state.dictation_flg = False
        st.session_state.shadowing_flg = False
    elif st.session_state.mode == ct.MODE_2:  # シャドーイング
        st.session_state.dictation_flg = False
        st.session_state.shadowing_count = 0
    elif st.session_state.mode == ct.MODE_3:  # ディクテーション
        st.session_state.shadowing_flg = False
        st.session_state.dictation_count = 0
