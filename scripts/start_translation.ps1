<#
.SYNOPSIS
  일본어 장면 TXT를 로컬 Ollama로 한국어 번역합니다. 중단 후 같은 명령으로 이어서 실행됩니다.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\start_translation.ps1 -Project projects\mygame -Init
  powershell -ExecutionPolicy Bypass -File scripts\start_translation.ps1 -Project projects\mygame
  powershell -ExecutionPolicy Bypass -File scripts\start_translation.ps1 -Project projects\mygame -CheckOnly
#>
param(
    [string]$Project = "examples\ollama_ko_scene",
    [switch]$Init,
    [switch]$CheckOnly,
    [switch]$NoCheck
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$Root = Split-Path -Parent $PSScriptRoot
# 사용자가 지정한 상대 경로는 현재 폴더 기준, 기본값은 저장소 기준으로 해석한다.
$baseDir = if ($PSBoundParameters.ContainsKey("Project")) { (Get-Location).Path } else { $Root }
$Project = [IO.Path]::GetFullPath([IO.Path]::Combine($baseDir, $Project))
Set-Location $Root
$python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "처음 실행: Python 가상환경과 의존성을 설치합니다..."
    & cmd /c "`"$Root\setup_ollama_ko.cmd`""
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

if ($CheckOnly) {
    & $python (Join-Path $Root "check_ollama_ko.py") $Project
    exit $LASTEXITCODE
}

$arguments = @((Join-Path $Root "run_ollama_ko.py"), $Project)
if ($Init) { $arguments += "--init" }
if ($NoCheck) { $arguments += "--no-check" }
& $python @arguments
$code = $LASTEXITCODE
switch ($code) {
    0 { Write-Host "완료" -ForegroundColor Green }
    2 { Write-Host "번역은 끝났지만 품질 검사에서 치명적 오류가 있습니다. 같은 명령으로 다시 실행하면 해당 줄만 재번역합니다." -ForegroundColor Yellow }
    default { Write-Host "실패. 같은 명령으로 다시 실행하면 저장된 번역 이후부터 이어서 진행합니다." -ForegroundColor Red }
}
exit $code
