#!/usr/bin/env python3
"""Star Office UI - Backend State Service"""

from flask import Flask, jsonify, send_from_directory, make_response, request
from datetime import datetime, timedelta
import json
import logging
import os
import re
import secrets
import threading

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Paths (project-relative, no hardcoded absolute paths)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(os.path.dirname(ROOT_DIR), "memory")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
STATE_FILE = os.path.join(ROOT_DIR, "state.json")
AGENTS_STATE_FILE = os.path.join(ROOT_DIR, "agents-state.json")
JOIN_KEYS_FILE = os.path.join(ROOT_DIR, "join-keys.json")


def get_yesterday_date_str():
    """어제 날짜 문자열 YYYY-MM-DD를 반환합니다"""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")


def sanitize_content(text):
    """내용을 정리하고 개인정보를 보호합니다"""
    import re
    
    # OpenID, User ID 등 제거
    text = re.sub(r'ou_[a-f0-9]+', '[사용자]', text)
    text = re.sub(r'user_id="[^"]+"', 'user_id="[숨김]"', text)
    
    # 구체적인 이름 제거 (있는 경우)
    # 필요에 따라 더 많은 규칙 추가 가능
    
    # IP 주소, 경로 등 민감 정보 제거
    text = re.sub(r'/root/[^"\s]+', '[경로]', text)
    text = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '[IP]', text)
    
    # 전화번호, 이메일 등 제거
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[이메일]', text)
    text = re.sub(r'1[3-9]\d{9}', '[휴대폰 번호]', text)
    
    return text


def extract_memo_from_file(file_path):
    """memory 파일에서 표시에 적합한 memo 내용을 추출합니다 (지혜로운 스타일의 요약)"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 실제 내용 추출, 과도한 포장 없음
        lines = content.strip().split("\n")
        
        # 핵심 요점 추출
        core_points = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            if line.startswith("- "):
                core_points.append(line[2:].strip())
            elif len(line) > 10:
                core_points.append(line)
        
        if not core_points:
            return "「어제 기록 없음」\n\n뜻이 있으면 밤늦게 자고 새벽 일찍 일어나는 수고도 마다하지 않으리; 가장 무익한 것은 하루 열심히 하고 열흘을 게으름 피우는 것이다."
        
        # 핵심 내용에서 2-3개 핵심 포인트 추출
        selected_points = core_points[:3]
        
        # 지혜 어록 모음
        wisdom_quotes = [
            "「일을 잘 하려면, 먼저 도구를 갖춰야 한다.」",
            "「작은 발걸음이 쌓이지 않으면 천 리에 이를 수 없고, 작은 물줄기가 모이지 않으면 강과 바다를 이룰 수 없다.」",
            "「앎과 행동이 하나가 될 때, 비로소 멀리 나아갈 수 있다.」",
            "「학업은 부지런함에서 정밀해지고, 놀이에서 황폐해진다; 행동은 사려에서 이루어지고, 무심함에서 무너진다.」",
            "「길은 멀고 험하지만, 나는 위아래로 탐구할 것이다.」",
            "「어젯밤 서풍이 푸른 나무를 시들게 하고, 홀로 높은 누각에 올라, 하늘 끝 길을 바라본다.」",
            "「옷자락이 점점 넓어져도 후회하지 않으니, 그대를 위해 초췌해져도 괜찮다.」",
            "「군중 속에서 수백 번 그를 찾았는데, 문득 뒤돌아보니, 그 사람은 불빛이 드문 곳에 있었다.」",
            "「세상사를 꿰뚫어 보는 것이 모두 학문이요, 인정에 통달하는 것이 바로 문장이다.」",
            "「책에서 얻은 것은 결국 얕고, 이 일을 참으로 알려면 몸소 행해야 한다.」"
        ]
        
        import random
        quote = random.choice(wisdom_quotes)
        
        # 내용 조합
        result = []
        
        # 핵심 내용 추가
        if selected_points:
            for i, point in enumerate(selected_points):
                # 개인정보 정리
                point = sanitize_content(point)
                # 너무 긴 내용 잘라내기
                if len(point) > 40:
                    point = point[:37] + "..."
                # 행당 최대 20자
                if len(point) <= 20:
                    result.append(f"· {point}")
                else:
                    # 20자 단위로 분할
                    for j in range(0, len(point), 20):
                        chunk = point[j:j+20]
                        if j == 0:
                            result.append(f"· {chunk}")
                        else:
                            result.append(f"  {chunk}")
        
        # 지혜 어록 추가
        if quote:
            if len(quote) <= 20:
                result.append(f"\n{quote}")
            else:
                for j in range(0, len(quote), 20):
                    chunk = quote[j:j+20]
                    if j == 0:
                        result.append(f"\n{chunk}")
                    else:
                        result.append(chunk)
        
        return "\n".join(result).strip()
        
    except Exception as e:
        print(f"memo 추출 실패: {e}")
        return "「어제 기록 불러오기 실패」\n\n「지난 일은 되돌릴 수 없지만, 앞으로 올 일은 아직 쫓을 수 있다.」"

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="/static")

# Rate limiter
limiter = Limiter(get_remote_address, app=app, default_limits=[])

# Admin token for protected endpoints
OFFICE_ADMIN_TOKEN = os.environ.get("OFFICE_ADMIN_TOKEN", "")
if not OFFICE_ADMIN_TOKEN:
    logging.warning("OFFICE_ADMIN_TOKEN is not set. Protected endpoints will reject all requests.")


def require_admin_token():
    """Validate Authorization: Bearer <token> header against OFFICE_ADMIN_TOKEN.

    Returns a 401 response tuple on failure, or None on success.
    """
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[len("Bearer "):] if auth_header.startswith("Bearer ") else ""
    if not OFFICE_ADMIN_TOKEN or not secrets.compare_digest(token, OFFICE_ADMIN_TOKEN):
        return jsonify({"ok": False, "msg": "Unauthorized"}), 401
    return None

# Guard join-agent critical section to enforce per-key concurrency under parallel requests
join_lock = threading.Lock()

# Generate a version timestamp once at server startup for cache busting
VERSION_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


@app.after_request
def add_no_cache_headers(response):
    """Aggressively prevent caching for all responses"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Default state
DEFAULT_STATE = {
    "state": "idle",
    "detail": "대기 중...",
    "progress": 0,
    "updated_at": datetime.now().isoformat()
}


def load_state():
    """Load state from file.

    Includes a simple auto-idle mechanism:
    - If the last update is older than ttl_seconds (default 25s)
      and the state is a "working" state, we fall back to idle.

    This avoids the UI getting stuck at the desk when no new updates arrive.
    """
    state = None
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = None

    if not isinstance(state, dict):
        state = dict(DEFAULT_STATE)

    # Auto-idle
    try:
        ttl = int(state.get("ttl_seconds", 300))
        updated_at = state.get("updated_at")
        s = state.get("state", "idle")
        working_states = {"writing", "researching", "executing"}
        if updated_at and s in working_states:
            # tolerate both with/without timezone
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            # Use UTC for aware datetimes; local time for naive.
            if dt.tzinfo:
                from datetime import timezone
                age = (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
            else:
                age = (datetime.now() - dt).total_seconds()
            if age > ttl:
                state["state"] = "idle"
                state["detail"] = "대기 중 (자동으로 휴식 구역으로 이동)"
                state["progress"] = 0
                state["updated_at"] = datetime.now().isoformat()
                # persist the auto-idle so every client sees it consistently
                try:
                    save_state(state)
                except Exception:
                    pass
    except Exception:
        pass

    return state


def save_state(state: dict):
    """Save state to file"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# Initialize state
if not os.path.exists(STATE_FILE):
    save_state(DEFAULT_STATE)


@app.route("/", methods=["GET"])
def index():
    """Serve the pixel office UI with built-in version cache busting"""
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("{{VERSION_TIMESTAMP}}", VERSION_TIMESTAMP)
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


@app.route("/join", methods=["GET"])
def join_page():
    """Serve the agent join page"""
    with open(os.path.join(FRONTEND_DIR, "join.html"), "r", encoding="utf-8") as f:
        html = f.read()
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


@app.route("/invite", methods=["GET"])
def invite_page():
    """Serve human-facing invite instruction page"""
    with open(os.path.join(FRONTEND_DIR, "invite.html"), "r", encoding="utf-8") as f:
        html = f.read()
    resp = make_response(html)
    resp.headers["Content-Type"] = "text/html; charset=utf-8"
    return resp


DEFAULT_AGENTS = [
    {
        "agentId": "star",
        "name": "Star",
        "isMain": True,
        "state": "idle",
        "detail": "대기 중, 언제든지 준비됩니다",
        "updated_at": datetime.now().isoformat(),
        "area": "breakroom",
        "source": "local",
        "joinKey": None,
        "authStatus": "approved",
        "authExpiresAt": None,
        "lastPushAt": None
    },
    {
        "agentId": "npc1",
        "name": "NPC 1",
        "isMain": False,
        "state": "writing",
        "detail": "트렌드 일보 정리 중...",
        "updated_at": datetime.now().isoformat(),
        "area": "writing",
        "source": "demo",
        "joinKey": None,
        "authStatus": "approved",
        "authExpiresAt": None,
        "lastPushAt": None
    }
]


def load_agents_state():
    if os.path.exists(AGENTS_STATE_FILE):
        try:
            with open(AGENTS_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return list(DEFAULT_AGENTS)


def save_agents_state(agents):
    with open(AGENTS_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(agents, f, ensure_ascii=False, indent=2)


def load_join_keys():
    if os.path.exists(JOIN_KEYS_FILE):
        try:
            with open(JOIN_KEYS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and isinstance(data.get("keys"), list):
                    return data
        except Exception:
            pass
    return {"keys": []}


def save_join_keys(data):
    with open(JOIN_KEYS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_agent_state(s):
    """상태를 정규화하여 호환성을 높입니다.
    호환 입력: working/busy → writing; run/running → executing; sync → syncing; research → researching.
    인식되지 않으면 기본적으로 idle을 반환합니다.
    """
    if not s:
        return 'idle'
    s_lower = s.lower().strip()
    if s_lower in {'working', 'busy', 'write'}:
        return 'writing'
    if s_lower in {'run', 'running', 'execute', 'exec'}:
        return 'executing'
    if s_lower in {'sync'}:
        return 'syncing'
    if s_lower in {'research', 'search'}:
        return 'researching'
    if s_lower in {'idle', 'writing', 'researching', 'executing', 'syncing', 'error'}:
        return s_lower
    # 기본 fallback
    return 'idle'


def state_to_area(state):
    area_map = {
        "idle": "breakroom",
        "writing": "writing",
        "researching": "writing",
        "executing": "writing",
        "syncing": "writing",
        "error": "error"
    }
    return area_map.get(state, "breakroom")


# Ensure files exist
if not os.path.exists(AGENTS_STATE_FILE):
    save_agents_state(DEFAULT_AGENTS)
if not os.path.exists(JOIN_KEYS_FILE):
    save_join_keys({"keys": []})


@app.route("/agents", methods=["GET"])
def get_agents():
    """Get full agents list (for multi-agent UI), with auto-cleanup on access"""
    agents = load_agents_state()
    now = datetime.now()

    cleaned_agents = []
    keys_data = load_join_keys()

    for a in agents:
        if a.get("isMain"):
            cleaned_agents.append(a)
            continue

        auth_expires_at_str = a.get("authExpiresAt")
        auth_status = a.get("authStatus", "pending")

        # 1) 승인 초과 시 자동 leave
        if auth_status == "pending" and auth_expires_at_str:
            try:
                auth_expires_at = datetime.fromisoformat(auth_expires_at_str)
                if now > auth_expires_at:
                    key = a.get("joinKey")
                    if key:
                        key_item = next((k for k in keys_data.get("keys", []) if k.get("key") == key), None)
                        if key_item:
                            key_item["used"] = False
                            key_item["usedBy"] = None
                            key_item["usedByAgentId"] = None
                            key_item["usedAt"] = None
                    continue
            except Exception:
                pass

        # 2) 푸시 없이 초과 시 자동 오프라인 (5분 초과)
        last_push_at_str = a.get("lastPushAt")
        if auth_status == "approved" and last_push_at_str:
            try:
                last_push_at = datetime.fromisoformat(last_push_at_str)
                age = (now - last_push_at).total_seconds()
                if age > 300:  # 5분간 푸시 없으면 자동 오프라인
                    a["authStatus"] = "offline"
            except Exception:
                pass

        cleaned_agents.append(a)

    save_agents_state(cleaned_agents)
    save_join_keys(keys_data)

    return jsonify(cleaned_agents)


@app.route("/agent-approve", methods=["POST"])
def agent_approve():
    """Approve an agent (set authStatus to approved)"""
    err = require_admin_token()
    if err:
        return err
    try:
        data = request.get_json()
        agent_id = (data.get("agentId") or "").strip()
        if not agent_id:
            return jsonify({"ok": False, "msg": "agentId가 누락되었습니다"}), 400

        agents = load_agents_state()
        target = next((a for a in agents if a.get("agentId") == agent_id and not a.get("isMain")), None)
        if not target:
            return jsonify({"ok": False, "msg": "에이전트를 찾을 수 없습니다"}), 404

        target["authStatus"] = "approved"
        target["authApprovedAt"] = datetime.now().isoformat()
        target["authExpiresAt"] = (datetime.now() + timedelta(hours=24)).isoformat()  # 기본 승인 24시간

        save_agents_state(agents)
        return jsonify({"ok": True, "agentId": agent_id, "authStatus": "approved"})
    except Exception as e:
        logging.exception("agent-approve error")
        return jsonify({"ok": False, "msg": "내부 서버 오류가 발생했습니다."}), 500


@app.route("/agent-reject", methods=["POST"])
def agent_reject():
    """Reject an agent (set authStatus to rejected and optionally revoke key)"""
    err = require_admin_token()
    if err:
        return err
    try:
        data = request.get_json()
        agent_id = (data.get("agentId") or "").strip()
        if not agent_id:
            return jsonify({"ok": False, "msg": "agentId가 누락되었습니다"}), 400

        agents = load_agents_state()
        target = next((a for a in agents if a.get("agentId") == agent_id and not a.get("isMain")), None)
        if not target:
            return jsonify({"ok": False, "msg": "에이전트를 찾을 수 없습니다"}), 404

        target["authStatus"] = "rejected"
        target["authRejectedAt"] = datetime.now().isoformat()

        # Optionally free join key back to unused
        join_key = target.get("joinKey")
        keys_data = load_join_keys()
        if join_key:
            key_item = next((k for k in keys_data.get("keys", []) if k.get("key") == join_key), None)
            if key_item:
                key_item["used"] = False
                key_item["usedBy"] = None
                key_item["usedByAgentId"] = None
                key_item["usedAt"] = None

        # Remove from agents list
        agents = [a for a in agents if a.get("agentId") != agent_id or a.get("isMain")]

        save_agents_state(agents)
        save_join_keys(keys_data)
        return jsonify({"ok": True, "agentId": agent_id, "authStatus": "rejected"})
    except Exception as e:
        logging.exception("agent-reject error")
        return jsonify({"ok": False, "msg": "내부 서버 오류가 발생했습니다."}), 500


@app.route("/join-agent", methods=["POST"])
@limiter.limit("60 per minute")
def join_agent():
    """Add a new agent with one-time join key validation and pending auth"""
    try:
        data = request.get_json()
        if not isinstance(data, dict) or not data.get("name"):
            return jsonify({"ok": False, "msg": "이름을 입력해주세요"}), 400

        name = data["name"].strip()
        state = data.get("state", "idle")
        detail = data.get("detail", "")
        join_key = data.get("joinKey", "").strip()

        # Normalize state early for compatibility
        state = normalize_agent_state(state)

        if not join_key:
            return jsonify({"ok": False, "msg": "접속 키를 입력해주세요"}), 400

        keys_data = load_join_keys()
        key_item = next((k for k in keys_data.get("keys", []) if k.get("key") == join_key), None)
        if not key_item:
            return jsonify({"ok": False, "msg": "접속 키가 유효하지 않습니다"}), 403
        # key 재사용 가능: used=true라도 거부하지 않음

        with join_lock:
            # 잠금 내에서 재읽기, 동시 요청이 동일한 오래된 스냅샷 기반으로 검증 통과하는 것 방지
            keys_data = load_join_keys()
            key_item = next((k for k in keys_data.get("keys", []) if k.get("key") == join_key), None)
            if not key_item:
                return jsonify({"ok": False, "msg": "접속 키가 유효하지 않습니다"}), 403

            agents = load_agents_state()

            # 동시접속 한도: 동일 key "동시 온라인" 최대 3개.
            # 온라인 판정: lastPushAt/updated_at 이 5분 이내; 그렇지 않으면 오프라인으로 간주, 동시접속에 미포함.
            now = datetime.now()
            existing = next((a for a in agents if a.get("name") == name and not a.get("isMain")), None)
            existing_id = existing.get("agentId") if existing else None

            def _age_seconds(dt_str):
                if not dt_str:
                    return None
                try:
                    dt = datetime.fromisoformat(dt_str)
                    return (now - dt).total_seconds()
                except Exception:
                    return None

            # opportunistic offline marking
            for a in agents:
                if a.get("isMain"):
                    continue
                if a.get("authStatus") != "approved":
                    continue
                age = _age_seconds(a.get("lastPushAt"))
                if age is None:
                    age = _age_seconds(a.get("updated_at"))
                if age is not None and age > 300:
                    a["authStatus"] = "offline"

            max_concurrent = int(key_item.get("maxConcurrent", 3))
            active_count = 0
            for a in agents:
                if a.get("isMain"):
                    continue
                if a.get("agentId") == existing_id:
                    continue
                if a.get("joinKey") != join_key:
                    continue
                if a.get("authStatus") != "approved":
                    continue
                age = _age_seconds(a.get("lastPushAt"))
                if age is None:
                    age = _age_seconds(a.get("updated_at"))
                if age is None or age <= 300:
                    active_count += 1

            if active_count >= max_concurrent:
                save_agents_state(agents)
                return jsonify({"ok": False, "msg": f"해당 접속 키의 동시 접속 한도({max_concurrent})에 도달했습니다. 잠시 후 다시 시도하거나 다른 키를 사용해주세요"}), 429

            if existing:
                existing["state"] = state
                existing["detail"] = detail
                existing["updated_at"] = datetime.now().isoformat()
                existing["area"] = state_to_area(state)
                existing["source"] = "remote-openclaw"
                existing["joinKey"] = join_key
                existing["authStatus"] = "approved"
                existing["authApprovedAt"] = datetime.now().isoformat()
                existing["authExpiresAt"] = (datetime.now() + timedelta(hours=24)).isoformat()
                existing["lastPushAt"] = datetime.now().isoformat()  # join을 온라인 진입으로 간주, 동시접속/오프라인 판정에 포함
                if not existing.get("avatar"):
                    import random
                    existing["avatar"] = random.choice(["guest_role_1", "guest_role_2", "guest_role_3", "guest_role_4", "guest_role_5", "guest_role_6"])
                agent_id = existing.get("agentId")
            else:
                # Use ms + random suffix to avoid collisions under concurrent joins
                import random
                import string
                agent_id = "agent_" + str(int(datetime.now().timestamp() * 1000)) + "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
                agents.append({
                    "agentId": agent_id,
                    "name": name,
                    "isMain": False,
                    "state": state,
                    "detail": detail,
                    "updated_at": datetime.now().isoformat(),
                    "area": state_to_area(state),
                    "source": "remote-openclaw",
                    "joinKey": join_key,
                    "authStatus": "approved",
                    "authApprovedAt": datetime.now().isoformat(),
                    "authExpiresAt": (datetime.now() + timedelta(hours=24)).isoformat(),
                    "lastPushAt": datetime.now().isoformat(),
                    "avatar": random.choice(["guest_role_1", "guest_role_2", "guest_role_3", "guest_role_4", "guest_role_5", "guest_role_6"])
                })

            key_item["used"] = True
            key_item["usedBy"] = name
            key_item["usedByAgentId"] = agent_id
            key_item["usedAt"] = datetime.now().isoformat()
            key_item["reusable"] = True

            # 유효한 key를 받으면 즉시 승인, 더 이상 주인의 수동 클릭을 기다리지 않음
            # (상태는 위 existing/new 분기에서 이미 저장됨)
            save_agents_state(agents)
            save_join_keys(keys_data)

        return jsonify({"ok": True, "agentId": agent_id, "authStatus": "approved", "nextStep": "자동 승인되었습니다. 즉시 상태 전송을 시작하세요"})
    except Exception as e:
        logging.exception("join-agent error")
        return jsonify({"ok": False, "msg": "내부 서버 오류가 발생했습니다."}), 500


@app.route("/leave-agent", methods=["POST"])
def leave_agent():
    """Remove an agent and free its one-time join key for reuse (optional)

    Prefer agentId (stable). Name is accepted for backward compatibility.
    """
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"ok": False, "msg": "invalid json"}), 400

        agent_id = (data.get("agentId") or "").strip()
        name = (data.get("name") or "").strip()
        if not agent_id and not name:
            return jsonify({"ok": False, "msg": "agentId 또는 이름을 입력해주세요"}), 400

        agents = load_agents_state()

        target = None
        if agent_id:
            target = next((a for a in agents if a.get("agentId") == agent_id and not a.get("isMain")), None)
        if (not target) and name:
            # fallback: remove by name only if agentId not provided
            target = next((a for a in agents if a.get("name") == name and not a.get("isMain")), None)

        if not target:
            return jsonify({"ok": False, "msg": "퇴장할 에이전트를 찾을 수 없습니다"}), 404

        join_key = target.get("joinKey")
        new_agents = [a for a in agents if a.get("isMain") or a.get("agentId") != target.get("agentId")]

        # Optional: free key back to unused after leave
        keys_data = load_join_keys()
        if join_key:
            key_item = next((k for k in keys_data.get("keys", []) if k.get("key") == join_key), None)
            if key_item:
                key_item["used"] = False
                key_item["usedBy"] = None
                key_item["usedByAgentId"] = None
                key_item["usedAt"] = None

        save_agents_state(new_agents)
        save_join_keys(keys_data)
        return jsonify({"ok": True})
    except Exception as e:
        logging.exception("leave-agent error")
        return jsonify({"ok": False, "msg": "내부 서버 오류가 발생했습니다."}), 500


@app.route("/status", methods=["GET"])
def get_status():
    """Get current main state (backward compatibility)"""
    state = load_state()
    return jsonify(state)


@app.route("/agent-push", methods=["POST"])
@limiter.limit("60 per minute")
def agent_push():
    """Remote openclaw actively pushes status to office.

    Required fields:
    - agentId
    - joinKey
    - state
    Optional:
    - detail
    - name
    """
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"ok": False, "msg": "invalid json"}), 400

        agent_id = (data.get("agentId") or "").strip()
        join_key = (data.get("joinKey") or "").strip()
        state = (data.get("state") or "").strip()
        detail = (data.get("detail") or "").strip()
        name = (data.get("name") or "").strip()

        if not agent_id or not join_key or not state:
            return jsonify({"ok": False, "msg": "agentId/joinKey/state가 누락되었습니다"}), 400

        valid_states = {"idle", "writing", "researching", "executing", "syncing", "error"}
        state = normalize_agent_state(state)

        keys_data = load_join_keys()
        key_item = next((k for k in keys_data.get("keys", []) if k.get("key") == join_key), None)
        if not key_item:
            return jsonify({"ok": False, "msg": "joinKey가 유효하지 않습니다"}), 403
        # key 재사용 가능: used/usedByAgentId 바인딩 검증 더 이상 수행하지 않음


        agents = load_agents_state()
        target = next((a for a in agents if a.get("agentId") == agent_id and not a.get("isMain")), None)
        if not target:
            return jsonify({"ok": False, "msg": "에이전트가 등록되지 않았습니다. 먼저 join을 진행해주세요"}), 404

        # Auth check: only approved agents can push.
        # Note: "offline" is a presence state (stale), not a revoked authorization.
        # Allow offline agents to resume pushing and auto-promote them back to approved.
        auth_status = target.get("authStatus", "pending")
        if auth_status not in {"approved", "offline"}:
            return jsonify({"ok": False, "msg": "에이전트가 승인되지 않았습니다. 주인의 승인을 기다려주세요"}), 403
        if auth_status == "offline":
            target["authStatus"] = "approved"
            target["authApprovedAt"] = datetime.now().isoformat()
            target["authExpiresAt"] = (datetime.now() + timedelta(hours=24)).isoformat()

        if target.get("joinKey") != join_key:
            return jsonify({"ok": False, "msg": "joinKey가 일치하지 않습니다"}), 403

        target["state"] = state
        target["detail"] = detail
        if name:
            target["name"] = name
        target["updated_at"] = datetime.now().isoformat()
        target["area"] = state_to_area(state)
        target["source"] = "remote-openclaw"
        target["lastPushAt"] = datetime.now().isoformat()

        save_agents_state(agents)
        return jsonify({"ok": True, "agentId": agent_id, "area": target.get("area")})
    except Exception as e:
        logging.exception("agent-push error")
        return jsonify({"ok": False, "msg": "내부 서버 오류가 발생했습니다."}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/yesterday-memo", methods=["GET"])
def get_yesterday_memo():
    """어제 일지를 가져옵니다"""
    try:
        # 어제 파일 먼저 탐색
        yesterday_str = get_yesterday_date_str()
        yesterday_file = os.path.join(MEMORY_DIR, f"{yesterday_str}.md")
        
        target_file = None
        target_date = yesterday_str
        
        if os.path.exists(yesterday_file):
            target_file = yesterday_file
        else:
            # 어제 파일이 없으면, 가장 최근 날짜 탐색
            if os.path.exists(MEMORY_DIR):
                files = [f for f in os.listdir(MEMORY_DIR) if f.endswith(".md") and re.match(r"\d{4}-\d{2}-\d{2}\.md", f)]
                if files:
                    files.sort(reverse=True)
                    # 오늘 것은 건너뜀 (있는 경우)
                    today_str = datetime.now().strftime("%Y-%m-%d")
                    for f in files:
                        if f != f"{today_str}.md":
                            target_file = os.path.join(MEMORY_DIR, f)
                            target_date = f.replace(".md", "")
                            break
        
        if target_file and os.path.exists(target_file):
            memo_content = extract_memo_from_file(target_file)
            return jsonify({
                "success": True,
                "date": target_date,
                "memo": memo_content
            })
        else:
            return jsonify({
                "success": False,
                "msg": "어제 일지를 찾을 수 없습니다"
            })
    except Exception as e:
        logging.exception("yesterday-memo error")
        return jsonify({
            "success": False,
            "msg": "내부 서버 오류가 발생했습니다."
        }), 500


@app.route("/set_state", methods=["POST"])
def set_state_endpoint():
    """Set state via POST (for UI control panel)"""
    err = require_admin_token()
    if err:
        return err
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"status": "error", "msg": "invalid json"}), 400
        state = load_state()
        if "state" in data:
            s = data["state"]
            valid_states = {"idle", "writing", "researching", "executing", "syncing", "error"}
            if s in valid_states:
                state["state"] = s
        if "detail" in data:
            state["detail"] = data["detail"]
        state["updated_at"] = datetime.now().isoformat()
        save_state(state)
        return jsonify({"status": "ok"})
    except Exception as e:
        logging.exception("set_state error")
        return jsonify({"status": "error", "msg": "내부 서버 오류가 발생했습니다."}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("Star Office UI - Backend State Service")
    print("=" * 50)
    print(f"State file: {STATE_FILE}")
    print("Listening on: http://0.0.0.0:18791")
    print("=" * 50)
    
    app.run(host="0.0.0.0", port=18791, debug=False)
