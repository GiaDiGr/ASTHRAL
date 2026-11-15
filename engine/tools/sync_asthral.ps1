<#
.SYNOPSIS
Safely checks GitHub and fast-forwards only the current branch's configured upstream.

.DESCRIPTION
Fetches without pruning remote branches. It does not switch branches, push,
reset, clean, rebase, or merge another branch. Local edits stop the update.
Before an eligible fast-forward it creates a local backup branch. Divergence
or incoming file deletions stop the update for explicit human review.
#>
[CmdletBinding()]
param(
    [switch]$FetchOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-PreSyncBackup {
    param([Parameter(Mandatory)][string]$BranchName)

    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $attempt = 0
    do {
        $suffix = if ($attempt -eq 0) { '' } else { "-$attempt" }
        $backupName = "backup/pre-sync/$BranchName/$stamp$suffix"
        & git show-ref --verify --quiet "refs/heads/$backupName"
        $exists = ($LASTEXITCODE -eq 0)
        $attempt++
    } while ($exists)

    & git branch $backupName HEAD
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudo crear la rama local de respaldo $backupName."
    }
    return $backupName
}

$rootOutput = & git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0 -or -not $rootOutput) {
    Write-Host 'ERROR: abre PowerShell dentro de una carpeta del repositorio ASTHRAL.'
    $global:LASTEXITCODE = 2
    return
}

$repoRoot = ($rootOutput | Select-Object -First 1).Trim()
Push-Location -LiteralPath $repoRoot
try {
    $branch = (& git branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $branch) {
        Write-Host 'ERROR: no hay una rama local seleccionada. No se cambió ningún archivo.'
        $global:LASTEXITCODE = 2
        return
    }

    $upstream = (& git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>$null)
    if ($LASTEXITCODE -ne 0 -or -not $upstream) {
        Write-Host "ERROR: la rama '$branch' no tiene una rama remota configurada. No se cambió ningún archivo."
        $global:LASTEXITCODE = 2
        return
    }
    $upstream = $upstream.Trim()

    $remote = (& git config --get "branch.$branch.remote")
    if ($LASTEXITCODE -ne 0 -or -not $remote -or $remote -eq '.') {
        Write-Host "ERROR: no se pudo identificar el remoto de '$upstream'. No se cambió ningún archivo."
        $global:LASTEXITCODE = 2
        return
    }
    $remote = $remote.Trim()

    Write-Host "Revisando '$upstream' para la rama actual '$branch'."
    & git fetch --no-tags $remote
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: falló la consulta del remoto '$remote'. La rama local no se actualizó."
        $global:LASTEXITCODE = 1
        return
    }

    if ($FetchOnly) {
        Write-Host 'Consulta terminada. No se movió la rama local ni se modificó la carpeta de trabajo.'
        $global:LASTEXITCODE = 0
        return
    }

    $localChanges = @(& git status --porcelain --untracked-files=all)
    if ($localChanges.Count -gt 0) {
        Write-Host 'Hay cambios locales o archivos sin seguimiento. No se actualizó la rama; consérvalos y haz un commit revisado antes de sincronizar:'
        $localChanges | ForEach-Object { Write-Host "  $_" }
        $global:LASTEXITCODE = 2
        return
    }

    $counts = (& git rev-list --left-right --count "HEAD...$upstream")
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: no se pudo comparar HEAD con '$upstream'. No se cambió ningún archivo."
        $global:LASTEXITCODE = 1
        return
    }
    $parts = $counts.Trim() -split '\s+'
    if ($parts.Count -ne 2) {
        Write-Host 'ERROR: Git devolvió un conteo de commits inesperado. No se cambió ningún archivo.'
        $global:LASTEXITCODE = 1
        return
    }
    $ahead = [int]$parts[0]
    $behind = [int]$parts[1]

    if ($ahead -eq 0 -and $behind -eq 0) {
        Write-Host "'$branch' ya está al día con '$upstream'."
        $global:LASTEXITCODE = 0
        return
    }
    if ($ahead -gt 0 -and $behind -eq 0) {
        Write-Host "La computadora tiene $ahead commit(s) local(es) que aún no están en '$upstream'. Se conservaron y no se hizo push."
        $global:LASTEXITCODE = 0
        return
    }
    if ($ahead -gt 0 -and $behind -gt 0) {
        $backupName = New-PreSyncBackup -BranchName $branch
        Write-Warning "Las ramas divergieron. Se conservaron los commits locales en '$backupName'; revisa y combina los avances manualmente."
        $global:LASTEXITCODE = 3
        return
    }

    $incomingDeletes = @(& git diff --name-only --diff-filter=D HEAD $upstream)
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'ERROR: no se pudieron revisar las eliminaciones entrantes. No se cambió ningún archivo.'
        $global:LASTEXITCODE = 1
        return
    }
    if ($incomingDeletes.Count -gt 0) {
        $backupName = New-PreSyncBackup -BranchName $branch
        Write-Warning "'$upstream' incluye archivos eliminados. No se aplicó esa actualización. El estado local quedó respaldado en '$backupName'; revisa estos archivos antes de decidir:"
        $incomingDeletes | ForEach-Object { Write-Host "  $_" }
        $global:LASTEXITCODE = 3
        return
    }

    $backupName = New-PreSyncBackup -BranchName $branch
    & git merge --ff-only $upstream
    if ($LASTEXITCODE -ne 0) {
        Write-Error "No se completó el avance rápido. El estado anterior sigue respaldado en '$backupName'."
        $global:LASTEXITCODE = 1
        return
    }

    Write-Host "Rama actualizada desde '$upstream'. El estado anterior se conserva en '$backupName'."
    & git status --short --branch
    $global:LASTEXITCODE = 0
}
catch {
    Write-Host "ERROR: $_"
    $global:LASTEXITCODE = 1
}
finally {
    Pop-Location
}
