# 선택적인 실제 프레임 스타일 미리보기

사용자가 실제 영상 위에서 글꼴·배치를 보고 싶어 하거나 영상 시안 전 정밀 확인이 필요할 때만 사용한다. 기본 콘티는 [이미지 생성으로 그린 콘티](visual-storyboard.md)다. 이 도구를 콘티 이미지 생성으로 설명하지 않는다.

```sh
bash scripts/run.sh style-preview PLAN --root WORKDIR --output-dir outputs/style-preview-v001
```

Windows는 `scripts\run.cmd style-preview ...`다. 실제 원본의 중간 프레임을 최종 MP4와 같은 크롭·자막 설정으로 합성한다. `shot-01.png` 등 개별 이미지와 안내선 버전, 최대 6컷 단위 시트가 나온다. 안내선은 UI 회피 참고용이며 공식 플랫폼 규격이 아니다. 새 폴더를 사용하고 원본·이전 결과를 보존한다.

v018의 `storyboard` 명령은 호환 별칭으로 유지한다. 출력 파일의 `storyboard-*.png`와 `storyboard.json`도 기존 이름을 유지하지만 **실제 프레임 스타일 미리보기** 자료다. 기본 그림 콘티와는 세션의 kind 및 저장 폴더로 구분한다.

정확한 폰트·테두리·픽셀 배치는 이 미리보기나 실제 영상에서 확인한다. 정지 이미지는 움직임·전환·음악 검수를 대신하지 않는다. 자동 보고의 `agent_image_view:not_checked`는 유지하고 실제 열람 결과를 세션에 따로 기록한다. 사용자가 요청하지 않은 선택 미리보기 때문에 제작 확인 단계를 추가하지 않는다.
