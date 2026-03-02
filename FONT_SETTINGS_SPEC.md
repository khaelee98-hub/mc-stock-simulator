# 폰트/크기 설정 기능 명세서

## 1. 기능 개요

GUI의 폰트 패밀리와 전체 크기 스케일을 사용자가 설정할 수 있는 기능이다. 설정 다이얼로그를 통해 글꼴을 선택하고 크기를 조절하면 UI 전체에 즉시 반영되며, JSON 파일로 설정이 영속화되어 프로그램 재시작 후에도 유지된다.

### 주요 기능

- 일반 글꼴 선택 (시스템에서 사용 가능한 폰트 목록 제공)
- 고정폭 글꼴 선택 (코드/통계 표시용)
- 글꼴 크기 스케일 조절 (80%~150%, 5% 단위)
- 실시간 미리보기
- config.json으로 설정 영속화

---

## 2. config.json 스키마

```json
{
  "font_family": "Malgun Gothic",
  "mono_font": "Consolas",
  "font_scale": 100
}
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `font_family` | string | 플랫폼별 자동감지 | UI 일반 글꼴 |
| `mono_font` | string | `"Consolas"` | 고정폭 글꼴 (통계, 자동완성 등) |
| `font_scale` | int | `100` | 글꼴 크기 배율 (80~150%) |

### 플랫폼별 기본 글꼴

| 플랫폼 | 기본 font_family |
|--------|------------------|
| Windows | Malgun Gothic |
| macOS | Apple SD Gothic Neo |
| Linux | Noto Sans KR |

### 유효성 검증

- `font_scale`은 80~150 범위로 클램핑
- config.json이 없거나 파싱 실패 시 기본값 사용
- 누락된 키는 기본값으로 보완

---

## 3. 설정 다이얼로그 UI 명세

### 레이아웃

```
+----------------------------------+
|  설정                       [x]  |
+----------------------------------+
|  글꼴 설정                        |
|                                  |
|  글꼴:                            |
|  [Malgun Gothic           v]     |
|                                  |
|  고정폭 글꼴:                      |
|  [Consolas                v]     |
|                                  |
|  글꼴 크기:                        |
|  |--------o-----------| 100%     |
|                                  |
|  +----------------------------+  |
|  | 미리보기: 가나다 ABC 123     |  |
|  +----------------------------+  |
|                                  |
|               [취소]  [적용]      |
+----------------------------------+
```

### 위젯 상세

| 위젯 | 타입 | 설명 |
|------|------|------|
| 글꼴 ComboBox | `CTkComboBox` (readonly) | 시스템 폰트 중 후보 목록과 교차한 사용 가능 폰트 표시 |
| 고정폭 글꼴 ComboBox | `CTkComboBox` (readonly) | 고정폭 폰트 후보 목록 |
| 크기 슬라이더 | `CTkSlider` | 80~150%, 14스텝 (5% 단위), 실시간 퍼센트 라벨 |
| 미리보기 라벨 | `CTkLabel` | 폰트/크기 변경 시 실시간 반영 |
| 적용 버튼 | `CTkButton` | 설정 저장 + 폰트 갱신 + UI 리빌드 |
| 취소 버튼 | `CTkButton` | 다이얼로그 닫기 (변경 없음) |

### 글꼴 후보 목록

**일반 글꼴:**
Malgun Gothic, 맑은 고딕, Apple SD Gothic Neo, Noto Sans KR, NanumGothic, 나눔고딕, Segoe UI, Arial, Helvetica, Verdana, Tahoma, Roboto

**고정폭 글꼴:**
Consolas, Cascadia Code, JetBrains Mono, D2Coding, Courier New, Menlo, Monaco, Source Code Pro, Fira Code

### 다이얼로그 동작

- `CTkToplevel` + `transient()` + `grab_set()` (모달)
- 메인 윈도우 중앙에 위치
- 420x400 고정 크기
- 현재 config 값을 초기값으로 로드

---

## 4. 폰트 스케일링 공식

### 기본 크기 (scale=100%)

| 폰트 상수 | 기본 크기 | 용도 |
|-----------|----------|------|
| `FONT_TITLE` | 18pt bold | 타이틀 |
| `FONT_SECTION` | 14pt bold | 섹션 제목 (카드 타이틀) |
| `FONT_BODY` | 13pt | 본문 라벨, 버튼 텍스트 |
| `FONT_INPUT` | 13pt | 입력 필드 |
| `FONT_SMALL` | 11pt | 행 라벨, 보조 텍스트 |
| `FONT_MONO` | 10pt | 자동완성 드롭다운, 통계 텍스트 |
| `FONT_STATUS` | 12pt | 상태 메시지 |

### 스케일 적용 공식

```
scaled_size = max(8, round(base_size * font_scale / 100))
```

- 최소 크기: 8pt (가독성 보장)
- 반올림 적용

### 스케일 예시

| base_size | 80% | 100% | 120% | 150% |
|-----------|-----|------|------|------|
| 18 | 14 | 18 | 22 | 27 |
| 14 | 11 | 14 | 17 | 21 |
| 13 | 10 | 13 | 16 | 20 |
| 11 | 9 | 11 | 13 | 17 |
| 10 | 8 | 10 | 12 | 15 |

---

## 5. 구현 상세

### 5-1. config.py (신규 모듈)

| 항목 | 설명 |
|------|------|
| `CONFIG_FILE` | 스크립트 디렉토리 내 `config.json` 경로 |
| `BASE_FONT_SIZES` | 7개 폰트의 기본 크기 dict |
| `DEFAULT_CONFIG` | 플랫폼별 기본 설정 dict |
| `FONT_CANDIDATES` | 일반 글꼴 후보 리스트 |
| `MONO_FONT_CANDIDATES` | 고정폭 글꼴 후보 리스트 |
| `load_config()` | config.json 로드, 없으면 기본값, scale 클램핑 |
| `save_config(config)` | config.json에 JSON 저장 |
| `compute_fonts(config)` | scale 적용하여 7개 폰트 튜플 + 패밀리명 dict 반환 |

### 5-2. gui.py 변경점

| 변경 | 설명 |
|------|------|
| 모듈 레벨 폰트 초기화 | 하드코딩 → `compute_fonts(load_config())` |
| `__init__()` | config 로드 → `_reload_fonts()` 호출 |
| `_reload_fonts(config)` | `global` 키워드로 9개 폰트 상수 갱신 |
| 설정 버튼 | 초기화 버튼 아래에 `[설정]` 버튼 추가 (border_width=1 outline 스타일) |
| `_open_settings()` | 설정 다이얼로그 (CTkToplevel 모달) |
| `_save_ui_state()` | 현재 입력값 캡처 (티커/가중치/이름, 금액, 기간, 시뮬레이션 수) |
| `_restore_ui_state(state)` | 캡처한 입력값 복원 |
| `_rebuild_ui()` | 상태 저장 → 전체 위젯 destroy → `_build_ui()` 재호출 → 상태 복원 |

### 5-3. 적용 흐름

```
[적용] 클릭
  -> save_config(new_config)      # config.json에 저장
  -> _reload_fonts(new_config)    # 글로벌 폰트 상수 갱신
  -> _setup_chart_style()         # matplotlib rcParams 갱신
  -> dialog.destroy()             # 다이얼로그 닫기
  -> _rebuild_ui()                # UI 리빌드
       -> _save_ui_state()        # 입력값 캡처
       -> root 자식 전부 destroy
       -> _build_ui()             # 새 폰트로 위젯 재생성
       -> _restore_ui_state()     # 입력값 복원
```

---

## 6. 테스트 시나리오

| # | 시나리오 | 기대 결과 |
|---|---------|----------|
| 1 | 기본 상태에서 `--gui` 실행 | 플랫폼 기본 폰트로 정상 표시 |
| 2 | [설정] 버튼 클릭 | 다이얼로그 열림, 현재 설정값 표시 |
| 3 | 글꼴 ComboBox 변경 | 미리보기 라벨에 실시간 반영 |
| 4 | 크기 슬라이더 조절 | 미리보기 라벨 크기 변경 + 퍼센트 표시 |
| 5 | [적용] 클릭 | UI 전체 새 폰트 적용, 입력값 유지 |
| 6 | [취소] 클릭 | 변경 없이 다이얼로그 닫힘 |
| 7 | 프로그램 재시작 | 변경된 설정 유지 (config.json 확인) |
| 8 | config.json 삭제 후 실행 | 기본값으로 정상 동작 |
| 9 | 크기 80% 적용 | 모든 텍스트 축소, UI 깨짐 없음 |
| 10 | 크기 150% 적용 | 모든 텍스트 확대, UI 깨짐 없음 |
| 11 | 폰트 변경 후 시뮬레이션 실행 | 차트 폰트도 변경 반영 |
| 12 | CLI 모드 실행 | 설정 기능 영향 없음 |
| 13 | 시뮬레이션 결과 표시 중 폰트 변경 | 리빌드 후 결과 영역 클리어됨 |
| 14 | 티커/가중치 입력 후 폰트 변경 | 리빌드 후 입력값 유지됨 |
| 15 | 날짜 범위 모드에서 폰트 변경 | 리빌드 후 기간 모드/값 유지됨 |
