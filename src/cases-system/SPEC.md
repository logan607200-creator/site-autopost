# 수리사례 포스팅 시스템 공통 약속 (그릿서비스 · 로건서비스)

2026-10-22. 오토밴스(autovance.co.kr)식 "수리 한 건 = 페이지 한 장"을 그릿·로건에 만든다.
참고: /mnt/project-files/marketing-review/오토밴스-분석-20261022.md

## 폴더

```
/mnt/project-files/cases-system/
  SPEC.md                 이 문서 (모두가 지킬 약속)
  engine/make_cases.py    공통 생성기 (개발자)
  engine/check_cases.py   검사기 (개발자)
  grit/
    site.yaml             사이트 정보·카테고리·지역어 (마케터가 채움)
    guide.md              글쓰기 규칙·키워드 지도 (마케터)
    posts/*.yaml          사례 글 1건 = 파일 1개 (마케터가 예시 작성)
    templates/            Jinja2 템플릿 + case.css (디자이너)
    design-notes.md       디자인 설명 (디자이너)
  logan/  (같은 구조)
  build/grit-preview/, build/logan-preview/   미리보기 (draft 포함)
  build/grit-upload/, build/logan-upload/     서버에 올릴 것 (draft 제외)
```

## URL

- 목록: `/cases/` (index.html), 카테고리별: `/cases/{category_slug}/`
- 글: `/cases/{slug}/` (index.html). slug = `{YYMMDD}-{브랜드영문}-{모델영문}-{작업영문}` 예: `261022-kia-k5-rear-bumper`
- 사진: `/assets/cases/{slug}-{nn}.webp`

## 글 파일 형식 (posts/{slug}.yaml, YAML, 마크다운 라이브러리 없음)

```yaml
slug: 261022-kia-k5-rear-bumper
date: 2026-10-22
draft: true            # true = 예시/확인 전. 업로드본에서 빠지고 미리보기에만 나옴
category: accident     # site.yaml categories 의 key
title: "K5 후방추돌 범퍼·트렁크 판금도색"          # 화면 H1 (증상/사고 + 작업)
seo_title: "기아 K5 후방추돌 리어범퍼 교환·트렁크 판금도색 보험수리 | 파주 그릿서비스"   # <title>, 40자 이내(네이버 기준)
description: "..."     # meta description 50~80자(네이버 기준), 지역어 1회
summary: "..."         # 한두 문장 결론. 숫자·사실 위주. AI 발췌용, 글 맨 위 요약 박스
car: {brand: 기아, model: K5, year: 2021, km: 45000}   # year/km 모르면 생략
region: 운정            # 고객 지역(선택)
symptoms: [후방추돌, 리어범퍼 파손, 트렁크 찌그러짐]
work: [리어범퍼 교환, 트렁크 리드 판금, 도색·조색]
tags: [파주 사고수리, 파주 판금도색, K5 범퍼]   # 화면 하단 태그(링크 아님)
cover: {src: assets/cases/261022-kia-k5-rear-bumper-01.webp, alt: "..."}
sections:              # 본문. 순서대로 H2
  - h2: 입고 상태
    text: |            # 문단은 빈 줄로 구분. **굵게** 정도만 허용
      ...
    photos:
      - {src: ..., alt: "...", caption: "..."}
  - h2: 손상 진단
  - h2: 작업 과정
  - h2: 출고
faq:                   # 0~3개. FAQPage 구조화 데이터
  - {q: "...", a: "..."}
related: [다른 slug, ...]   # 선택. 없으면 같은 category 최근 글 3개 자동
```

## 템플릿 약속 (Jinja2, templates/ 안)

- `base.html` 공통 틀(head, 헤더, 푸터, 하단 전화·카톡 바). 블록: `title`, `head_extra`, `content`
- `case.html` 글 상세 (extends base). 변수: `site`(site.yaml 전체), `post`(위 YAML 전체 + `url`, `date_kr`, `category_name`), `related`(post 목록), `jsonld`(문자열, 개발자가 만듦), `root`(사이트 루트로 가는 상대경로 접두어, 예 `../../`)
- `list.html` 목록 (extends base). 변수: `site`, `posts`, `categories`, `current_category`(없으면 None), `root`
- `card.html` 카드 1장 include. 변수 `p`(post)
- `home-section.html` 홈에 넣을 "최근 수리사례" 섹션 조각(최근 6개). 변수 `posts`, `root`(홈은 "")
- `case.css` 위 페이지 전용 CSS. 모든 경로는 `{{ root }}` 기준 상대경로.
- 본문 `text`는 개발자가 `|para` 필터로 <p> 변환, `**굵게**` 만 처리. 디자이너는 `{{ s.text|para }}` 로 씀.
- 이미지에 width/height, loading="lazy"(첫 이미지 제외). h1 1개. 한글은 word-break:keep-all.

## site.yaml (마케터)

```yaml
key: grit
name: 그릿서비스
site: https://gritservice.co.kr/
phone: 1577-0412
tel: "15770412"
kakao: https://pf.kakao.com/_UExgxaX
blog: https://blog.naver.com/grit_service
address: 경기도 파주시 교하로 1312-53, 1동 1층
brand_color: "#004a9f"
logo: assets/grit-service-logo.png
regions: [파주, 운정, 교하, 금촌, 문산, 일산, 김포]
categories:
  - {key: accident, slug: accident-repair, name: 사고수리, intro: "..."}
  ...
```

## 지켜야 할 것

- 사장님 확인 전 숫자(가격, 기간, 영업시간, 대차, 누적 실적)는 쓰지 않는다. 예시 글은 `draft: true`, 차량 정보는 "예시"임이 분명해야 한다.
- 번호판·고객 얼굴은 가린 사진만.
- 사이트용 글과 블로그용 글은 문장을 다르게 쓴다(같은 사진·사실은 괜찮음).
- 로건 홈(index.php)은 라이브가 더 새 버전이라 생성기가 덮어쓰지 않는다. 로건은 /cases/ 폴더만 추가, 홈 섹션은 조각(snippet)만 제공.
- 그릿 홈은 /mnt/project-files/gritservice-site/make_grit.py 가 만든다. 홈 "최근 수리사례" 섹션과 메뉴 링크는 거기에 붙인다(기존 변경사항 유지).

## 절대 규칙 (2026-10-22 사장님)
- 우리가 쓴 마케팅 글(사례 페이지 등) 업로드본에 noindex 가 있으면 안 된다. 있으면 noindex 가 빠질 때까지 글을 고친 뒤에 올린다.
- make_cases.py 업로드 모드는 noindex 가 하나라도 나오면 실패(종료 코드 1) → make_grit.py 도 멈춤. check_cases.py K7 도 FAIL.
- draft 는 noindex 로 내보내지 않고 업로드본에서 아예 빠진다. 미리보기만 noindex 허용.
