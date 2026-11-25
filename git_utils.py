import subprocess


class GitError(Exception):
    """Git 명령 실행 중 발생한 오류"""


def run_git(args):
    """git 명령을 실행하고 결과 문자열을 돌려준다."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        raise GitError("git이 설치되어 있지 않습니다.")

    if result.returncode != 0:
        raise GitError(result.stderr.strip() or "git 명령 실행에 실패했습니다.")

    return result.stdout


def is_git_repo():
    """현재 폴더가 Git 저장소인지 확인한다."""
    try:
        run_git(["rev-parse", "--is-inside-work-tree"])
        return True
    except GitError:
        return False


def get_status():
    """git status 결과 (짧은 형식)를 돌려준다."""
    return run_git(["status", "--short"])


def get_diff():
    """git diff 결과를 돌려준다. (수정된 파일 + 스테이징된 파일 모두 포함)"""
    unstaged = run_git(["diff"])
    staged = run_git(["diff", "--cached"])
    return staged + unstaged


def get_current_branch():
    """현재 브랜치 이름을 돌려준다."""
    return run_git(["branch", "--show-current"]).strip()