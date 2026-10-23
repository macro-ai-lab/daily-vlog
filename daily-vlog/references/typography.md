# 용도별 글꼴과 릴스 자막 배치

스타일 제안·이미지 콘티·폰트 변경 때 읽는다. 아래는 인스타그램 사용량 순위가 아닌 용도별 디자인 추천이다. 이번 요청 > 승인된 개인 지침 > 배포 기본값 순으로 적용하며 기존 기본 Noto Sans KR를 임의 교체하지 않는다.

## 바로 사용할 글꼴

| 용도 | 번들 선택 | 제안할 장면 |
|---|---|---|
| 정보·설명 | Pretendard SemiBold / SUIT SemiBold | 설명·말 자막·방법 안내 |
| 감성 브이로그 | 마루 부리 SemiBold / 고운바탕 Bold | 차분한 일기·부드러운 짧은 문장 |
| 썸네일·포인트 | 검은고딕 Regular | 짧고 강한 한글 제목·핵심 한마디 |
| 기존 기본 | Noto Sans KR Regular | 기존 계획과 타임로그 기본값 유지 |

같은 실제 장면·문구에서 2~3개만 비교하고, 설명·감성·강조 글꼴을 모든 컷에 섞지 않는다. 검은고딕의 Regular는 가는 굵기를 뜻하지 않으며 제목용으로 굵다. 지원 문자가 제한되므로 실제 문구의 누락·네모 글자를 이미지에서 확인한다. 지원하지 않는 문자에는 사용자가 선택할 대안을 제안한다.

[실제 글꼴 비교](../assets/font-comparison.png)는 단색 배경의 참고 이미지다. 최종 선택은 원본 위의 이미지 콘티로 한다.

에이전트는 선택한 폰트의 실제 경로를 받는다:

```sh
bash scripts/run.sh font --name "고운바탕" --output-dir WORKDIR/fonts
```

Pretendard / SUIT / 마루부리 / 고운바탕 / 검은고딕과 영문 이름을 지원한다. 이 선택들은 추가 다운로드나 시스템 설치 없이 번들 파일과 라이선스의 해시를 확인해 경로를 반환한다. 정적 폰트에는 `font_weight`를 넣지 않는다. 이전 가변 폰트 설정을 바꾸면 `font_weight:null`로 제거한다. 제목·시간·설명 각각의 font가 우선하므로 바꾸려는 요소의 실제 설정에 경로를 적용한다. Noto Sans KR의 다른 굵기는 기존 `font --name "Noto Sans KR"` 다운로드를 사용한다.

## 크기와 배치

- 한 번에 한 의미를 읽게 한다. 짧은 한 줄을 우선하고 긴 문장은 작은 글씨로 축소하기보다 문구·자막 이벤트를 나눈다. 현재 두 줄 설명은 지원하지 않는다.
- 제목은 도입 구간에 짧게, 시간은 별도 고정 자리, 설명은 겹치지 않는 자리로 둔다. 모든 글자를 동시에 크고 굵게 하지 않는다.
- 얼굴뿐 아니라 손·음식·제품·휴대폰 화면도 가리지 않는지 본다. 사용자가 고정한 시간은 임의 이동하지 않는다.
- 하단의 계정·설명·음원과 오른쪽 버튼 영역을 고려한다. 안내선은 참고이며 실제 게시 미리보기에서 확인한다. Meta의 광고용 규격을 일반 릴스 전체의 고정 픽셀 규칙으로 확대하지 않는다.
- 밝고 어두운 화면을 모두 비교한다. 얇은 테두리·그림자부터 검토하고, 명조·감성 글꼴에 굵은 검은 테두리를 일괄 적용하지 않는다. 원본 배경에 맞는 어두운 글자도 비교할 수 있다.
- 기본색과 강조색 하나부터 시작한다. 강조는 핵심 문구에만 준다. 움직이는 효과는 실제 지원 범위 안에서만 제안한다.
- 1080×1920 이미지를 약 360×640으로 줄인 모습과 휴대폰 재생을 확인한다. PC의 크게 확대한 미리보기만으로 크기를 정하지 않는다.

비교 시작값으로 정보 자막 60~72px, 감성 문장 52~64px, 짧은 제목 88~112px를 사용할 수 있다. 플랫폼 규칙이나 새로운 배포 기본값은 아니다. 실제 글자 폭·구도·요소별 지원 범위를 우선하고, 기존 사용자 크기를 덮어쓰지 않는다. 90px를 넘는 제목은 `text_overlays.title.font_size`처럼 요소별 설정을 사용한다.

## 출처와 이용 조건

번들 원본·버전 또는 커밋·SHA256·라이선스는 [font-catalog.json](font-catalog.json)과 각 폰트의 `assets/fonts/*LICENSE*` / `*OFL*`에 보존한다. 번들 폰트는 SIL OFL 1.1이며 저작권·라이선스를 함께 배포한다. 영상에 글자를 그리는 것과 폰트 파일 재배포는 구분한다. [SIL OFL FAQ](https://openfontlicense.org/ofl-faq/)

- [Pretendard](https://github.com/orioncactus/pretendard), [SUIT](https://github.com/sun-typeface/SUIT): 공식 OFL과 파일 확인.
- [마루 부리 소개](https://hangeul.naver.com/font), [네이버 라이선스 전문](https://help.naver.com/service/30016/contents/18088?osType=PC&lang=ko): 화면용 부리 글꼴, 라이선스 동봉 번들 가능. 전문에는 네이버의 여러 글꼴 예약명이 함께 포함된다.
- [고운바탕](https://github.com/yangheeryu/Gowun-Batang): 연필 손글씨에서 영감을 받은 부리 글꼴, OFL.
- [검은고딕](https://github.com/zesstype/Black-Han-Sans): 제목용, 제한된 문자 지원, OFL.
- [산돌의 영상 자막 트렌드](https://www.sandollcloud.com/font-recommendations/article/278/20): 명조 자막과 다양한 썸네일 글꼴의 스타일 참고. 소개된 유료 폰트를 무료 번들로 취급하지 않는다.
- [Meta Reels 안내](https://www.facebook.com/business/ads/facebook-instagram-reels-ads): 핵심 메시지와 UI 안전 영역 고려.
- [Netflix 한국어 자막 지침](https://partnerhelp.netflixstudios.com/hc/en-us/articles/216001127-Korean-Timed-Text-Style-Guide): 한 줄 우선·최대 두 줄 등 가독성 원칙 참고. 글자 수·시간 규칙은 해당 플랫폼의 번역 자막 규칙이며 릴스 규칙이 아니다.

온글잎 콘콘체, G마켓 산스, 잘난체, 카페24 써라운드도 추가 후보지만 이번 번들에 포함하지 않았다. 공식 배포 파일과 각 버전의 최신 영상 이용·번들 조건을 확인한 뒤 추가한다. 특히 잘난체 원본·고딕·2의 조건을 혼동하지 않는다.
