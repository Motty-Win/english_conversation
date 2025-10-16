import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from openai import BadRequestError, OpenAI  # 修正: v1系の例外もこちらから

import constants as ct
import functions as ft

# 各種設定
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

# タイトル表示
st.markdown(f"## {ct.APP_NAME}")

# 初期処理
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.start_flg = False
    st.session_state.pre_mode = ""
    st.session_state.shadowing_flg = False
    st.session_state.shadowing_button_flg = False
    st.session_state.shadowing_count = 0
    st.session_state.shadowing_first_flg = True
    st.session_state.shadowing_audio_input_flg = False
    st.session_state.shadowing_evaluation_first_flg = True
    st.session_state.dictation_flg = False
    st.session_state.dictation_button_flg = False
    st.session_state.dictation_count = 0
    st.session_state.dictation_first_flg = True
    st.session_state.dictation_chat_message = ""
    st.session_state.dictation_evaluation_first_flg = True
    st.session_state.chat_open_flg = False
    st.session_state.problem = ""

# 環境変数の取得時にデフォルト値を設定
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    st.error("環境変数 'OPENAI_API_KEY' が設定されていません。")
    st.stop()

# v1クライアントを作成してセッションに保持
if "openai_obj" not in st.session_state:  # 修正: openai_client を openai_obj に変更
    st.session_state.openai_obj = OpenAI()  # APIキーは環境変数から自動読込

# ChatOpenAI のモデル名を確認
try:
    st.session_state.llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,  # 精度を上げるために温度を下げる
    )
except ValueError as e:
    st.error(f"モデル名が正しくありません: {e}")

st.session_state.memory = ConversationSummaryBufferMemory(
    llm=st.session_state.llm, max_token_limit=1000, return_messages=True
)

# モード「日常英会話」用のChain作成
st.session_state.chain_basic_conversation = ft.create_chain(
    ct.SYSTEM_TEMPLATE_BASIC_CONVERSATION
)

# 初期表示
# col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
# 提出課題用
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
    # モードを変更した際の処理
    if st.session_state.mode != st.session_state.pre_mode:
        # 自動でそのモードの処理が実行されないようにする
        st.session_state.start_flg = False
        # 「日常英会話」選択時の初期化処理
        if st.session_state.mode == ct.MODE_1:
            st.session_state.dictation_flg = False
            st.session_state.shadowing_flg = False
        # 「シャドーイング」選択時の初期化処理
        st.session_state.shadowing_count = 0
        if st.session_state.mode == ct.MODE_2:
            st.session_state.dictation_flg = False
        # 「ディクテーション」選択時の初期化処理
        st.session_state.dictation_count = 0
        if st.session_state.mode == ct.MODE_3:
            st.session_state.shadowing_flg = False
        # チャット入力欄を非表示にする
        st.session_state.chat_open_flg = False
    st.session_state.pre_mode = st.session_state.mode
with col4:
    st.session_state.englv = st.selectbox(
        label="英語レベル",
        options=ct.ENGLISH_LEVEL_OPTION,
        label_visibility="collapsed",
    )

with st.chat_message("assistant", avatar="images/ai_icon.jpg"):
    st.markdown(
        "こちらは生成AIによる音声英会話の練習アプリです。何度も繰り返し練習し、英語力をアップさせましょう。"
    )
    st.markdown("**【操作説明】**")
    st.success(
        """
    - モードと再生速度を選択し、「英会話開始」ボタンを押して英会話を始めましょう。
    - モードは「日常英会話」「シャドーイング」「ディクテーション」から選べます。
        - 日常英会話: AIと音声会話を行い、適宜文法添削を受けることができます。
        - シャドーイング: AIがランダムな英文を読み上げ、それを真似て発話。AIが照合・評価を行います。
        - ディクテーション: AIがランダムな英文を読み上げ、チャット欄に入力。AIが照合・評価を行います。
    - 発話後、5秒間沈黙することで音声入力が完了します。
    - 「一時中断」ボタンを押すことで、英会話を一時中断できます。
    """
    )
st.divider()

# メッセージリストの一覧表示
for message in st.session_state.messages:
    if message["role"] == "assistant":
        with st.chat_message(message["role"], avatar="images/ai_icon.jpg"):
            st.markdown(message["content"])
    elif message["role"] == "user":
        with st.chat_message(message["role"], avatar="images/user_icon.jpg"):
            st.markdown(message["content"])
    else:
        st.divider()

# LLMレスポンスの下部にモード実行のボタン表示
if st.session_state.shadowing_flg:
    st.session_state.shadowing_button_flg = st.button("シャドーイング開始")
if st.session_state.dictation_flg:
    st.session_state.dictation_button_flg = st.button("ディクテーション開始")

# 「ディクテーション」モードのチャット入力受付時に実行
if st.session_state.chat_open_flg:
    st.info(
        "AIが読み上げた音声を、画面下部のチャット欄からそのまま入力・送信してください。"
    )

st.session_state.dictation_chat_message = st.chat_input(
    "※「ディクテーション」選択時以外は送信不可"
)

if st.session_state.dictation_chat_message and not st.session_state.chat_open_flg:
    st.stop()

# 「英会話開始」ボタンが押された場合の処理
if st.session_state.start_flg:

    # モード：「ディクテーション」
    # 「ディクテーション」ボタン押下時か、「英会話開始」ボタン押下時か、チャット送信時
    if st.session_state.mode == ct.MODE_3 and (
        st.session_state.dictation_button_flg
        or st.session_state.dictation_count == 0
        or st.session_state.dictation_chat_message
    ):
        if st.session_state.dictation_first_flg:
            st.session_state.chain_create_problem = ft.create_chain(
                ct.SYSTEM_TEMPLATE_CREATE_PROBLEM
            )
            st.session_state.dictation_first_flg = False
        # チャット入力以外
        if not st.session_state.chat_open_flg:
            with st.spinner("問題文生成中..."):
                st.session_state.problem, llm_response_audio = (
                    ft.create_problem_and_play_audio()
                )

            st.session_state.chat_open_flg = True
            st.session_state.dictation_flg = False
            st.rerun()
        # チャット入力時の処理
        else:
            # チャット欄から入力された場合にのみ評価処理が実行されるようにする
            if not st.session_state.dictation_chat_message:
                st.stop()

            # AIメッセージとユーザーメッセージの画面表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(st.session_state.problem)
            with st.chat_message("user", avatar=ct.USER_ICON_PATH):
                st.markdown(st.session_state.dictation_chat_message)

            # LLMが生成した問題文とチャット入力値をメッセージリストに追加
            st.session_state.messages.append(
                {"role": "assistant", "content": st.session_state.problem}
            )
            st.session_state.messages.append(
                {"role": "user", "content": st.session_state.dictation_chat_message}
            )

            with st.spinner("評価結果の生成中..."):
                system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                    llm_text=st.session_state.problem,
                    user_text=st.session_state.dictation_chat_message,
                )
                st.session_state.chain_evaluation = ft.create_chain(system_template)
                # 問題文と回答を比較し、評価結果の生成を指示するプロンプトを作成
                llm_response_evaluation = ft.create_evaluation()

            # 評価結果のメッセージリストへの追加と表示
            with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
                st.markdown(llm_response_evaluation)
                # 問題文の日本語訳を表示
                with st.expander("問題文の日本語訳を表示"):
                    with st.spinner("翻訳中..."):
                        translated_problem = ft.translate_text(st.session_state.problem)
                        st.markdown(translated_problem)
            st.session_state.messages.append(
                {"role": "assistant", "content": llm_response_evaluation}
            )
            st.session_state.messages.append({"role": "other"})

            # 各種フラグの更新
            st.session_state.dictation_flg = True
            st.session_state.dictation_chat_message = ""
            st.session_state.dictation_count += 1
            st.session_state.chat_open_flg = False

            st.rerun()

    # モード：「日常英会話」
    if st.session_state.mode == ct.MODE_1:
        # 音声入力を受け取って音声ファイルを作成
        audio_input_file_path = (
            f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        )
        ft.record_audio(audio_input_file_path)

        # 音声入力ファイルから文字起こしテキストを取得
        with st.spinner("音声入力をテキストに変換中..."):
            transcript = ft.transcribe_audio(audio_input_file_path)
            audio_input_text = transcript.text

        # 音声入力テキストの画面表示
        with st.chat_message("user", avatar=ct.USER_ICON_PATH):  # 修正: アイコンを固定
            st.markdown(audio_input_text)
            # ユーザー返答の日本語訳を表示
            with st.expander("日本語訳を表示"):
                with st.spinner("翻訳中..."):
                    translated_user_text = ft.translate_text(audio_input_text)
                    st.markdown(translated_user_text)

        with st.spinner("回答の音声読み上げ準備中..."):
            voice_type = "nova"  # 女性の声に固定
            client = st.session_state.openai_obj
            try:
                # 1) テキスト応答
                chat = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": audio_input_text}],
                    temperature=0.3,
                )
                llm_response_text = chat.choices[0].message.content

                # 2) TTS（WAVで受け取りたいので response_format="wav" を指定）
                speech = client.audio.speech.create(
                    model="tts-1",
                    voice=voice_type,
                    input=llm_response_text,  # type: ignore
                    response_format="wav",
                )

                audio_output_file_path = (
                    f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
                )
                # speech.content はバイナリ（bytes）
                ft.save_to_wav(speech.content, audio_output_file_path)

            except BadRequestError as e:
                st.error(f"OpenAI API 呼び出し中にエラーが発生しました: {e}")
                st.stop()

        # 音声ファイルの読み上げ
        ft.play_wav(audio_output_file_path, speed=st.session_state.speed)

        # AIメッセージの画面表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(llm_response_text)
            # 日本語翻訳ボタン
            with st.expander("日本語訳を表示"):
                with st.spinner("翻訳中..."):
                    translated_text = ft.translate_text(llm_response_text)  # type: ignore
                    st.markdown(translated_text)

        # ユーザー入力値とLLMからの回答をメッセージ一覧に追加
        st.session_state.messages.append({"role": "user", "content": audio_input_text})
        st.session_state.messages.append(
            {"role": "assistant", "content": llm_response_text}
        )

    # モード：「シャドーイング」
    # 「シャドーイング」ボタン押下時か、「英会話開始」ボタン押下時
    if st.session_state.mode == ct.MODE_2 and (
        st.session_state.shadowing_button_flg
        or st.session_state.shadowing_count == 0
        or st.session_state.shadowing_audio_input_flg
    ):
        if st.session_state.shadowing_first_flg:
            st.session_state.chain_create_problem = ft.create_chain(
                ct.SYSTEM_TEMPLATE_CREATE_PROBLEM
            )
            st.session_state.shadowing_first_flg = False

        if not st.session_state.shadowing_audio_input_flg:
            with st.spinner("問題文生成中..."):
                st.session_state.problem, llm_response_audio = (
                    ft.create_problem_and_play_audio()
                )

        # 音声入力を受け取って音声ファイルを作成
        st.session_state.shadowing_audio_input_flg = True
        audio_input_file_path = (
            f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
        )
        ft.record_audio(audio_input_file_path)
        st.session_state.shadowing_audio_input_flg = False

        with st.spinner("音声入力をテキストに変換中..."):
            # 音声入力ファイルから文字起こしテキストを取得
            transcript = ft.transcribe_audio(audio_input_file_path)
            audio_input_text = transcript.text

        # AIメッセージとユーザーメッセージの画面表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(st.session_state.problem)
        with st.chat_message("user", avatar=ct.USER_ICON_PATH):
            st.markdown(audio_input_text)

        # LLMが生成した問題文と音声入力値をメッセージリストに追加
        st.session_state.messages.append(
            {"role": "assistant", "content": st.session_state.problem}
        )
        st.session_state.messages.append({"role": "user", "content": audio_input_text})

        with st.spinner("評価結果の生成中..."):
            if st.session_state.shadowing_evaluation_first_flg:
                system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                    llm_text=st.session_state.problem, user_text=audio_input_text
                )
                st.session_state.chain_evaluation = ft.create_chain(system_template)
                st.session_state.shadowing_evaluation_first_flg = False
            # 問題文と回答を比較し、評価結果の生成を指示するプロンプトを作成
            llm_response_evaluation = ft.create_evaluation()

        # 評価結果のメッセージリストへの追加と表示
        with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
            st.markdown(llm_response_evaluation)
            # 問題文の日本語訳を表示
            with st.expander("問題文の日本語訳を表示"):
                with st.spinner("翻訳中..."):
                    translated_problem = ft.translate_text(st.session_state.problem)
                    st.markdown(translated_problem)
        st.session_state.messages.append(
            {"role": "assistant", "content": llm_response_evaluation}
        )
        st.session_state.messages.append({"role": "other"})

        # 各種フラグの更新
        st.session_state.shadowing_flg = True
        st.session_state.shadowing_count += 1

        # 「シャドーイング」ボタンを表示するために再描画
        st.session_state.shadowing_flg = True
        st.session_state.shadowing_count += 1
        st.rerun()
