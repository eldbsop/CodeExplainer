import argparse
import sys

import ai_client
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


def request_ai(args, system_prompt, user_prompt):
    """AI API를 1회 호출한다. 실패하면 오류 메시지를 출력하고 종료한다."""
    print("[INFO] AI API 요청 중... (호출 횟수: 1회)")
    try:
        return ai_client.call_ai(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
    except ai_client.AIError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_commit(args):
    status, diff = collect_git_info()

    # 임시 프롬프트: 4단계에서 제대로 설계할 예정
    system_prompt = "너는 Git 커밋 메시지를 작성하는 도우미야."
    user_prompt = f"아래 변경 사항에 대한 커밋 메시지를 한국어로 작성해줘.\n\n{diff}"

    result = request_ai(args, system_prompt, user_prompt)
    print("[DONE] 생성 완료")
    print("--- Commit Message ---")
    print(result)
    print("----------------------")


def cmd_pr(args):
    status, diff = collect_git_info()
    branch = git_utils.get_current_branch()
    print(f"[INFO] 현재 브랜치: {branch}")
    # 4단계에서 PR 생성을 붙일 예정
    print("[TODO] PR 생성은 다음 단계에서 구현합니다.")


def add_ai_options(parser):
    """commit/pr 명령이 공통으로 쓰는 AI 파라미터 옵션을 추가한다."""
    parser.add_argument("--model", default=ai_client.DEFAULT_MODEL,
                        help=f"사용할 모델 (기본값: {ai_client.DEFAULT_MODEL})")
    parser.add_argument("--temperature", type=float, default=ai_client.DEFAULT_TEMPERATURE,
                        help=f"창의성 0~1 (기본값: {ai_client.DEFAULT_TEMPERATURE})")
    parser.add_argument("--max-tokens", type=int, default=ai_client.DEFAULT_MAX_TOKENS,
                        help=f"최대 응답 토큰 수 (기본값: {ai_client.DEFAULT_MAX_TOKENS})")


def build_parser():
    parser = argparse.ArgumentParser(description="AI 기반 커밋 메시지/PR 초안 생성기")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commit_parser = subparsers.add_parser("commit", help="커밋 메시지 생성")
    add_ai_options(commit_parser)
    commit_parser.set_defaults(func=cmd_commit)

    pr_parser = subparsers.add_parser("pr", help="PR 제목/본문 생성")
    add_ai_options(pr_parser)
    pr_parser.set_defaults(func=cmd_pr)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()