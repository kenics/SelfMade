import os
import re

def read_lines(filepath):
    """
    ファイル全体の行をリストで取得
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")

    with open(filepath, encoding="utf-8") as f:
        return f.readlines()

def replace_line_in_file(filepath, lineno, new_line):
    """
    指定ファイルの lineno（1始まり）の行を new_line に置き換える。
    成功時は True、失敗時は False。
    """
    try:
        lines = read_lines(filepath)
        if 1 <= lineno <= len(lines):
            lines[lineno - 1] = new_line.rstrip() + "\n"
            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        else:
            return False
    except Exception as e:
        print(f"行置換エラー: {e}")
        return False

def read_context_lines(filepath, lineno, context=2):
    """
    指定行の前後 context 行（デフォルト前後2行）を含むリストを返す。
    行番号は1始まり。
    """
    try:
        lines = read_lines(filepath)
        start = max(0, lineno - context - 1)
        end = min(len(lines), lineno + context)
        return [(i + 1, lines[i].rstrip()) for i in range(start, end)]
    except Exception as e:
        print(f"コンテキスト読み込みエラー: {e}")
        return []


def replace_function_in_file(filepath, function_name, new_function_code):
    """
    指定された関数名の定義を含む関数ブロックを new_function_code に置き換える。
    """
    lines = read_lines(filepath)
    pattern = re.compile(rf"^\s*def {re.escape(function_name)}\s*\(.*?\):")

    start_index = -1
    end_index = -1

    for i, line in enumerate(lines):
        if pattern.match(line):
            start_index = i
            indent = len(line) - len(line.lstrip())
            for j in range(i + 1, len(lines)):
                next_indent = len(lines[j]) - len(lines[j].lstrip())
                if lines[j].strip() and next_indent <= indent:
                    end_index = j
                    break
            else:
                end_index = len(lines)
            break

    if start_index >= 0 and end_index > start_index:
        new_lines = new_function_code.strip().splitlines()
        new_lines = [l + "\n" for l in new_lines]
        lines[start_index:end_index] = new_lines

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True

    return False

def write_new_class_file(base_dir, class_name, code):
    """
    指定された base_dir（EchoCodeForge）配下に クラス名.py を作成し、
    指定されたコードを書き込む。
    """
    filename = f"{class_name}.py"
    abs_path = os.path.join(base_dir, filename)

    if os.path.exists(abs_path):
        print(f"⚠ ファイル {filename} はすでに存在します。上書きしません。")
        return False

    with open(abs_path, "w", encoding="utf-8") as f:
        f.write(code.strip() + "\n")
    return True