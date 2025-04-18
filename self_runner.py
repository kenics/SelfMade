import subprocess
import os
import time
import openai
from datetime import datetime
import sys

# --- パス設定 ---
BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = r"D:\EchoCodeForge"
AGENT_SCRIPT_PATH = os.path.join(PROJECT_ROOT, "agent1.py")
LOG_PATH = os.path.join(BASE_DIR, "run_log.txt")
QA_LOG_PATH = os.path.join(BASE_DIR, "QA.txt")

# --- モジュール検索パス追加 ---
sys.path.append(os.path.join(BASE_DIR, "Config"))
sys.path.append(os.path.join(BASE_DIR, "AutoFixer"))

# --- モジュールインポート ---
from ConfigLoader import ConfigLoader
from fixer import detect_syntax_error_line, extract_error_message
from file_editor import (
    read_context_lines,
    replace_line_in_file,
    replace_function_in_file,
    write_new_class_file
)
from utils import extract_python_code_from_response, extract_class_name_from_code

# --- OpenAI API キー設定 ---
loader = ConfigLoader()
openai.api_key = loader.get_secret("openai_api_key")

# === ユーティリティ関数 ===

def wait_for_run_command():
    while True:
        cmd = input("実行コマンドを入力してください（run）: ").strip().lower()
        if cmd == "run":
            break

def append_log(filepath, content):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(content + "\n")

def run_agent_script():
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    append_log(LOG_PATH, f"{timestamp} === 実行開始 ===")

    process = subprocess.Popen(
        ["python", AGENT_SCRIPT_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=PROJECT_ROOT
    )
    stdout, stderr = process.communicate()

    append_log(LOG_PATH, stdout)
    append_log(LOG_PATH, stderr)

    return stdout, stderr

def detect_error_type(log_text):
    if "SyntaxError" in log_text or "IndentationError" in log_text:
        return "syntax"
    elif "Traceback" in log_text:
        return "runtime"
    return None

def send_to_chatgpt(question):
    append_log(QA_LOG_PATH, "【質問】" + question)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": question}]
    )
    answer = response["choices"][0]["message"]["content"]
    append_log(QA_LOG_PATH, "【回答】" + answer)
    return answer

# === メイン処理 ===

def main():
    wait_for_run_command()
    stdout, stderr = run_agent_script()
    log_text = stdout + "\n" + stderr

    error_type = detect_error_type(log_text)

    if error_type == "syntax":
        print("⚠ 文法エラー検出。修正処理を開始します。")
        filepath, lineno = detect_syntax_error_line(log_text, PROJECT_ROOT)
        if filepath and lineno:
            abs_path = os.path.join(PROJECT_ROOT, filepath)
            print(f"\n対象ファイル: {filepath}（{lineno}行目）")

            print("\n--- 該当行とその前後 ---")
            for lineno_i, line_text in read_context_lines(abs_path, lineno):
                print(f"{lineno_i}: {line_text}")

            new_code = input(f"\n{filepath}:{lineno} に置き換えるコードを入力してください:\n> ").strip()
            if replace_line_in_file(abs_path, lineno, new_code):
                print("✅ 修正完了")
            else:
                print("❌ 修正失敗：行番号が範囲外です")

    elif error_type == "runtime":
        print("⚠ 実行時エラー検出。ChatGPT に問い合わせます。")
        question = f"以下のPython実行時エラーを修正してください:\n{log_text}"
        answer = send_to_chatgpt(question)
        print("ChatGPTの回答:\n", answer)

        # ChatGPT の回答からコードを抽出
        code = extract_python_code_from_response(answer)
        error_type_detail, error_message = extract_error_type_and_message(log_text)

        if error_type_detail:
            print(f"\n🔎 エラー種別: {error_type_detail}")
            print(f"📝 エラー内容: {error_message}")

            if error_type_detail == "SyntaxError":
                # → クラス or 関数の自動修正処理へ
                if code:
                    class_name = extract_class_name_from_code(code)
                    if class_name:
                        print(f"🆕 クラス {class_name} を新規作成します")
                        if write_new_class_file(PROJECT_ROOT, class_name, code):
                            print(f"✅ {class_name}.py を作成しました")
                        else:
                            print("❌ ファイルの作成に失敗しました（既存の可能性あり）")
                    else:
                        filepath, _ = detect_syntax_error_line(log_text, PROJECT_ROOT)
                        abs_path = os.path.join(PROJECT_ROOT, filepath)
                        function_name = input("修正対象の関数名を入力してください: ").strip()
                        if replace_function_in_file(abs_path, function_name, code):
                            print(f"✅ {function_name} 関数を自動修正しました。")
                        else:
                            print("❌ 関数置換に失敗しました。")
                else:
                    print("❌ ChatGPTの回答にコードが見つかりませんでした。")

            elif error_type_detail in ("ImportError", "ModuleNotFoundError"):
                print("🛠 モジュールのインポートに関するエラーです。依存ライブラリの確認が必要です。")
                # TODO: requirements.txt チェック or ChatGPT に import 修正を問い合わせる

            elif error_type_detail in ("TypeError", "ValueError"):
                print("🔧 実行中の型エラー・値エラーです。関数引数や戻り値の確認を進めます。")
                # TODO: 関数の引数と使い方の見直しを ChatGPT に聞くなど

            else:
                print(f"⚠ その他のエラータイプです（{error_type_detail}）。ログを確認してください。")

        else:
            print("❌ エラー種別を特定できませんでした。")

    else:
        print("✅ 実行成功。エラーなし。")

if __name__ == "__main__":
    main()
