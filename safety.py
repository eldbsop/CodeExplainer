import re

MAX_FILES = 10
MAX_LINES = 200

# (패턴, 대체 문구) 목록
MASK_PATTERNS = [
    (re.compile(r"AIza[0-9A-Za-z_\-]{20,}"), "[MASKED_API_KEY]"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "[MASKED_API_KEY]"),
    (re.compile(r"ghp_[A-Za-z0-9]{20,}"), "[MASKED_TOKEN]"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "[MASKED_EMAIL]"),
    # KEY=값, token: 값 같은 형태
    (re.compile(
        r"(?i)((?:api[_-]?key|secret|token|password|passwd)\s*[=:]\s*)[\"']?[^\s\"']+[\"']?"
    ), r"\1[MASKED]"),
]


def mask_sensitive(text):
    """민감정보 패턴을 마스킹하고 (결과 텍스트, 마스킹 횟수)를 돌려준다."""
    count = 0
    for pattern, replacement in MASK_PATTERNS:
        text, n = pattern.subn(replacement, text)
        count += n
    return text, count


def limit_diff(diff, max_files=MAX_FILES, max_lines=MAX_LINES):
    """diff를 최대 파일 수/줄 수로 자르고 (결과 텍스트, 잘렸는지 여부)를 돌려준다."""
    # 'diff --git' 기준으로 파일 단위로 나눈다
    chunks = re.split(r"(?m)^(?=diff --git )", diff)
    chunks = [c for c in chunks if c.strip()]

    truncated = False
    if len(chunks) > max_files:
        chunks = chunks[:max_files]
        truncated = True

    result = "".join(chunks)
    lines = result.splitlines()
    if len(lines) > max_lines:
        result = "\n".join(lines[:max_lines])
        truncated = True

    return result, truncated


def apply_safe_mode(diff):
    """safe-mode: 마스킹(A) + 분량 제한(B)을 적용한다."""
    diff, masked = mask_sensitive(diff)
    diff, truncated = limit_diff(diff)
    return diff, masked, truncated
    