# 편집 계획

제목·고정 시간·요소별 폰트 등 사용자 수정은 [커스터마이징](customization.md)의 `text_overlays`를 사용한다. `position_mode:fixed`이면 해당 요소에 컷별 `timeline_offset_y`를 적용하지 않는다. 명시한 사용자 설정이 기본 스타일보다 우선한다.

시작 설정·분석·사용자 맥락·자막을 바탕으로 만든 [이미지 생성으로 그린 콘티](visual-storyboard.md)를 확인하고, 승인한 장면·배치·스타일 의도를 이 편집 계획으로 옮긴다. 이 계획이나 실제 영상 프레임이 그림 콘티 생성의 필수 입력은 아니다. 정확한 폰트·픽셀 배치는 실제 영상 시안에서 확인한다.

`--root WORKDIR`가 모든 입력·출력 상대경로의 기준이다. 계획 파일은 WORKDIR 안의 JSON이나 절대경로로 지정한다. 출력/부가 기록을 덮어쓰지 않는다.

먼저 [선택한 형식](formats.md)과 분석 후 입력받은 사용자 상황·보여줄 내용·표현 방향을 작업 기록에 보존한다. 새 맥락 질문에 답을 받기 전에는 자막이나 콘티를 확정하지 않는다. 타임로그는 시간 흐름과 행동, 일상 모음은 짧은 관찰·감상, 이야기형은 [이야기 지침](narrative.md)의 한 줄 관점과 장면별 역할로 자막을 정한다. 사용자 맥락·관점·장면 역할·시점·실제 날짜 범위는 `vlog-session.json.narrative`나 별도 작업 기록에 보존하고, 실제 출력 문구만 해당 shot의 자막·오버레이에 적용한다. 렌더러가 이야기 메모를 자동 해석한다고 가정하지 않는다.

기본 입력은 무음 H.264 SDR MP4. 1080×1920, 24fps, H.264 출력. 4~20컷, 컷당 0.5~4초(24fps 프레임에 맞춤), 전체 10~40초를 지원한다. 이 범위가 장면에 맞지 않으면 임의로 장면을 늘리지 말고 범위 조정을 설명한다. 현재 렌더러는 fill crop이며 fit letterbox를 지원한다고 말하지 않는다.

시작에 확인한 영상별 최대 사용 길이를 본편 구간의 상한으로 적용한다. 기본 제안은 2초이며 짧은 원본은 늘리지 않는다. 동작 완결성을 이유로 승인한 상한을 임의로 초과하지 않는다. 예를 들어 최대 2초를 선택했다면 1초 원본은 1초 그대로, 3초나 10초 원본에서는 의미 있는 2초 이하 구간을 사용한다. 원본이 충분하지 않아 총길이 제한과 충돌하면 반복·정지·임의 늘리기로 맞추지 말고 렌더 범위 조정이 필요함을 설명한다. 긴 영상 분석 도구는 구간 선택을 돕는 수단이며 긴 요약본을 만드는 것이 타임로그의 목적은 아니다. 타임로그 요청이면 촬영 순서를 따르고, 시간 표시는 별도의 시작 설정을 따른다. 끈 경우 `text_overlays.time.enabled:false`로 명시하고 시간 자막을 넣지 않는다. 켠 경우에도 실제 촬영시각이 확인된 컷에만 표시하고 모르는 시각은 지어내지 않는다.

선택한 [형식](formats.md)에 맞춰 기본 편집을 적용하고 실제 폰트를 계획에 명시한다. 이야기형의 [기본 연출](default-editing.md)은 Pretendard 본문·마루 부리 포인트·SUIT 시간이며, 타임로그와 일상 모음에는 담백한 본문·시간 중심으로 적용한다. 새 지침은 에이전트의 편집 기준이며 자동 적용되는 render 프리셋이 아니다. 원음·기울임·글로우·움직임은 기본 render 명령 밖의 합성 지원을 확인하고 별도 작업 기록과 검수 결과를 남긴다. 기존 렌더러의 지원 범위는 그대로다.

기존 중앙 타임로그의 호환 기본값은 [timelog-style.json](timelog-style.json)이다. 렌더러는 생략한 폰트·크기에 Noto Sans KR Regular 시간 54px·문장 52px를 적용할 수 있으므로 새 계획에는 실제 선택한 요소별 폰트·크기를 명시한다. 기존 계획·명시 설정·개인 지침은 자동 갱신하지 않는다. 레퍼런스의 정확한 원본 폰트명을 확인한 것으로 설명하지 않는다.

개인 영상의 시계 없는 예(최대 3초를 선택한 경우):

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

새 기본 연출의 Pretendard·마루 부리·SUIT와 기존 호환용 Noto Sans KR는 번들 파일을 사용한다. 개인 오버라이드와 이번 영상의 명시적 폰트 선택이 우선한다. Windows의 단일 TTF에서는 macOS 예제의 font_index를 0으로 정규화한다. 다른 폰트를 직접 지정하면 `.ttc`의 font_index가 달라질 수 있으므로 확인한다. 저작권이 있는 시스템 폰트를 복사해 배포하지 않는다.

## 제작 이력 메타데이터

새 계획 최상위에 `production_id`(작품별 안정된 ID, 수정 버전 간 동일)와 `edit_format`(`timelog` / `moments` / `story`)을 넣는다. 렌더 후 [타입별 제작 이력](production-history.md)에 사용된다. 기존 계획에 없으면 unclassified로 보존하며 자동으로 타임로그라고 추정하지 않는다.

콘텐츠 유형은 `content_type`, 표시명은 `content_type_label`, 편집 방식은 `edit_format`으로 분리한다. 모든 키는 개방형이며 [유형 안내](formats.md)에 따라 새 키를 추가할 수 있다. 예: `content_type:travel_review`, `content_type_label:여행 후기`, `edit_format:timelog`.
