# Contributors

`im-not-ai`(humanize-korean) 개발에 기여해 주신 분들을 기록합니다. GitHub의 자동 Contributors 통계는 commit author 기준이라 외부 통찰·reference 작업이 잘 잡히지 않아, 별도 명단으로 정리합니다.

## Maintainer

- **[@epoko77-ai](https://github.com/epoko77-ai)** (이승현, epoko@nate.com) — 프로젝트 창립 및 유지보수. 분류 체계(`ai-tell-taxonomy.md`) 설계, 초기 5인 에이전트 파이프라인 구축(v2.1에서 정밀 3콜 구조로 재편), v1.0~v1.2 릴리스 책임.

## v1.2 외부 기여자

### [@simonsez9510](https://github.com/simonsez9510) (Won Seongmuk)

**기여**: 한국어 비소설 단행본 원고(약 8.5만 자, 9개 챕터+에필로그) 출판사 송고 전 최종 검수에 v1.1을 실전 적용한 후기 + 개선 제안 4건 + 어댑터 reference PR.

**반영**:
- [Issue #1](https://github.com/epoko77-ai/im-not-ai/issues/1) "실전 사용 후기 + 개선 제안 4건 — 단행본 원고 8.5만 자 적용 결과"
  - v1.2 권한 위계 §1~§6 신설 동기 (`ai-tell-taxonomy.md`)
  - `author-context.yaml` 스키마 신설 (`references/author-context-schema.md`)
  - 에이전트 주입 분리 정책 (detector/rewriter/auditor 주입, naturalness-reviewer 미주입)
- [PR #3](https://github.com/epoko77-ai/im-not-ai/pull/3) "v1.2 권한 위계 다운스트림 어댑터 reference"
  - Multiplier 캡 정책 (일반 ≤ 2.0, D-1~D-6 ≤ 1.5, A-8·C-5 = 1.0 고정)
  - `reviewer_contract.naturalness_reviewer_voice_blind` 강제 필드
  - Schema validator 책임 강화 (자유 텍스트 거부, prompt injection escape character 검증)
  - Telemetry 정책 (`voice_profile_log.json`)
  - Hard-block은 caller/adapter 책임 명시
  - 어댑터 reference 본체는 `references/proposals/` 격리 보존 예정 (book_essay 보강 후 머지)

**관련 commit**: `bfcf676`, `9f39ce0`, `81fd1b9`

### [@gaebalai](https://github.com/gaebalai) (AI-fluent liberal arts Engineer)

**기여**: LICENSE 누락 지적 + 슬래시 커맨드/Plugin/자동 설치기 reference + 외부 distribution channel 운영.

**반영**:
- [Issue #5](https://github.com/epoko77-ai/im-not-ai/issues/5) "라이선스 내용이 추가해주심이?"
  - MIT License 본체 도입 (`LICENSE`, `adc2814`)
- [Issue #6](https://github.com/epoko77-ai/im-not-ai/issues/6) "슬래시커맨드가 있으면 더 좋을것 같아요"
  - `/humanize`, `/humanize-redo` 슬래시 커맨드 본체 도입 (`9054518`)
  - v1.3 메이저 업데이트 검토 ([Issue #8](https://github.com/epoko77-ai/im-not-ai/issues/8))
- [`gaebalai/im-not-ai`](https://github.com/gaebalai/im-not-ai) 포크
  - Claude Code Plugin/Marketplace 규격 패키징 reference
  - 자동 설치기(`install.sh`) reference
  - 6개 슬래시 커맨드 reference
  - README "방법 C"에서 본체 distribution channel로 안내

**관련 commit**: `adc2814`, `9054518`

## v2.3 외부 기여자 (2026-08)

이 회차는 **머지된 PR보다 '찾아준 결함'이 더 컸습니다.** 아래 세 분의 발견은 저장소가 직접 고쳤으므로 commit author 에는 남지 않습니다. 이 명단이 존재하는 이유가 정확히 이것입니다.

### [@bukbuk82-alt](https://github.com/bukbuk82-alt)

**기여**: 심링크 설치 사용자가 **첫 실행부터 항상 실패**하던 경로 해석 버그를 재현·원인 분석·문서 모순까지 짚어 제보.

- [Issue #71](https://github.com/epoko77-ai/im-not-ai/issues/71) — `_resolve_run_dir()` 이 상대경로를 cwd 가 아닌 저장소 루트 기준으로 절대화. SKILL.md 는 "모든 경로는 cwd 기준"이라 지시하는데 스크립트가 반대로 동작. 저장소 루트에서 돌리면 `cwd == PROJECT_ROOT` 라 **내부에서는 영원히 안 보이는 버그**였습니다. 실패할 때마다 빈 `_workspace/{run_id}/` 가 쌓이던 부작용까지 지적.
- 반영: [PR #78](https://github.com/epoko77-ai/im-not-ai/pull/78) — cwd 기준 해석 + `--diagnosis` 기준 통일 + 빈 디렉터리 누적 제거. 저장소 밖 임시 cwd 에서 도는 회귀 테스트 5건 신설(`tests/test_run_dir_resolution.py`).

### [@andrea9292](https://github.com/andrea9292)

**기여**: Hermes 포트를 만들며 **계약·경계 두 축을 교차 검증**해 실행 불가 경로 2건 발견.

- [Issue #59](https://github.com/epoko77-ai/im-not-ai/issues/59) — 프로덕션 게이트 `verify_gates.py` 가 `tests/golden/checks.py` 를 런타임 import. 저장소 전체 배포에서는 동작하지만 **런타임만 선별 배포하면 P3 golden 축이 통째로 죽습니다.** 게이트가 조용히 한 축을 잃는 최악의 실패 형태.
  - 반영: [PR #79](https://github.com/epoko77-ai/im-not-ai/pull/79) — `checks.py` 를 `scripts/` 로 이동(이름만 tests 아래 있었을 뿐 전부 프로덕션 검사 로직). `tests/` 없는 트리에서 실제로 실행되는 회귀 테스트 신설.
- [Issue #54](https://github.com/epoko77-ai/im-not-ai/issues/54) — Light 경로는 `02_diagnosis.md` 를 만들지 않는데 finalize 승급 규칙은 전 경로 공통이고 finalizer 는 그 파일을 필수로 요구. **Light 승급이 실행 불가.**
  - 반영: [PR #80](https://github.com/epoko77-ai/im-not-ai/pull/80) — `diagnosis_path` 를 선택으로. 진단 콜을 추가하지 않는 쪽을 upstream 의도로 확정(finalize 본체는 원문↔윤문본 직접 대조로 성립).

### [@yswyang0228](https://github.com/yswyang0228)

**기여**: 전역 에이전트 풀 오염 진단 + **구버전 링크 마이그레이션 정리 아이디어**.

- [PR #57](https://github.com/epoko77-ai/im-not-ai/pull/57) — 같은 문제를 다룬 #70 과 중복이고 저장소 로컬 `.claude/agents/` 방식이 #69 의 인벤토리 테스트와 충돌해 닫았습니다. 다만 **구버전 개발용 링크·은퇴 dangling 링크 자동 해제는 이 PR 에만 있던 개선**이었습니다.
- 반영: [Issue #73](https://github.com/epoko77-ai/im-not-ai/issues/73) 으로 승계 → [PR #81](https://github.com/epoko77-ai/im-not-ai/pull/81) 로 구현. 소유권을 심링크 대상으로만 판별해 사용자 파일·타 도구 링크는 불가침으로 설계.

### [@penta505](https://github.com/penta505)

**기여**: 배포 정합성 4건을 각각 회귀 테스트와 함께 제출. 이 회차 머지 PR 의 대부분.

- [PR #67](https://github.com/epoko77-ai/im-not-ai/pull/67) — fixture 가 원문에 없는 문자열(`"세 가지"`)을 보존 대상으로 요구하던 것 수정 + `protected_tokens ⊆ input_text` 무결성 테스트
- [PR #68](https://github.com/epoko77-ai/im-not-ai/pull/68) — 매니페스트 버전 드리프트(2.1.0 → 2.3.0) + 버전 sync 테스트 + RELEASING.md 경로 정정
- [PR #69](https://github.com/epoko77-ai/im-not-ai/pull/69) — SKILL.md 에이전트 서술 정합(한 문단에 12종/10개/실물 9종 세 숫자가 달랐음) + 인벤토리 테스트
- [PR #70](https://github.com/epoko77-ai/im-not-ai/pull/70) — 전역 설치를 런타임 4종으로 한정 + `--all-agents` 탈출구 + **셸 테스트를 CI 에 최초 등록**

### [@ruddyscent](https://github.com/ruddyscent) (Kyungwon Chun)

**기여**: 내용 앵커 유실(#74) 수정 — 이슈 등록 몇 시간 만에 제출.

- [PR #75](https://github.com/epoko77-ai/im-not-ai/pull/75) — `anchor_ledger` 런타임 계약. 편집 **전에** 핵심 내용 명사를 기록하고 앵커가 사라지는 edit 은 즉시 롤백. 보존 책임을 사후 검사가 아니라 편집 루프 안에 넣은 것이 핵심 판단이었습니다. 배포 경로 5곳 전수 적용 + 경로 정합 테스트.
  - 실측: opus-5 × fx_guard_overedit 전후 각 11 run 에서 **확장성·지속가능성 유실 2회 → 0회**.
  - 하네스 변경(프롬프트에 fixture 정답 주입)만 되돌렸습니다 — 사유는 PR 코멘트에 상술.
  - 이 조사 과정에서 fixture 가 taxonomy D-7 이 제거를 지시하는 표현을 보존 대상으로 요구하던 별개 결함도 드러났습니다.
- [PR #72](https://github.com/epoko77-ai/im-not-ai/pull/72) — Codex 포트 3경로 확장 (검토 중)

### [@MinJ-park](https://github.com/MinJ-park)

**기여**: vendoring 후 멀티에이전트 리뷰(발견별 적대적 검증 포함) 14건 공유.

- [Issue #43](https://github.com/epoko77-ai/im-not-ai/issues/43) — 산출물 계약 드리프트·실행 경로 버그. 특히 **`metrics_v2.py` 기본 baseline 이 존재하지 않는 파일을 가리켜 z-score 14개가 전부 None 이 되는데 경고는 0건**이던 발견은 자체적으로 찾기 어려운 종류였습니다. "조용한 실패" 라는 렌즈가 이후 게이트 설계에 계속 쓰였습니다(#59 도 같은 렌즈).

### [@cakel](https://github.com/cakel)

**기여**: 마켓플레이스 배포 누락 지적.

- [Issue #33](https://github.com/epoko77-ai/im-not-ai/issues/33) — v2.0.0 태그 미publish 로 사용자가 v1.5.0 만 받던 문제. 이후 릴리스 절차에 태그·publish 확인이 편입됐습니다.

### [@needsbuilder](https://github.com/needsbuilder)

**기여**: Hermes Agent 런타임 포트.

- [PR #61](https://github.com/epoko77-ai/im-not-ai/pull/61) — **받아본 런타임 포트 중 완성도가 가장 높았습니다.** 본체 완전 무수정, 실파일 번들, 그리고 quick-rules 사본이 본진과 드리프트하면 CI 가 깨지는 동기 검사까지. 사본 방식의 최대 위험인 "조용히 썩기" 를 정확히 막은 설계로, 이후 다른 포트를 볼 때 기준으로 삼고 있습니다.
- 공식 지원 런타임을 늘리지 않는다는 **정책 판단**으로 닫았습니다(라이브 검증 수단이 없는 런타임에 "공식 지원" 을 표기할 수 없음). 별도 저장소로 유지해 주시면 README 커뮤니티 포트 항목에 링크합니다.

### [@cuhong](https://github.com/cuhong)

**기여**: 사용자 피드백 축적 채널 제안 + HG-1 패턴(선언형 은유 → 담백한 기술 서술).

- [PR #66](https://github.com/epoko77-ai/im-not-ai/pull/66) — 배선 방식(심사 게이트 없는 파일이 quick-rules 보다 높은 우선순위 + 매 세션 임포트)이 SSOT 단일성·슬림성과 충돌해 닫았습니다. **HG-1 콘텐츠 자체는 정확한 관찰**이라 D-5 보강 또는 `estimated` 신규 패턴으로 taxonomy 재제출을 요청드렸습니다.

### 검토 중

[@eungwonkim](https://github.com/eungwonkim) ([PR #56](https://github.com/epoko77-ai/im-not-ai/pull/56) C-8 발동 조건) · [@nhleeclaw](https://github.com/nhleeclaw) ([PR #60](https://github.com/epoko77-ai/im-not-ai/pull/60) D-8·F-6 신설) · [@hyeonsangjeon](https://github.com/hyeonsangjeon) ([PR #65](https://github.com/epoko77-ai/im-not-ai/pull/65) Copilot CLI) · [@junhwanjang](https://github.com/junhwanjang) ([PR #64](https://github.com/epoko77-ai/im-not-ai/pull/64) commit-ko)


## 기여하기

본 프로젝트는 MIT 라이선스이며 외부 기여를 환영합니다. 기여 형태는 다음 중 무엇이든 좋습니다.

- **새 AI 티 패턴 제보** — `references/ai-tell-taxonomy.md` 후보로 Issue 등록 (실증 사례 2건+ 첨부 시 승격 검토)
- **사용성 개선 제안** — 슬래시 커맨드, Plugin 통합, 자동화 reference 등
- **다국어 확장** — 일본어/중국어 분류 체계 적용 가능성 검토
- **버그 리포트** — Issue로 등록
- **테스트·fixture 기여** — 회귀 테스트 스위트 확장(새 fixture·판정 차원). [`tests/README.md`](tests/README.md) 참고

PR 보내실 때는 GitHub 기본 inbound = outbound 원칙에 따라 동일한 MIT 라이선스로 contribution됩니다. 본 명단은 릴리스 단위로 갱신됩니다. **머지되지 않은 제보·리뷰도 기록합니다** — 이 명단이 존재하는 이유가 commit author 로는 잡히지 않는 기여를 남기기 위해서입니다.
