"""
モード別の処理を担当するハンドラーモジュール
"""

import time
from typing import Any

import streamlit as st
from openai import BadRequestError

import constants as ct
import functions as ft


def handle_basic_conversation_mode() -> None:
    """日常英会話モードの処理"""
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
    _display_user_message_with_translation(audio_input_text)

    # AI応答の生成と音声化
    llm_response_text = _generate_and_play_response(audio_input_text)

    # AIメッセージの画面表示
    _display_assistant_message_with_translation(llm_response_text)

    # メッセージ履歴に追加
    st.session_state.messages.append({"role": "user", "content": audio_input_text})
    st.session_state.messages.append(
        {"role": "assistant", "content": llm_response_text}
    )


def handle_shadowing_mode() -> None:
    """シャドーイングモードの処理"""
    # 初回のみチェイン作成
    if st.session_state.shadowing_first_flg:
        st.session_state.chain_create_problem = ft.create_chain(
            ct.SYSTEM_TEMPLATE_CREATE_PROBLEM
        )
        st.session_state.shadowing_first_flg = False

    # 問題文生成（音声入力フラグが立っていない場合のみ）
    if not st.session_state.shadowing_audio_input_flg:
        with st.spinner("問題文生成中..."):
            st.session_state.problem, _ = ft.create_problem_and_play_audio()

    # 音声入力
    st.session_state.shadowing_audio_input_flg = True
    audio_input_file_path = (
        f"{ct.AUDIO_INPUT_DIR}/audio_input_{int(time.time())}.wav"
    )
    ft.record_audio(audio_input_file_path)
    st.session_state.shadowing_audio_input_flg = False

    # 文字起こし
    with st.spinner("音声入力をテキストに変換中..."):
        transcript = ft.transcribe_audio(audio_input_file_path)
        audio_input_text = transcript.text

    # 問題文と回答を表示
    _display_problem_and_answer(st.session_state.problem, audio_input_text)

    # 評価
    evaluation = _generate_evaluation(st.session_state.problem, audio_input_text, "shadowing")
    _display_evaluation_with_translation(evaluation, st.session_state.problem)

    # 状態更新
    st.session_state.shadowing_flg = True
    st.session_state.shadowing_count += 1
    st.rerun()


def handle_dictation_mode() -> None:
    """ディクテーションモードの処理"""
    # 初回のみチェイン作成
    if st.session_state.dictation_first_flg:
        st.session_state.chain_create_problem = ft.create_chain(
            ct.SYSTEM_TEMPLATE_CREATE_PROBLEM
        )
        st.session_state.dictation_first_flg = False

    # チャット入力待機中でない場合（問題文生成）
    if not st.session_state.chat_open_flg:
        with st.spinner("問題文生成中..."):
            st.session_state.problem, _ = ft.create_problem_and_play_audio()

        st.session_state.chat_open_flg = True
        st.session_state.dictation_flg = False
        st.rerun()
    # チャット入力時の評価処理
    else:
        if not st.session_state.dictation_chat_message:
            st.stop()

        # 問題文と回答を表示
        _display_problem_and_answer(
            st.session_state.problem, st.session_state.dictation_chat_message
        )

        # 評価
        evaluation = _generate_evaluation(
            st.session_state.problem,
            st.session_state.dictation_chat_message,
            "dictation",
        )
        _display_evaluation_with_translation(evaluation, st.session_state.problem)

        # 状態更新
        st.session_state.dictation_flg = True
        st.session_state.dictation_chat_message = ""
        st.session_state.dictation_count += 1
        st.session_state.chat_open_flg = False
        st.rerun()


# ===== プライベートヘルパー関数 =====


def _display_user_message_with_translation(text: str) -> None:
    """ユーザーメッセージを翻訳付きで表示"""
    with st.chat_message("user", avatar=ct.USER_ICON_PATH):
        st.markdown(text)
        with st.expander("日本語訳を表示"):
            with st.spinner("翻訳中..."):
                translated_text = ft.translate_text(text)
                st.markdown(translated_text)


def _display_assistant_message_with_translation(text: str) -> None:
    """アシスタントメッセージを翻訳付きで表示"""
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(text)
        with st.expander("日本語訳を表示"):
            with st.spinner("翻訳中..."):
                translated_text = ft.translate_text(text)
                st.markdown(translated_text)


def _generate_and_play_response(user_input: str) -> str:
    """ユーザー入力に対する応答を生成して再生"""
    with st.spinner("回答の音声読み上げ準備中..."):
        client = st.session_state.openai_obj
        try:
            # テキスト応答生成
            chat = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": user_input}],
                temperature=0.3,
            )
            response_text = chat.choices[0].message.content

            # 音声合成
            speech = client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=response_text,
                response_format="wav",
            )

            # 音声保存と再生
            audio_output_file_path = (
                f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
            )
            ft.save_to_wav(speech.content, audio_output_file_path)

        except BadRequestError as e:
            st.error(f"OpenAI API 呼び出し中にエラーが発生しました: {e}")
            st.stop()

    # 音声再生
    ft.play_wav(audio_output_file_path, speed=st.session_state.speed)

    return response_text


def _display_problem_and_answer(problem: str, answer: str) -> None:
    """問題文と回答を表示"""
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(problem)
    with st.chat_message("user", avatar=ct.USER_ICON_PATH):
        st.markdown(answer)

    # メッセージ履歴に追加
    st.session_state.messages.append({"role": "assistant", "content": problem})
    st.session_state.messages.append({"role": "user", "content": answer})


def _generate_evaluation(problem: str, answer: str, mode: str) -> str:
    """評価を生成"""
    with st.spinner("評価結果の生成中..."):
        # シャドーイングまたはディクテーションの初回のみチェイン作成
        evaluation_first_flg = (
            st.session_state.shadowing_evaluation_first_flg
            if mode == "shadowing"
            else st.session_state.dictation_evaluation_first_flg
        )

        if evaluation_first_flg:
            system_template = ct.SYSTEM_TEMPLATE_EVALUATION.format(
                llm_text=problem, user_text=answer
            )
            st.session_state.chain_evaluation = ft.create_chain(system_template)

            if mode == "shadowing":
                st.session_state.shadowing_evaluation_first_flg = False
            else:
                st.session_state.dictation_evaluation_first_flg = False

        return ft.create_evaluation()


def _display_evaluation_with_translation(evaluation: str, problem: str) -> None:
    """評価結果を翻訳付きで表示"""
    with st.chat_message("assistant", avatar=ct.AI_ICON_PATH):
        st.markdown(evaluation)
        with st.expander("問題文の日本語訳を表示"):
            with st.spinner("翻訳中..."):
                translated_problem = ft.translate_text(problem)
                st.markdown(translated_problem)

    # メッセージ履歴に追加
    st.session_state.messages.append({"role": "assistant", "content": evaluation})
    st.session_state.messages.append({"role": "other"})
