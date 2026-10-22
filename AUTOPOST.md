# 블로그 → 사이트 자동 게시 (2026-10-22, 사장님 "PC에서 완전 자동 업로드" 선택)

## 흐름
1. 매일 아침(클라우드 예약 작업): 두 네이버 블로그 새 글 확인
   - 그릿 blog.naver.com/grit_service (Uplika 워크스페이스 ws_e132b2bb6ee06642)
   - 로건 blog.naver.com/logan_service (Uplika 워크스페이스 ws_5a0f1fc1aec90792)
   - 이미 옮긴 글: `src/cases-system/photo-sources.txt` 와 posts/*.yaml 의 `source:`
2. 새 글을 `src/cases-system/CONVERT.md` 규칙으로 posts/{slug}.yaml 작성 (draft: false, source, photos_pending: true)
   - 차량 수리 사례가 아닌 글(공지·이벤트·안내)은 건너뜀
   - 가격·기간·대차·할인·최고 표현 금지, 사실은 블로그에 있는 것만
3. `bash build.sh` — 검사(noindex·금지어·링크·JSON-LD) 통과해야만 deploy/ 갱신. 실패하면 커밋하지 않음
4. 커밋·푸시 (main)
5. 사장님 PC(작업 스케줄러, 1시간마다): `pc/autopost-upload.ps1` 이 바뀐 deploy/ 파일만 FTP 업로드
   - deploy/grit/ → /public_html/gritservice/
   - deploy/logan/ → /public_html/

## 절대 규칙
- 올라가는 파일에 noindex 금지 (build.sh 가 발견하면 중단)
- 블로그는 읽기만. Uplika publish/update/delete 쓰지 않음
- FTP 비밀번호는 PC 의 WinSCP 저장 사이트에만. 저장소·대화에 적지 않음
- 사이트 디자인·코드 변경은 src/ 에서 하고 build.sh 로 반영 (deploy/ 직접 수정 금지)
