# 편집 계획

제목·고정 시간·요소별 폰트 등 사용자 수정은 [커스터마이징](customization.md)의 `text_overlays`를 사용한다. `position_mode:fixed`이면 해당 요소에 컷별 `timeline_offset_y`를 적용하지 않는다. 명시한 사용자 설정이 기본 스타일보다 우선한다.

`--root WORKDIR`가 모든 입력·출력 상대경로의 기준이다. 계획 파일은 WORKDIR 안의 JSON이나 절대경로로 지정한다. 출력/부가 기록을 덮어쓰지 않는다.

기본 입력은 무음 H.264 SDR MP4. 1080×1920, 24fps, H.264 출력. 4~20컷, 컷당 0.5~4초(24fps 프레임에 맞춤), 전체 10~40초를 지원한다. 이 범위가 장면에 맞지 않으면 임의로 장면을 늘리지 말고 범위 조정을 설명한다. 현재 렌더러는 fill crop이며 fit letterbox를 지원한다고 말하지 않는다.

타임로그를 요청한 경우에는 컷당 약 2초가 기본이다. 1초 원본은 1초 그대로, 3초나 10초 원본은 의미 있는 동작의 약 2초 구간을 사용한다. 동작 완결성에 따라 조금 조절할 수 있다. 원본이 충분하지 않아 총길이 제한과 충돌하면 반복·정지·임의 늘리기로 맞추지 말고 렌더 범위 조정이 필요함을 설명한다. 긴 영상 분석 도구는 구간 선택을 돕는 수단이며 긴 요약본을 만드는 것이 타임로그의 목적은 아니다. 실제 촬영시각이 확인되면 그 순서와 시간 자막을 유지하고, 모르는 시각은 지어내지 않는다.

타임로그 기본 스타일은 [timelog-style.json](timelog-style.json)이다. 번들 `assets/fonts/NotoSansKR-Regular.otf`를 시간·문장 모두에 쓰며 1080px 너비 기준 시간 54px, 문장 52px, 흰색·검은 테두리 2px로 표시한다. 렌더러는 타임로그 계획의 생략된 값에 이 스타일을 적용한다. 명시한 다른 글꼴·크기·구도는 우선하므로 기존 계획을 이번 기본값으로 변경할 때에는 이전 font와 크기를 에이전트가 갱신한다. 출력 화면에서의 비율이 기준이며 휴대폰 화면 픽셀을 그대로 쓰지 않는다. 레퍼런스의 원본 폰트명을 확정한 것으로 설명하지 않는다. 번들 폰트의 저작권과 이용 조건은 assets/fonts/NotoSansKR-LICENSE.txt에 보존한다.

개인 영상의 시계 없는 예:

```json
{
  "source_kind": "personal",
  "disclosure_label": "",
  "timeline_mode": false,
  "caption_style": {"font_size": 53, "font_index": 4, "y": 980, "stroke_width": 2},
  "music": null,
  "shots": [
    {"source": "clips/a.mp4", "start": 0, "duration": 2.5, "crop_x": 0.5, "caption": "아침 준비"},
    {"source": "clips/b.mp4", "start": 1, "duration": 2.5, "crop_x": 0.4, "caption": "커피 한 잔"},
    {"source": "clips/c.mp4", "start": 0, "duration": 2.5, "crop_x": 0.6, "caption": "잠깐 산책"},
    {"source": "clips/d.mp4", "start": 2, "duration": 2.5, "crop_x": 0.5, "caption": "집으로"}
  ]
}
```

예시의 자막·구간을 실제 영상에 그대로 붙이지 않는다. `crop_x`는 좌0~우1. `crop_end_x`를 쓰면 구간 동안 가로 구도가 이동한다.

중앙 시계+행동 두 줄은 [stock-example.json](stock-example.json)을 참고한다. 스톡 예제는 [출처 기록](stock-sources.txt)의 원본 5개가 별도로 필요하며 스킬에 원본은 없다. 이 예는 `source_kind:stock`, `disclosure_label:예시 타임라인 · 스톡`, `time_label_policy:editorial`로 연출 시각임을 명시한다. 사용자가 예시 시각을 요청하지 않은 개인 영상에는 넣지 않는다. 실제 촬영시각이 확인된 경우만 `time_label_policy:capture_verified`와 해당 컷의 `capture_time_evidence`를 사용한다. `timeline_offset_y`는 중앙 블록을 0~400px 내린다.

선택 BGM:
`"music": {"source":"music/licensed.mp3","start":0,"gain_db":-8,"fade_in":0.6,"fade_out":1.2}`
이 설정은 단순 gain+fade이며 자동 loudness 보정을 약속하지 않는다. 출력 구간 이상의 길이가 있는 음원이 필요하다. MP4에서 음원을 추출해 재사용하지 않는다. 법적으로 사용할 수 있는 별도 원본만 쓴다.

배포 기본 폰트는 macOS·Windows 모두 번들 Noto Sans KR Regular다. 개인 오버라이드와 이번 영상의 명시적 폰트 선택은 이 기본값보다 우선한다. Windows의 단일 TTF에서는 macOS 예제의 font_index를 0으로 정규화한다. 다른 폰트를 직접 지정하면 `.ttc`의 font_index가 달라질 수 있으므로 확인한다. 저작권이 있는 시스템 폰트를 복사해 배포하지 않는다.
