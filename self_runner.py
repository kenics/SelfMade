import subprocess
import os
import time
import openai
from datetime import datetime

# === 設定 ===
AGENT_SCRIPT_PATH = r"D:\EchoCodeForge\agent1.py"
LOG_PATH = "run_log.txt"
QA_LOG_PATH = "QA.txt"
PROJECT_ROOT = r"D:\EchoCodeForge"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 環境変数で設定しておくこと

openai.api_key = OPENAI_API_KEY

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

def detect_syntax_or_runtime_error(log_text):
    if "SyntaxError" in log_text or "IndentationError" in log_text:
        return "syntax"
    elif "Traceback" in log_text:
        return "runtime"
    return None

def extract_error_details(log_text):
    lines = log_text.splitlines()
    for line in lines:
        if ".py" in line and (("SyntaxError" in line) or ("Traceback" in line)):
            return line.strip()
    return "詳細不明のエラー"

def send_to_chatgpt(question):
    append_log(QA_LOG_PATH, "【質問】" + question)
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": question}
        ]
    )
    answer = response["choices"][0]["message"]["content"]
    append_log(QA_LOG_PATH, "【回答】" + answer)
    return answer

def main():
    wait_for_run_command()
    stdout, stderr = run_agent_script()

    log_text = stdout + "\n" + stderr
    error_type = detect_syntax_or_runtime_error(log_text)

    if error_type == "syntax":
        print("⚠ 文法エラー検出。対象ファイルを修正します（手動または自動で対応）")
        error_info = extract_error_details(log_text)
        print("エラー内容:", error_info)
        # TODO: error_info から対象ファイル名・行番号を抽出して、自動修正を行う処理を追加
    elif error_type == "runtime":
        print("⚠ 実行時エラー検出。ChatGPTに問い合わせます。")
        error_info = extract_error_details(log_text)
        answer = send_to_chatgpt(f"以下のPython実行エラーを修正したい:\n{log_text}\nエラー: {error_info}")
        print("ChatGPTの回答:", answer)
        # TODO: 回答に応じて修正・新規クラス追加などを行う処理を追加
    else:
        print("✅ エラーは検出されませんでした。")

if __name__ == "__main__":
    main()
