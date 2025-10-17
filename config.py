"""
アプリケーション設定モジュール

セッション状態の初期化と管理を担当
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class SessionState:
    """セッション状態の初期値を管理するデータクラス"""

    # メッセージ関連
    messages: List[Dict[str, str]] = field(default_factory=list)

    # アプリケーション状態
    start_flg: bool = False
    pre_mode: str = ""

    # シャドーイングモード関連
    shadowing_flg: bool = False
    shadowing_button_flg: bool = False
    shadowing_count: int = 0
    shadowing_first_flg: bool = True
    shadowing_audio_input_flg: bool = False
    shadowing_evaluation_first_flg: bool = True

    # ディクテーションモード関連
    dictation_flg: bool = False
    dictation_button_flg: bool = False
    dictation_count: int = 0
    dictation_first_flg: bool = True
    dictation_chat_message: str = ""
    dictation_evaluation_first_flg: bool = True
    chat_open_flg: bool = False

    # 問題文
    problem: str = ""


def initialize_session_state(st_session_state: Any) -> None:
    """
    セッション状態を初期化する

    Args:
        st_session_state: Streamlitのsession_stateオブジェクト
    """
    if "messages" not in st_session_state:
        default_state = SessionState()
        for key, value in default_state.__dict__.items():
            st_session_state[key] = value
