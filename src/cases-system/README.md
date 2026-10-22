# 수리사례 포스팅 시스템 (그릿서비스 · 로건서비스)

2026-10-22 만듦. 오토밴스(autovance.co.kr)처럼 "수리 한 건 = 페이지 한 장".
약속(형식·주소 규칙): SPEC.md / 글쓰기 규칙·키워드: grit/guide.md, logan/guide.md

## 글 올리는 순서
1. 사장님이 사진(번호판 가림, 6장 이상)과 메모(차종·연식·주행거리·증상·작업, 고객 게시 동의)를 줌
2. posts/{slug}.yaml 작성 (예시 글 3개를 본보기로), 사진은 assets/cases/ 에
3. 사장님 확인 후 `draft: false`
4. 빌드
   - 그릿: `cd ../gritservice-site && python3 make_grit.py upload` (공개 글이 1개 이상이면 메뉴 "수리사례", 홈 섹션, sitemap, llms.txt 자동 추가)
   - 로건: `cd engine && python3 make_cases.py ../logan ../build/logan-upload` → cases/ 폴더만 서버에 올림. 로건 홈(index.php)은 라이브가 더 새 버전이라 자동으로 안 바꿈: 메뉴 링크와 cases/home-section.html 조각은 손으로 붙이고, sitemap-cases.xml 은 서치어드바이저·서치콘솔에 따로 제출
5. 검사: `python3 engine/check_cases.py <출력폴더> <site.yaml>` FAIL 0 이어야 올림
6. 미리보기(예시 포함): `GRIT_CASES_PREVIEW=1 python3 make_grit.py ../cases-system/build/grit-preview-full`, 로건은 `--preview --copy-assets`

## 지금 상태
- 글은 모두 예시(draft). 업로드본에는 아무것도 안 붙음(빈 목록 페이지는 검색에 손해라 만들지 않음).
- 같은 사례의 블로그 글은 문장을 새로 써서 사이트 발행 1~3일 뒤에.
