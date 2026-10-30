<#
.SYNOPSIS
  One command to install (if needed), check, and open Shopping in the Agent OS Executive window.

.DESCRIPTION
  Safe to run every day. It never deletes data, never enables paid sources and never turns on purchasing.
    1. Finds Python 3.11+ (the "py" launcher or "python").
    2. Uses a private virtual environment (default: %LOCALAPPDATA%\AgentOS\venv) and installs these
       checkouts into it only when they are missing: personal-agent-os, agent-os-shopping, ingester-engine.
    3. Creates the Shopping data folder if it does not exist (real data: %USERPROFILE%\.agent-os-shopping,
       demo data: %USERPROFILE%\.agent-os-shopping-demo; the two never mix).
    4. On first run, turns on the free keyless sources (agent-shopping stores add-free).
    5. Runs agent-shopping doctor and prints anything you need to do.
    6. Starts the Executive window and opens it on the Shopping tab.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\Start-Shopping.ps1
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\Start-Shopping.ps1 -Demo
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\Start-Shopping.ps1 -InstallWatchTask   # check prices every 2 hours
#>
[CmdletBinding()]
param(
  [string]$AgentOsPath = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
  [string]$ShoppingPath = '',
  [string]$IngesterPath = '',
  [string]$VenvPath = (Join-Path $env:LOCALAPPDATA 'AgentOS\venv'),
  [switch]$Demo,
  [switch]$Reinstall,
  [switch]$InstallWatchTask,
  [switch]$NoBrowser,
  [int]$Port = 8770
)
$ErrorActionPreference = 'Stop'

function Say($text) { Write-Host "[shopping] $text" }
function Fail($text) { Write-Host "[shopping] STOPPED: $text" -ForegroundColor Red; exit 1 }

function Find-Sibling($name, $given) {
  if ($given) { if (Test-Path (Join-Path $given 'pyproject.toml')) { return (Resolve-Path $given).Path } else { Fail "$given is not a $name checkout" } }
  foreach ($base in @((Split-Path $AgentOsPath -Parent), (Split-Path (Split-Path $AgentOsPath -Parent) -Parent))) {
    $candidate = Join-Path $base $name
    if (Test-Path (Join-Path $candidate 'pyproject.toml')) { return (Resolve-Path $candidate).Path }
  }
  return $null
}

# 1. Python ------------------------------------------------------------------------------------------
$basePython = $null
foreach ($cmd in @(@('py', '-3'), @('python'))) {
  try {
    $exe = $cmd[0]; $rest = @($cmd | Select-Object -Skip 1)
    $version = & $exe @rest -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
    if ($LASTEXITCODE -eq 0 -and [version]$version -ge [version]'3.11') { $basePython = $cmd; break }
  } catch { }
}
if (-not $basePython) { Fail 'Python 3.11 or newer was not found. Install it from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), then run this again.' }
Say "Python $version found"

# 2. Checkouts and virtual environment ---------------------------------------------------------------
$shopping = Find-Sibling 'agent-os-shopping' $ShoppingPath
if (-not $shopping) { Fail "agent-os-shopping was not found next to $AgentOsPath. Run: git clone https://github.com/unwit1/agent-os-shopping `"$(Join-Path (Split-Path $AgentOsPath -Parent) 'agent-os-shopping')`"" }
$ingester = Find-Sibling 'ingester-engine' $IngesterPath
if (-not $ingester) { Fail "ingester-engine (needed by Agent OS) was not found. Run: git clone https://github.com/unwit1/ingester-engine `"$(Join-Path (Split-Path $AgentOsPath -Parent) 'ingester-engine')`"" }

$python = Join-Path $VenvPath 'Scripts\python.exe'
if (-not (Test-Path $python)) {
  Say "Creating a private Python environment in $VenvPath"
  $exe = $basePython[0]; $rest = @($basePython | Select-Object -Skip 1)
  & $exe @rest -m venv $VenvPath
  if ($LASTEXITCODE -ne 0) { Fail 'Could not create the virtual environment.' }
}
$missing = & $python -c "import importlib.util as u; print(' '.join(m for m in ('agent_os','agent_shopping','ingester_engine') if u.find_spec(m) is None))"
if ($Reinstall -or $missing) {
  Say "Installing: $(if ($Reinstall) { 'everything (reinstall)' } else { $missing })"
  & $python -m pip install --disable-pip-version-check -q -e $ingester -e $shopping -e $AgentOsPath
  if ($LASTEXITCODE -ne 0) { Fail 'pip install failed. The error is printed above.' }
}

# 3. Data folder and mode ----------------------------------------------------------------------------
$shopCli = @($python, '-c', 'import sys; from agent_shopping.cli import main; sys.exit(main())')
$cmdParts = @($shopCli)
if ($Demo) {
  $env:AGENT_SHOPPING_HOME = Join-Path $env:USERPROFILE '.agent-os-shopping-demo'
  $cmdParts += '--demo-stores'
  Say "DEMO mode: invented stores and prices, kept in $env:AGENT_SHOPPING_HOME"
} elseif (-not $env:AGENT_SHOPPING_HOME) {
  $env:AGENT_SHOPPING_HOME = Join-Path $env:USERPROFILE '.agent-os-shopping'
}
# A JSON array survives paths with spaces; the adapter reads it without any shell quoting.
$env:AGENT_SHOPPING_CMD = ConvertTo-Json -Compress -InputObject $cmdParts
$firstRun = -not (Test-Path (Join-Path $env:AGENT_SHOPPING_HOME 'canonical'))
New-Item -ItemType Directory -Force -Path $env:AGENT_SHOPPING_HOME | Out-Null
Remove-Item Env:\LIVE_PURCHASES_ENABLED -ErrorAction SilentlyContinue   # this build is manual checkout only

# 4. Free sources on first run -------------------------------------------------------------------------
if ($firstRun -and -not $Demo) {
  Say 'First run: turning on free, keyless sources (no account, no cost)'
  & $shopCli[0] $shopCli[1] $shopCli[2] --home $env:AGENT_SHOPPING_HOME stores add-free | Out-Null
  if ($LASTEXITCODE -ne 0) { Say 'Could not turn on the free sources; the health check below says why.' }
}

# 5. Doctor ---------------------------------------------------------------------------------------------
Say 'Health check:'
$doctorArgs = @('--home', $env:AGENT_SHOPPING_HOME)
if ($Demo) { $doctorArgs += '--demo-stores' }
& $shopCli[0] $shopCli[1] $shopCli[2] @doctorArgs doctor
# exit code 1 only means "needs attention"; the window shows the same report.

# Optional: scheduled price checks ---------------------------------------------------------------------
if ($InstallWatchTask) {
  # The task runs a small .cmd file, so no quotes have to survive schtasks argument passing.
  $runner = Join-Path (Split-Path $VenvPath -Parent) $(if ($Demo) { 'shopping-watch-demo.cmd' } else { 'shopping-watch.cmd' })
  $demoFlag = if ($Demo) { ' --demo-stores' } else { '' }
  Set-Content -Path $runner -Encoding ASCII -Value @(
    '@echo off',
    "`"$python`" -c `"import sys; from agent_shopping.cli import main; sys.exit(main())`" --home `"$env:AGENT_SHOPPING_HOME`"$demoFlag watch-due"
  )
  $taskName = if ($Demo) { 'AgentOS Shopping watch (demo)' } else { 'AgentOS Shopping watch' }
  try {
    $action = New-ScheduledTaskAction -Execute $runner          # typed value: spaces in the path are fine
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 2)
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Force | Out-Null
    Say "Scheduled '$taskName' every 2 hours. Remove: Unregister-ScheduledTask -TaskName '$taskName'"
  } catch {
    Say "Could not create the scheduled task ($($_.Exception.Message)). Price checks still run when you press Run watcher now."
  }
}

# 6. Start the window ------------------------------------------------------------------------------------
$log = Join-Path $env:TEMP 'agentos-executive-window.log'
$err = Join-Path $env:TEMP 'agentos-executive-window.err.log'
Remove-Item $log, $err -ErrorAction SilentlyContinue
$proc = Start-Process -FilePath $python -ArgumentList @('-m', 'agent_os', 'executive', 'window', '--port', $Port, '--no-open') `
  -WorkingDirectory $AgentOsPath -RedirectStandardOutput $log -RedirectStandardError $err -PassThru -WindowStyle Hidden
$url = $null
for ($i = 0; $i -lt 60 -and -not $url; $i++) {
  Start-Sleep -Milliseconds 500
  if ($proc.HasExited) { Get-Content $err -ErrorAction SilentlyContinue | Write-Host; Fail 'The Executive window stopped while starting (details above).' }
  $line = Get-Content $log -ErrorAction SilentlyContinue | Where-Object { $_ -like '*executive_window*' } | Select-Object -First 1
  if ($line) { $url = ($line | ConvertFrom-Json).executive_window }
}
if (-not $url) { Fail "The Executive window did not report its address. See $err" }
try { Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 10 | Out-Null } catch { Fail "The window started but does not answer at $url" }
Say "Running at $url  (process $($proc.Id); stop it with: Stop-Process -Id $($proc.Id))"
if (-not $NoBrowser) { Start-Process "$($url)#shopping" }
Say 'Done. Shopping is open. Your data is kept between restarts.'
