<#
.SYNOPSIS
  Registers (or removes) a per-user Task Scheduler task that runs one executive
  watcher sweep every 5 minutes. No administrator rights required.
.EXAMPLE
  .\install-executive-watcher.ps1            # install or update
  .\install-executive-watcher.ps1 -Uninstall # remove
#>
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [int]$IntervalMinutes = 5,
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$TaskName = "AgentOS Executive Watcher"
$RepoRoot = Split-Path -Parent $PSScriptRoot

if ($Uninstall) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed task '$TaskName'."
    } else {
        Write-Host "Task '$TaskName' is not installed."
    }
    return
}

$agent = Join-Path $RepoRoot "agent.py"
if (-not (Test-Path $agent)) { throw "agent.py not found at $agent" }

$action = New-ScheduledTaskAction -Execute $Python `
    -Argument "`"$agent`" executive watch --once" -WorkingDirectory $RepoRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 4)
# Current user, interactive token only: runs without elevation.
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive -RunLevel Limited

# Register-ScheduledTask -Force replaces an existing task, so re-running is idempotent.
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "Installed task '$TaskName': python $agent executive watch --once every $IntervalMinutes minutes."
