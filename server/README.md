# 서버 설정 파일 (자동 업로드 대상 아님)
.htaccess 는 잘못되면 사이트 전체가 안 열릴 수 있어 자동 업로드(deploy/)에 넣지 않았습니다. 사장님이 FTP(WinSCP)로 한 번만 손으로 올립니다.
- grit.htaccess → /public_html/gritservice/.htaccess
- logan.htaccess → /public_html/.htaccess (기존 파일이 있으면 맨 위에 붙이기)
각 파일 맨 위의 '올린 직후 확인' 주소를 열어 보고, 이상하면 보관한 원래 파일로 되돌리면 됩니다.
