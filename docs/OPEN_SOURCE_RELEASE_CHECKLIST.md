# Star Office UI — 오픈소스 공개 준비 체크리스트（준비만, 업로드 없음）

## 0. 현재 목표
- 본 문서는 "공개 전 준비"를 위한 것으로, 실제 업로드는 수행하지 않습니다.
- 모든 push 행위는 Haixin의 최종 명확한 승인이 필요합니다.

## 1. 개인정보 및 보안 검토 결과（현재 저장소）

### 고위험 파일 발견（반드시 제외）
- 실행 로그:
  - `cloudflared.out`
  - `cloudflared-named.out`
  - `cloudflared-quick.out`
  - `healthcheck.log`
  - `backend.log`
  - `backend/backend.out`
- 실행 상태:
  - `state.json`
  - `agents-state.json`
  - `backend/backend.pid`
- 백업/히스토리 파일:
  - `index.html.backup.*`
  - `index.html.original`
  - `*.backup*` 디렉터리 및 파일
- 로컬 가상 환경 및 캐시:
  - `.venv/`
  - `__pycache__/`

### 잠재적 민감 정보 발견
- 코드 내 절대 경로 `/root/...` 포함（상대 경로 또는 환경 변수로 변경 권장）
- 문서와 스크립트에 사설 도메인 `office.example.com` 포함（예시로 유지 가능하나, 플레이스홀더 도메인으로 변경 권장）

## 2. 필수 수정 사항（커밋 전）

### A. .gitignore（추가 필요）
추가 권장 항목:
```
*.log
*.out
*.pid
state.json
agents-state.json
join-keys.json
*.backup*
*.original
__pycache__/
.venv/
venv/
```

### B. README 저작권 고지（반드시 추가）
"아트 에셋 저작권 및 사용 제한" 섹션 추가:
- 코드는 오픈소스 라이선스（예: MIT）를 따름
- 아트 소재는 원작자/스튜디오 소유
- 소재는 학습/시연 용도만 허용, **상업적 이용 금지**

### C. 공개 디렉터리 정리
- 실행 로그, 실행 상태 파일, 백업 파일 정리
- "실행 가능한 최소 집합 + 필요한 에셋 + 문서"만 유지

## 3. 준비 중인 공개 패키지 권장 구조
```
star-office-ui/
  backend/
    app.py
    requirements.txt
    run.sh
  frontend/
    index.html
    game.js (필요 시)
    layout.js
    assets/* (공개 가능한 에셋만)
  office-agent-push.py
  set_state.py
  state.sample.json
  README.md
  LICENSE
  SKILL.md
  docs/
```

## 4. 공개 전 최종 확인（Haixin 확인용）
- [ ] 사설 도메인 예시（`office.example.com`）를 유지할지 여부
- [ ] 어떤 아트 리소스를 공개 허용할지（항목별 확인）
- [ ] README 비상업적 선언이 의도한 문구와 일치하는지
- [ ] 연동 스크립트를 별도 examples 디렉터리에 넣을지 여부

## 5. 현재 상태
- ✅ 문서 준비 완료（총괄 요약, 기능 설명, Skill v2, 공개 체크리스트）
- ⏳ "공개 에셋 범위 + 선언 문구 + 패키징 정리 스크립트 실행 여부" Haixin 확인 대기 중
- ⛔ GitHub 업로드 미실행
