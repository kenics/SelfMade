import os
import difflib
from pathlib import Path

def read_lines(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.readlines()

def read_context_lines(filepath, lineno, context=2):
    """
    指定された行番号を中心に前後の context 行数を含めて返す。
    戻り値: [(行番号, 行テキスト), ...]
    """
    lines = read_lines(filepath)
    start = max(0, lineno - context - 1)
    end = min(len(lines), lineno + context)
    return [(i + 1, lines[i].rstrip()) for i in range(start, end)]

def replace_line_in_file(filepath, lineno, new_line):
    """
    指定ファイルの lineno（1始まり）の行を new_line に置き換える。
    元の改行コード（\n または \r\n）を保持して上書きする。
    """
    try:
        lines = read_lines(filepath)
        if 1 <= lineno <= len(lines):
            old_line = lines[lineno - 1]

            # 改行コードを判別
            if old_line.endswith('\r\n'):
                newline = '\r\n'
            elif old_line.endswith('\n'):
                newline = '\n'
            else:
                newline = ''

            lines[lineno - 1] = new_line.rstrip() + newline

            with open(filepath, "w", encoding="utf-8") as f:
                f.writelines(lines)
            return True
        else:
            return False
    except Exception as e:
        print(f"行置換エラー: {e}")
        return False

def replace_function_in_file(filepath, function_name, new_code):
    """
    指定ファイル内の function_name に一致する関数定義を new_code で置換。
    関数定義の開始〜次の関数/クラス定義の直前までを対象とする。
    """
    try:
        lines = read_lines(filepath)
        start = end = None

        for i, line in enumerate(lines):
            if line.strip().startswith(f"def {function_name}("):
                start = i
                break

        if start is None:
            print(f"関数 {function_name} が見つかりません。")
            return False

        # 関数終了行を検出
        for j in range(start + 1, len(lines)):
            if lines[j].strip().startswith(("def ", "class ")):
                end = j
                break
        if end is None:
            end = len(lines)

        # 差し替え
        new_lines = [l + "\n" for l in new_code.strip().splitlines()]
        lines[start:end] = new_lines

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    except Exception as e:
        print(f"関数置換エラー: {e}")
        return False

def write_new_class_file(project_root, class_name, code):
    """
    指定された class_name を元に、project_root 配下に <class_name>.py を新規作成。
    既に存在する場合は False を返す。
    """
    filename = os.path.join(project_root, f"{class_name}.py")
    if os.path.exists(filename):
        print(f"{filename} は既に存在します。")
        return False

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code.strip() + "\n")
        return True
    except Exception as e:
        print(f"ファイル作成エラー: {e}")
        return False

def generate_diff_file(original_lines, new_lines, context_line_info, target_filepath, output_dir):
    """
    差分ファイル（unified diff 形式）を <元ファイル名>-dff.txt として保存する。

    Parameters:
    - original_lines: 修正前の行リスト（str）
    - new_lines: 修正後の行リスト（str）
    - context_line_info: [(行番号, 行内容)] のリスト（見た目確認のため）
    - target_filepath: 修正対象の .py ファイルの絶対パス
    - output_dir: 差分ファイルの保存先（通常は BASE_DIR/Diff）
    """
    project_root = os.environ.get("PROJECT_ROOT")
    if not project_root:
        project_root = os.path.abspath(os.path.join(target_filepath, os.pardir, os.pardir))

    # WindowsのバックスラッシュをUNIXスタイルに変換（Git apply対策）
    rel_path = os.path.relpath(target_filepath, start=project_root).replace("\\", "/")
    #rel_path = os.path.basename(target_filepath)
    diff_header = f"diff --git a/{rel_path} b/{rel_path}"
    filename = Path(target_filepath).name
    diff_filename = os.path.join(output_dir, f"{filename}-dff.txt")


    diff = [diff_header] + list(difflib.unified_diff(
        original_lines,
        new_lines,
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
        lineterm=""
    ))

    with open(diff_filename, "w", encoding="utf-8") as f:
        f.writelines(line + "\n" for line in diff)

    print(f"✅ 差分ファイルを生成しました: {diff_filename}")