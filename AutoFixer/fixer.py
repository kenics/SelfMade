import re
import os

def detect_syntax_error_line(log_text, project_root):
    """
    log_text 内から SyntaxError や Traceback の位置を検出し、
    EchoCodeForge 以下の相対パスとエラー行番号を返す。

    例:
      File "D:\\EchoCodeForge\\Sb3BlockGen\\Script.py", line 8
      → ("Sb3BlockGen\\Script.py", 8)
    """
    pattern = r'File "(.*?\\EchoCodeForge\\)(.+?\.py)", line (\d+)'
    match = re.search(pattern, log_text)
    if match:
        _, relative_path, lineno = match.groups()
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

def detect_syntax_error_line(log_text, project_root):
    """
    log_text 内の Traceback から、最後に出現する 'File "..."' の行を取得して、
    EchoCodeForge 以下の相対パスと行番号を返す。
    """
    # 複数の File "..." をすべて見つける
    pattern = r'File "(.*?\\EchoCodeForge\\)(.+?\.py)", line (\d+)'
    matches = re.findall(pattern, log_text)

    if matches:
        # 最後の File が実際のエラー位置
        _, relative_path, lineno = matches[-1]
        return os.path.normpath(relative_path), int(lineno)

    return None, None
