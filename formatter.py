import re

COMMIT_TITLE_RECOMMENDED = 50
COMMIT_TITLE_MAX = 72
PR_TITLE_MAX = 80
PR_SECTIONS = ["Why", "What", "How to Test"]


def strip_markdown(text):
    """AI가 붙인 마크다운 기호와 코드 펜스를 제거한다."""
    text = re.sub(r"```[a-zA-Z]*\n?", "", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"(?m)^\s*-{3,}\s*$", "", text)
    return text.strip()


def truncate(text, limit):
    """제목이 너무 길면 limit자로 자른다."""
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def format_commit(raw):
    """커밋 메시지를 정리하고 (메시지, 경고 목록)을 돌려준다."""
    warnings = []
    text = strip_markdown(raw)
    lines = [line.rstrip() for line in text.splitlines()]

    # 첫 번째로 내용이 있는 줄을 제목으로 쓴다
    while lines and not lines[0].strip():
        lines.pop(0)
    if not lines:
        return "", ["AI 응답이 비어 있습니다."]

    title = lines[0].strip()
    body = "\n".join(lines[1:]).strip()

    if len(title) > COMMIT_TITLE_MAX:
        warnings.append(f"커밋 제목이 {len(title)}자라 {COMMIT_TITLE_MAX}자로 잘랐습니다.")
        title = truncate(title, COMMIT_TITLE_MAX)
    elif len(title) > COMMIT_TITLE_RECOMMENDED:
        warnings.append(
            f"커밋 제목이 {len(title)}자입니다. ({COMMIT_TITLE_RECOMMENDED}자 이내 권장)"
        )

    message = title + ("\n\n" + body if body else "")
    return message, warnings


def parse_pr(raw):
    """AI 응답에서 (제목, 본문)을 분리한다."""
    text = strip_markdown(raw)
    title_match = re.search(r"(?im)^\s*TITLE:\s*(.+)$", text)
    body_match = re.search(r"(?is)^\s*BODY:\s*\n?(.*)$", text, re.MULTILINE)

    if title_match:
        title = title_match.group(1).strip()
    else:
        title = text.splitlines()[0].strip() if text else ""

    body_start = re.search(r"(?im)^\s*BODY:\s*$", text)
    if body_start:
        body = text[body_start.end():].strip()
    else:
        header = re.search(r"(?m)^##\s", text)
        body = text[header.start():].strip() if header else ""
    return title, body


def section_has_bullet(body, name):
    """해당 섹션 안에 불릿이 1개 이상 있는지 확인한다."""
    pattern = rf"(?ms)^##\s*{re.escape(name)}\s*\n(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, body)
    if not match:
        return False
    return any(line.strip().startswith(("- ", "* ")) for line in match.group(1).splitlines())


def format_pr(raw):
    """PR 제목/본문을 정리하고 (제목, 본문, 경고 목록)을 돌려준다."""
    warnings = []
    title, body = parse_pr(raw)

    if len(title) > PR_TITLE_MAX:
        warnings.append(f"PR 제목이 {len(title)}자라 {PR_TITLE_MAX}자로 잘랐습니다.")
        title = truncate(title, PR_TITLE_MAX)

    for name in PR_SECTIONS:
        if not re.search(rf"(?m)^##\s*{re.escape(name)}\s*$", body):
            # 후처리: 빠진 섹션 헤더를 채워 넣는다
            body += f"\n\n## {name}\n- (내용을 직접 작성해 주세요)"
            warnings.append(f"'{name}' 섹션이 없어 빈 섹션을 추가했습니다.")
        elif not section_has_bullet(body, name):
            warnings.append(f"'{name}' 섹션에 불릿이 없습니다. 직접 보완해 주세요.")

    return title, body.strip(), warnings