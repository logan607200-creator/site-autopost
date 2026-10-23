# 저장소에 새로 바뀐 deploy/ 파일만 FTP 로 서버에 올린다. (작업 스케줄러가 1시간마다 실행)
# FTP 접속 정보는 WinSCP 에 저장한 사이트 이름(아래 $Site)으로만 쓴다. 비밀번호는 이 파일에 적지 않는다.
$ErrorActionPreference = "Stop"
$Repo   = "C:\site-autopost"
$Site   = "ivy-ftp"          # WinSCP 에 저장한 사이트 이름
# 컴퓨터마다 저장한 이름이 다르면 .site-name 파일(한 줄)에 적어 둔 이름을 쓴다
$SiteFile = Join-Path $Repo ".site-name"
if (Test-Path $SiteFile) { $n = (Get-Content $SiteFile -Raw -Encoding UTF8).Trim(); if ($n) { $Site = $n } }
# WinSCP 는 설치 방식에 따라 위치가 다르다(winget 은 사용자 폴더에 설치)
$WinScp = @("C:\Program Files (x86)\WinSCP\WinSCP.com", "C:\Program Files\WinSCP\WinSCP.com",
            (Join-Path $env:LOCALAPPDATA "Programs\WinSCP\WinSCP.com")) | Where-Object { Test-Path $_ } | Select-Object -First 1
# 막 설치한 직후 등 PATH 에 git 이 없으면 기본 설치 위치를 붙인다
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
  $env:Path += ";C:\Program Files\Git\cmd;" + (Join-Path $env:LOCALAPPDATA "Programs\Git\cmd")
}
$Log    = Join-Path $Repo "upload-log.txt"
$State  = Join-Path $Repo ".last-uploaded"
$Remote = @{ "deploy/grit/" = "/public_html/gritservice/"; "deploy/logan/" = "/public_html/" }

function Log($m) { Add-Content -Path $Log -Value ("{0:yyyy-MM-dd HH:mm} {1}" -f (Get-Date), $m) -Encoding UTF8 }

Set-Location $Repo
git pull --ff-only --quiet
# git 은 실패해도 PowerShell 오류로 멈추지 않으므로 종료 코드를 직접 본다
if ($LASTEXITCODE -ne 0) { Log "실패: git pull (저장소 충돌 또는 네트워크)"; exit 1 }
$new = (git rev-parse HEAD).Trim()
$old = if (Test-Path $State) { (Get-Content $State -Raw).Trim() } else { "" }
if ($old -eq $new) { exit 0 }

# 처음 실행이면 deploy/ 전체, 아니면 지난번 올린 뒤 바뀐 것만
# 이름이 바뀐 파일은 "새 파일 추가 + 옛 파일 삭제"로 본다(--no-renames)
$gone = @()
if ($old) {
  $files = @(git -c core.quotepath=off diff --no-renames --name-only --diff-filter=ACM $old $new -- deploy/)
  $gone  = @(git -c core.quotepath=off diff --no-renames --name-only --diff-filter=D $old $new -- deploy/)
} else {
  $files = @(git -c core.quotepath=off ls-files -- deploy/)
}
if (-not $files -and -not $gone) { Set-Content $State $new; exit 0 }

# 접속에 실패하면 바로 멈추고, 접속되면 OPEN-OK 를 찍은 뒤 나머지는 오류가 나도 계속
$lines = @("option batch abort", "option confirm off", "open `"$Site`"", "echo OPEN-OK", "option batch continue")
$dirs = @{}
foreach ($f in $files) {
  foreach ($k in $Remote.Keys) {
    if ($f.StartsWith($k)) {
      $rel = $f.Substring($k.Length)
      $dst = $Remote[$k] + $rel
      $d = $dst.Substring(0, $dst.LastIndexOf("/"))
      # 폴더가 없으면 만든다(있으면 오류를 무시)
      $parts = $d.Trim("/").Split("/"); $acc = ""
      foreach ($p in $parts) { $acc += "/" + $p; if (-not $dirs[$acc]) { $lines += "mkdir `"$acc`""; $dirs[$acc] = 1 } }
      $src = Join-Path $Repo ($f -replace "/", "\")
      $lines += "put -nopermissions -nopreservetime `"$src`" `"$dst`""
    }
  }
}
# 저장소에서 지운 페이지는 서버에서도 지운다(옛 주소가 계속 살아 있지 않게)
foreach ($f in $gone) {
  foreach ($k in $Remote.Keys) {
    if ($f.StartsWith($k)) { $lines += "rm `"" + $Remote[$k] + $f.Substring($k.Length) + "`"" }
  }
}
$lines += "exit"
$script = Join-Path $env:TEMP "autopost-winscp.txt"
Set-Content -Path $script -Value $lines -Encoding UTF8
$out = & $WinScp /script="$script" /log="$Repo\winscp-last.log" | Out-String
$opened = $out -match "OPEN-OK"
$putErrors = Select-String -Path "$Repo\winscp-last.log" -Pattern "Error transferring|Access denied|Connection failed|Authentication failed" -Quiet
if ($opened -and ($LASTEXITCODE -eq 0 -or -not $putErrors)) {
  Set-Content $State $new
  Log ("올림 {0}개, 지움 {1}개 ({2})" -f $files.Count, $gone.Count, $new.Substring(0,7))
  # 검색엔진(네이버·빙)에 바뀐 페이지 알리기(IndexNow). 실패해도 업로드 결과에는 영향 없음
  $Key = "0d5b85b24fd3f3b1750da89666d9a379"
  $Hosts = @{ "deploy/grit/" = "gritservice.co.kr"; "deploy/logan/" = "loganservice.co.kr" }
  foreach ($k in $Hosts.Keys) {
    $h = $Hosts[$k]
    $urls = @($files | Where-Object { $_.StartsWith($k) -and $_ -match "\.(html|php)$" -and $_ -notmatch "404\.html$" } |
      ForEach-Object { "https://$h/" + ($_.Substring($k.Length) -replace "(^|/)index\.(html|php)$", '$1') })
    if (-not $urls) { continue }
    $body = @{ host = $h; key = $Key; keyLocation = "https://$h/$Key.txt"; urlList = $urls } | ConvertTo-Json
    foreach ($ep in @("https://searchadvisor.naver.com/indexnow", "https://api.indexnow.org/indexnow")) {
      try { Invoke-RestMethod -Uri $ep -Method Post -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 20 | Out-Null; Log ("IndexNow {0} {1}개 → {2}" -f $h, $urls.Count, $ep) }
      catch { Log ("IndexNow 실패 {0} ({1})" -f $h, $_.Exception.Message) }
    }
  }
} else {
  Log "실패: winscp-last.log 확인"
  exit 1
}
