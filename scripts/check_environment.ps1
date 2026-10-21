<#
.SYNOPSIS
  Ollama 한국어 번역 환경 점검 (Python, 가상환경, GPU, Ollama 서버, 설치 모델, API 연결).
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\check_environment.ps1
  powershell -ExecutionPolicy Bypass -File scripts\check_environment.ps1 -Project projects\mygame -TestChat
#>
param(
    [string]$Project = "examples\ollama_ko_scene",
    [string]$Endpoint = "",
    [switch]$TestChat
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Root = Split-Path -Parent $PSScriptRoot
# 사용자가 지정한 상대 경로는 현재 폴더 기준, 기본값은 저장소 기준으로 해석한다.
$baseDir = if ($PSBoundParameters.ContainsKey("Project")) { (Get-Location).Path } else { $Root }
$Project = [IO.Path]::GetFullPath([IO.Path]::Combine($baseDir, $Project))
Set-Location $Root
$script:Failures = 0

function Report([string]$Level, [string]$Message) {
    $color = @{ OK = "Green"; WARN = "Yellow"; FAIL = "Red"; INFO = "Gray" }[$Level]
    Write-Host ("[{0}] {1}" -f $Level, $Message) -ForegroundColor $color
    if ($Level -eq "FAIL") { $script:Failures++ }
}

function Read-ConfigValue([string]$Path, [string]$Key) {
    # 단순한 "key: value" 줄만 읽는다. 주석과 따옴표는 제거한다.
    if (-not (Test-Path $Path)) { return "" }
    foreach ($line in Get-Content -LiteralPath $Path -Encoding UTF8) {
        if ($line -match "^\s*$([regex]::Escape($Key)):\s*(.*)$") {
            return (($Matches[1] -replace "\s+#.*$", "").Trim().Trim('"').Trim("'"))
        }
    }
    return ""
}

Report INFO ("Windows {0}, PowerShell {1}" -f [Environment]::OSVersion.Version, $PSVersionTable.PSVersion)

# Python 3.11
try {
    $py = (& py -3.11 --version) 2>&1
    if ($LASTEXITCODE -eq 0) { Report OK "Python: $py" } else { Report FAIL "Python 3.11이 없습니다 (py -3.11 실패). python.org에서 3.11 설치" }
} catch { Report FAIL "Python Launcher(py)가 없습니다. Python 3.11을 'py launcher' 포함으로 설치" }

if (Test-Path ".venv\Scripts\python.exe") {
    & .venv\Scripts\python.exe -c "import httpx, yaml, orjson" 2>$null
    if ($LASTEXITCODE -eq 0) { Report OK "가상환경 .venv 및 의존성 확인" } else { Report WARN ".venv 의존성 누락: setup_ollama_ko.cmd 실행" }
} else { Report WARN ".venv 없음: 처음 실행 시 setup_ollama_ko.cmd가 자동으로 설치합니다" }

# GPU
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    $gpu = & nvidia-smi --query-gpu=name,memory.used,memory.total,driver_version --format=csv,noheader
    Report OK "GPU: $gpu"
} else { Report WARN "nvidia-smi를 찾지 못했습니다. NVIDIA 드라이버 확인 (CPU만으로도 동작하지만 매우 느림)" }

# 프로젝트 설정
$configPath = Join-Path $Project "config.yaml"
if (Test-Path $configPath) { Report OK "설정 파일: $configPath" } else { Report FAIL "설정 파일 없음: $configPath (run_ollama_ko.py --init 으로 생성)" }
$model = Read-ConfigValue $configPath "model"
$numCtx = Read-ConfigValue $configPath "numCtx"
if (-not $Endpoint) { $Endpoint = Read-ConfigValue $configPath "endpoint" }
if (-not $Endpoint) { $Endpoint = "http://127.0.0.1:11434" }
$base = ($Endpoint.TrimEnd("/") -replace "/(v1/chat/completions|api/chat|v1|api)$", "")
$inputDir = Join-Path $Project "gt_input"
if (Test-Path $inputDir) {
    $count = @(Get-ChildItem -LiteralPath $inputDir -File -Recurse).Count
    if ($count -gt 0) { Report OK "입력 파일 $count 개: $inputDir" } else { Report WARN "입력 폴더가 비어 있습니다: $inputDir" }
}

# Ollama 서버와 모델
try {
    $version = Invoke-RestMethod -Uri "$base/api/version" -TimeoutSec 5
    Report OK "Ollama 서버 $base (버전 $($version.version))"
    $tags = Invoke-RestMethod -Uri "$base/api/tags" -TimeoutSec 10
    $names = @($tags.models | ForEach-Object { $_.name })
    if ($names.Count -eq 0) { Report FAIL "설치된 모델이 없습니다 (ollama pull 또는 ollama create 필요)" }
    foreach ($m in $tags.models) {
        $gb = [math]::Round($m.size / 1GB, 1)
        Report INFO ("  모델 {0}  {1} GB  {2}" -f $m.name, $gb, $m.details.parameter_size)
    }
    if (-not $model) { Report FAIL "config.yaml의 model이 비어 있습니다. 위 목록의 이름 하나를 입력하세요" }
    elseif ($names -contains $model -or $names -contains "$model`:latest") { Report OK "설정 모델 '$model' 설치됨" }
    else { Report FAIL "설정 모델 '$model'이 설치 목록에 없습니다 (이름과 태그 확인)" }
    try {
        $null = Invoke-RestMethod -Uri "$base/v1/models" -TimeoutSec 5
        Report OK "OpenAI 호환 API $base/v1 응답"
    } catch { Report WARN "OpenAI 호환 API /v1 응답 없음 (native 모드는 영향 없음)" }
} catch {
    Report FAIL "Ollama 서버 $base 에 연결할 수 없습니다. Ollama 앱 실행 또는 'ollama serve' 확인"
}

if ($TestChat -and $model -and $script:Failures -eq 0) {
    $ctx = 8192
    if ($numCtx) { $ctx = [int]$numCtx }
    $body = @{
        model = $model; stream = $false; think = $false
        options = @{ temperature = 0.2; num_ctx = $ctx; num_predict = 128 }
        messages = @(@{ role = "user"; content = "다음 일본어를 한국어로 번역해 한 줄로만 답하세요: 雨の駅で、彼女を待っていた。" })
    } | ConvertTo-Json -Depth 5
    try {
        $sw = [Diagnostics.Stopwatch]::StartNew()
        $answer = Invoke-RestMethod -Uri "$base/api/chat" -Method Post -ContentType "application/json; charset=utf-8" `
            -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 600
        $sw.Stop()
        Report OK ("번역 시험 {0:N1}초, 입력 토큰 {1}, 출력 토큰 {2}: {3}" -f $sw.Elapsed.TotalSeconds,
            $answer.prompt_eval_count, $answer.eval_count, $answer.message.content.Trim())
    } catch {
        # 오래된 Ollama는 think 파라미터를 거부할 수 있다.
        Report FAIL "번역 시험 실패: $($_.Exception.Message) (구버전 Ollama라면 config.yaml의 think를 null로)"
    }
    try {
        $ps = Invoke-RestMethod -Uri "$base/api/ps" -TimeoutSec 5
        foreach ($m in $ps.models) {
            $share = if ($m.size) { [math]::Round(100 * $m.size_vram / $m.size) } else { 0 }
            Report INFO ("  적재 {0}: 전체 {1:N1} GB 중 GPU {2}% (나머지는 시스템 RAM/CPU)" -f $m.name, ($m.size / 1GB), $share)
        }
    } catch { }
}

if ($script:Failures -gt 0) { Write-Host "점검 실패 $($script:Failures)건" -ForegroundColor Red; exit 1 }
Write-Host "환경 점검 완료" -ForegroundColor Green
exit 0
