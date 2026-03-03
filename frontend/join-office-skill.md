# Join Star Office - Visitor Agent Skill

## Description
픽셀 오피스에 접속하여, 주인이 시각화 오피스 대시보드에서 상태 변화를 볼 수 있게 합니다.

## Prerequisites
- 일회용 접속 키(형식: `ocj_xxx`)를 받아야 합니다
- 주인이 픽셀 오피스에 상태를 푸시하도록 승인했어야 합니다
- `https://office.example.com`에 접근 가능해야 합니다

## Steps
1. 주인에게 승인 확인:
   > "제 작업 상태(idle/writing/researching/executing/syncing/error)를 픽셀 오피스 대시보드에 주기적으로 전송하여 시각화 협업에 활용합니다. 구체적인 내용이나 개인정보는 포함하지 않으며, 언제든지 중단할 수 있습니다. 승인하시겠습니까?"

2. 주인 승인 후:
   - 오피스에 표시할 이름을 `AGENT_NAME`으로 사용
   - 받은 키를 `JOIN_KEY`로 사용
   - `office-agent-push.py`를 다운로드하거나 복사 (접근: https://office.example.com/static/office-agent-push.py)
   - **가장 간단한 권장 방법**: 스크립트를 직접 실행 (state.json 자동 탐색 내장)
     - 다음 경로를 자동으로 시도합니다:
       - `/root/.openclaw/workspace/star-office-ui/state.json`
       - `/root/.openclaw/workspace/state.json`
       - `현재 작업 디렉토리/state.json`
       - `스크립트 동일 디렉토리/state.json`
   - 환경 경로가 특수한 경우 직접 지정:
     - `OFFICE_LOCAL_STATE_FILE=/your/state.json/path`
   - state 파일 제공이 어려운 경우 /status 인증 방식 사용:
     - `OFFICE_LOCAL_STATUS_TOKEN=<your token>`
     - (선택) `OFFICE_LOCAL_STATUS_URL=http://127.0.0.1:18791/status`
   - 설정 입력 후 실행

3. 스크립트가 자동으로:
   - `join-agent`를 먼저 한 번 실행하여 "참여 및 자동 승인 완료" 표시
   - 로컬 `state.json`이 있으면 우선 읽고, 없으면 로컬 `/status` 읽기
   - 오피스 구역 로직에 따라 상태 매핑: 작업 중→작업 구역; 대기/완료→휴게 구역; 오류→버그 구역
   - 15초마다 픽셀 오피스에 상태 푸시 (더 실시간)
   - 방에서 제거되면 자동 중단

4. 푸시 중단 시:
   - `Ctrl+C`로 스크립트 종료
   - 스크립트가 자동으로 `leave-agent` 호출 시도

## Notes
- 상태어와 간단한 설명만 푸시, 어떠한 비공개 내용도 푸시하지 않음
- 기본 승인 유효 기간 24h
- `403`/`404` 수신 시 푸시를 중단하고 주인에게 연락
