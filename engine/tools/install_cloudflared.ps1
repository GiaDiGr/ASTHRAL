# Official Cloudflare Windows x64 release, pinned and Authenticode checked.
$ErrorActionPreference = 'Stop'
$project = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$folder = Join-Path $project 'work/cloudflare'
New-Item -ItemType Directory -Force -Path $folder | Out-Null
$target = Join-Path $folder 'cloudflared.exe'
$expected = 'd5c1d82031da6253dcdcff64c944cd0fe063016edeb2e4fd088075fc9bd52d0a'
if (!(Test-Path -LiteralPath $target)) {
    $temporary = Join-Path $folder 'cloudflared.download.exe'
    Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/download/2026.11.0/cloudflared-windows-amd64.exe' -OutFile $temporary
    if ((Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
        throw 'Official release checksum mismatch. Download was not installed.'
    }
    $signature = Get-AuthenticodeSignature -LiteralPath $temporary
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O="Cloudflare, Inc\."') {
        throw 'Cloudflare Authenticode signature verification failed.'
    }
    Move-Item -LiteralPath $temporary -Destination $target
}
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Installed cloudflared checksum mismatch.'
}
$signature = Get-AuthenticodeSignature -LiteralPath $target
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O="Cloudflare, Inc\."') {
    throw 'Installed cloudflared signature is invalid.'
}
& $target --version
