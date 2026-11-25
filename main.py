import argparse
import sys

import git_utils


def collect_git_info():
    """Git 변경 사항을 수집해서 (status, diff)를 돌려준다. 변경이 없으면 종료한다."""
    if not git_utils.is_git_repo():
        print("[ERROR] Git 저장소가 아닙니다. 프로젝트 루트 디렉토리에서 실행해 주세요.")
        sys.exit(1)

    try:
        status = git_utils.get_status()
        diff = git_utils.get_diff()
    except git_utils.GitError as e:
        print(f"[ERROR] Git 명령 실행 실패: {e}")
        sys.exit(1)

    if not status.strip():
        print("[INFO] 변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 종료합니다.")
        sys.exit(0)

    changed_files = len(status.strip().splitlines())
    diff_lines = len(diff.splitlines())
    print(f"[INFO] Git status 수집 완료: {changed_files}개 파일 변경 감지")
    print(f"[INFO] Git diff 수집 완료: {diff_lines}줄")

    return status, diff


def cmd_commit(args):
    status, diff = collect_git_info()
    # 3단계에서 여기에 AI 호출을 붙일 예정
    print("[TODO] AI 호출은 다음 단계에서 구현합니다.")


def cmd_pr(args):
    status, diff = collect_git_info()
    branch = git_utils.get_current_branch()
    print(f"[INFO] 현재 브랜치: {branch}")
    # 4단계에서 여기에 PR 생성을 붙일 예정
    print("[TODO] AI 호출은 다음 단계에서 구현합니다.")


def build_parser():
    parser = argparse.ArgumentParser(description="AI 기반 커밋 메시지/PR 초안 생성기")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commit_parser = subparsers.add_parser("commit", help="커밋 메시지 생성")
    commit_parser.set_defaults(func=cmd_commit)

    pr_parser = subparsers.add_parser("pr", help="PR 제목/본문 생성")
    pr_parser.set_defaults(func=cmd_pr)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()