import re

def extract_python_code_from_response(response_text):
    """
    ChatGPT の回答から ```python ... ``` で囲まれたコード部分を抽出して返す。
    """
    match = re.search(r"```python\s*\n(.*?)```", response_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_class_name_from_code(code):
    """
    `class クラス名:` を含む Python コードから最初のクラス名を抽出して返す。
    """
    match = re.search(r'^\s*class\s+(\w+)\s*[:\(]', code, re.MULTILINE)
    if match:
        return match.group(1)
    return None

