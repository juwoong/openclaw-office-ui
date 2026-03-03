// Star Office UI - 레이아웃 및 레이어 설정
// 모든 좌표, depth, 리소스 경로를 여기서 통합 관리
// magic number 방지, 수정 오류 위험 감소

// 핵심 규칙:
// - 투명 리소스(예: 책상)는 강제 .png, 불투명 리소스는 .webp 우선
// - 레이어 순서: 낮음 → sofa(10) → starWorking(900) → desk(1000) → flower(1100)

const LAYOUT = {
  // === 게임 캔버스 ===
  game: {
    width: 1280,
    height: 720
  },

  // === 각 구역 좌표 ===
  areas: {
    door:        { x: 640, y: 550 },
    writing:     { x: 320, y: 360 },
    researching: { x: 320, y: 360 },
    error:       { x: 1066, y: 180 },
    breakroom:   { x: 640, y: 360 }
  },

  // === 장식 및 가구: 좌표 + 원점 + depth ===
  furniture: {
    // 소파
    sofa: {
      x: 670,
      y: 144,
      origin: { x: 0, y: 0 },
      depth: 10
    },

    // 새 책상 (투명 PNG 강제)
    desk: {
      x: 218,
      y: 417,
      origin: { x: 0.5, y: 0.5 },
      depth: 1000
    },

    // 책상 위 화분
    flower: {
      x: 310,
      y: 405,
      origin: { x: 0.5, y: 0.5 },
      depth: 1100
    },

    // Star가 책상 앞에서 작업 중 (desk 아래)
    starWorking: {
      x: 217,
      y: 333,
      origin: { x: 0.5, y: 0.5 },
      depth: 900,
      scale: 1.32
    },

    // 식물들
    plants: [
      { x: 565, y: 178, depth: 5 },
      { x: 230, y: 185, depth: 5 },
      { x: 977, y: 496, depth: 5 }
    ],

    // 포스터
    poster: {
      x: 252,
      y: 66,
      depth: 4
    },

    // 커피 머신
    coffeeMachine: {
      x: 659,
      y: 397,
      origin: { x: 0.5, y: 0.5 },
      depth: 99
    },

    // 서버실
    serverroom: {
      x: 1021,
      y: 142,
      origin: { x: 0.5, y: 0.5 },
      depth: 2
    },

    // 오류 버그
    errorBug: {
      x: 1007,
      y: 221,
      origin: { x: 0.5, y: 0.5 },
      depth: 50,
      scale: 0.9,
      pingPong: { leftX: 1007, rightX: 1111, speed: 0.6 }
    },

    // 동기화 애니메이션
    syncAnim: {
      x: 1157,
      y: 592,
      origin: { x: 0.5, y: 0.5 },
      depth: 40
    },

    // 고양이
    cat: {
      x: 94,
      y: 557,
      origin: { x: 0.5, y: 0.5 },
      depth: 2000
    }
  },

  // === 현판 ===
  plaque: {
    x: 640,
    y: 720 - 36,
    width: 420,
    height: 44
  },

  // === 리소스 로딩 규칙: PNG 강제 사용 항목 (투명 리소스) ===
  forcePng: {
    desk_v2: true // 새 책상은 반드시 투명, PNG 강제
  },

  // === 전체 리소스 수 (로딩 진행 바 용) ===
  totalAssets: 15
};
