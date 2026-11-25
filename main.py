import argparse
import sys

import ai_client
import formatter
import git_utils
import prompts
import safety


def collect_git_info(args):
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

    if args.safe_mode:
        diff, masked, truncated = safety.apply_safe_mode(diff)
        print(f"[INFO] safe-mode 적용: 민감정보 {masked}건 마스킹"
              + (", diff 일부만 전송(분량 제한)" if truncated else ""))

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


def print_warnings(warnings):
    for w in warnings:
        print(f"[WARN] {w}")


def cmd_commit(args):
    status, diff = collect_git_info(args)

    raw = request_ai(
        args,
        prompts.COMMIT_SYSTEM_PROMPT,
        prompts.build_commit_user_prompt(status, diff),
    )
    message, warnings = formatter.format_commit(raw)
    if not message:
        print("[ERROR] AI가 빈 응답을 돌려줬습니다. 다시 실행해 주세요.")
        sys.exit(1)

    print("[DONE] 커밋 메시지 생성 완료")
    print_warnings(warnings)
    print()
    print("--- Commit Message ---")
    print(message)
    print("----------------------")
    print("[INFO] 생성된 메시지는 초안입니다. 검토 후 적용해 주세요.")


def cmd_pr(args):
    status, diff = collect_git_info(args)
    branch = git_utils.get_current_branch()
    print(f"[INFO] 현재 브랜치: {branch}")

    raw = request_ai(
        args,
        prompts.PR_SYSTEM_PROMPT,
        prompts.build_pr_user_prompt(branch, status, diff),
    )
    title, body, warnings = formatter.format_pr(raw)
    if not title:
        print("[ERROR] AI가 빈 응답을 돌려줬습니다. 다시 실행해 주세요.")
        sys.exit(1)

    print("[DONE] PR 초안 생성 완료")
    print_warnings(warnings)
    print()
    print("--- PR Title ---")
    print(title)
    print()
    print("--- PR Body ---")
    print(body)
    print("----------------")
    print("[INFO] 생성된 PR 초안은 참고용입니다. 검토 후 적용해 주세요.")


def add_common_options(parser):
    """commit/pr 명령이 공통으로 쓰는 옵션을 추가한다."""
    parser.add_argument("--model", default=ai_client.DEFAULT_MODEL,
                        help=f"사용할 모델 (기본값: {ai_client.DEFAULT_MODEL})")
    parser.add_argument("--temperature", type=float, default=ai_client.DEFAULT_TEMPERATURE,
                        help=f"창의성 0~1 (기본값: {ai_client.DEFAULT_TEMPERATURE})")
    parser.add_argument("--max-tokens", type=int, default=ai_client.DEFAULT_MAX_TOKENS,
                        help=f"최대 응답 토큰 수 (기본값: {ai_client.DEFAULT_MAX_TOKENS})")
    parser.add_argument("--safe-mode", action="store_true",
                        help="민감정보 마스킹 + diff 분량 제한(최대 10개 파일, 200줄) 후 전송")


def build_parser():
    parser = argparse.ArgumentParser(description="AI 기반 커밋 메시지/PR 초안 생성기")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commit_parser = subparsers.add_parser("commit", help="커밋 메시지 생성")
    add_common_options(commit_parser)
    commit_parser.set_defaults(func=cmd_commit)

    pr_parser = subparsers.add_parser("pr", help="PR 제목/본문 생성")
    add_common_options(pr_parser)
    pr_parser.set_defaults(func=cmd_pr)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()