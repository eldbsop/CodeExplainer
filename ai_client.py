import json
import os
import urllib.error
import urllib.request

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3.1-flash-lite"
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 1000


class AIError(Exception):
    """AI API 호출 중 발생한 오류"""


def get_api_key():
    """환경변수에서 API Key를 읽는다. 없으면 안내 메시지와 함께 오류를 낸다."""
    api_key = os.environ.get("AI_API_KEY")
    if not api_key:
        raise AIError(
            'AI_API_KEY 환경변수가 설정되지 않았습니다.\n'
            '## 예) export AI_API_KEY="YOUR_KEY"'
        )
    return api_key


def call_ai(system_prompt, user_prompt, model, temperature, max_tokens):
    """AI API를 1회 호출하고 생성된 텍스트를 돌려준다."""
    api_key = get_api_key()

    body = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            # 2.5 모델의 '생각' 기능이 토큰을 쓰지 않도록 끈다 (답변이 잘리는 것 방지)
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    request = urllib.request.Request(
        API_URL.format(model=model),
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        if e.code in (400, 403) and "API key" in detail:
            raise AIError("인증 실패: API Key가 올바른지 확인해 주세요.")
        if e.code == 404:
            raise AIError(f"모델을 찾을 수 없습니다(404): --model 이름을 확인해 주세요. ({model})")
        if e.code == 429:
            raise AIError("요청 한도 초과(429): 잠시 후 다시 시도해 주세요.")
        raise AIError(f"API 오류({e.code}): {detail}")
    except urllib.error.URLError as e:
        raise AIError(f"네트워크 오류: {e.reason}")
    except TimeoutError:
        raise AIError("응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")

    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError):
        raise AIError(f"예상하지 못한 응답 형식입니다(안전 필터에 걸렸을 수도 있어요): {data}")