import re
import os

def detect_syntax_error_line(log_text, project_root):
    """
    log_text 内の Traceback から、最後に出現する 'File "..."' の行を取得して、
    EchoCodeForge 以下の相対パスと行番号を返す。
    """
    pattern = r'File "(.*?\\EchoCodeForge\\)(.+?\.py)", line (\d+)'
    matches = re.findall(pattern, log_text)

    if matches:
        # 最後の File が実際のエラー位置
        _, relative_path, lineno = matches[-1]
        return os.path.normpath(relative_path), int(lineno)

    return None, None

def extract_error_message(log_text):
    """
    エラーメッセージの中から SyntaxError や Exception を含む行を最初に返す。
    なければ "不明なエラー" を返す。
    """
    for line in log_text.splitlines():
        if any(keyword in line for keyword in ["SyntaxError", "IndentationError", "Exception", "Traceback"]):
            return line.strip()
    return "不明なエラー"

def extract_error_type_and_message(log_text):
    """
    Traceback の最後に出現するエラーの種類とメッセージを分離して取得する。
    例: "SyntaxError: '(' was never closed" → ("SyntaxError", "'(' was never closed")
    """
    lines = log_text.strip().splitlines()

    # 下から順に確認し、":" を含むエラー行を探す
    for line in reversed(lines):
        if ":" in line:
            parts = line.strip().split(":", 1)
            if len(parts) == 2:
                error_type = parts[0].strip()
                message = parts[1].strip()
                return error_type, message

    return None, None

def extract_first_traceback_file_and_line(log_text):
    """
    Traceback の最初のファイルと行番号を正規表現で抽出する。
    万が一 detect_syntax_error_line に失敗したとき用。
    """
    pattern = r'File "(.+?\.py)", line (\d+)'
    match = re.search(pattern, log_text)
    if match:
        return match.group(1), int(match.group(2))
    return None, None
