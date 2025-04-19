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
QATEMP_LOG_PATH = os.path.join(BASE_DIR, "QAtemp.txt") 

# --- モジュール検索パス追加 ---
sys.path.append(os.path.join(BASE_DIR, "Config"))
sys.path.append(os.path.join(BASE_DIR, "AutoFixer"))

# --- モジュールインポート ---
from ConfigLoader import ConfigLoader
from DeBug import DeBug

debug = DeBug()

from fixer import (
    detect_syntax_error_line,
    extract_error_message,
    extract_error_type_and_message  # ← 正しく定義されていればOK
)

from file_editor import (
    read_context_lines,
    replace_line_in_file,
    replace_function_in_file,
    write_new_class_file
)
from utils import (
    extract_python_code_from_response,
    extract_class_name_from_code
)

# --- OpenAI API キー設定 ---
loader = ConfigLoader()
api_key = loader.get_secret("openai_api_key")
client = openai.OpenAI(api_key=api_key)
ai_enabled = loader.get("ai_enabled", True)

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

def send_to_chatgpt(question,client):
    append_log(QA_LOG_PATH, "【質問】" + question)
    if ai_enabled:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": question}]
        )
        answer = response.choices[0].message.content
        append_log(QA_LOG_PATH, "【回答】" + answer)

        # --- QAtemp.txt: 回答だけを上書き保存 ---
        with open(QATEMP_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(answer)

        return answer
    else:
        # --- QAtemp.txt の内容を回答として読み込む ---
        try:
            with open(QATEMP_LOG_PATH, "r", encoding="utf-8") as f:
                answer = f.read().strip()
                print("💡 QAtemp.txt から回答を読み込みました。")
                append_log(QA_LOG_PATH, "【回答（ファイルから）】" + answer)
                return answer
        except FileNotFoundError:
            print("❌ QAtemp.txt が存在しません。")
            return ""
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
            context_lines = read_context_lines(abs_path, lineno)
            for lineno_i, line_text in context_lines:
                print(f"{lineno_i}: {line_text}")

            # ChatGPT に送るためのコード生成
            context_code = "\n".join(line_text for _, line_text in context_lines)
            chatgpt_question = (
                f"以下のPythonコードには文法エラーがあります。\n"
                f"{lineno} 行目付近に問題があります。文法的に正しい形に修正してください：\n\n"
                f"```python\n{context_code}\n```"
            )
            # 1. 問い合わせ内容を表示
            print("\n=== ChatGPT に送信する質問内容 ===\n")
            print(chatgpt_question)
            print("\nこの内容で問い合わせますか？（yes で問い合わせを実行）")
            confirm = input("> ").strip().lower()

            if confirm != "yes":
                print("ChatGPTに問い合わせず、終了しました。")
                return

            answer = send_to_chatgpt(chatgpt_question,client)
            print("ChatGPTの回答:\n", answer)

            code = extract_python_code_from_response(answer)
            if code:
                new_code_lines = code.splitlines()
                print("\n--- 修正後のコード ---")
                for i, line in enumerate(new_code_lines, start=1):
                    print(f"{i}: {line}")

                confirm = input("このコードで置き換えますか？（y[yes]/n[no]）: ").strip().lower()
                if confirm in( "y","yes"):
                    for i, (lineno_i, original_line) in enumerate(context_lines):
                        if i < len(new_code_lines):
                            new_line = new_code_lines[i]
                            if new_line.replace('\r', '').replace('\n', '').lstrip() != original_line.replace('\r', '').replace('\n', '').lstrip():
                                debug.print(str(lineno_i) + "行目 " + original_line + " new:" + new_line)
                                replace_line_in_file(abs_path, lineno_i, new_code_lines[i])
                    print("✅ 該当行を修正しました。")
                    # --- Git diff を表示するか確認 ---
                    show_diff = input("修正後の diff を表示しますか？（y[yes]/n[no]）: ").strip().lower()
                    if show_diff in ("y", "yes"):
                        print("\n=== Git Diff ===")
                        os.system(f"git -C \"{PROJECT_ROOT}\" diff \"{abs_path}\"")
                else:
                    print("⚠ 修正をキャンセルしました。")
            else:
                print("❌ ChatGPTの回答に修正コードが見つかりませんでした。")

    elif error_type == "runtime":
        print("⚠ 実行時エラー検出。ChatGPT に問い合わせます。")
        question = f"以下のPython実行時エラーを修正してください:\n{log_text}"
        # 1. 問い合わせ内容を表示
        print("\n=== ChatGPT に送信する質問内容 ===\n")
        print(question)
        print("\nこの内容で問い合わせますか？（yes で実行）")
        confirm = input("> ").strip().lower()

        if confirm != "yes":
            print("ChatGPTに問い合わせず、終了しました。")
            return
        
        answer = send_to_chatgpt(question,client)
        print("ChatGPTの回答:\n", answer)

        code = extract_python_code_from_response(answer)
        error_type_detail, error_message = extract_error_type_and_message(log_text)

        if error_type_detail:
            print(f"\n🔎 エラー種別: {error_type_detail}")
            print(f"📝 エラー内容: {error_message}")

            if error_type_detail == "SyntaxError":
                # このケースは通常 runtime には含まれないが念のため対応
                pass

            elif error_type_detail in ("ImportError", "ModuleNotFoundError"):
                print("🛠 モジュールのインポートに関するエラーです。依存ライブラリの確認が必要です。")

            elif error_type_detail in ("TypeError", "ValueError"):
                print("🔧 実行中の型エラー・値エラーです。関数引数や戻り値の確認が必要です。")

            else:
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
                    print("❌ ChatGPTの回答に修正コードが見つかりませんでした。")
        else:
            print("❌ エラー種別を特定できませんでした。")

    else:
        print("✅ 実行成功。エラーなし。")

if __name__ == "__main__":
    main()
