# Generate speech from custom text.
# Usage: .\run-generate.ps1 "Your text here" [-Output output.wav] [-PromptAudio prompt.wav] [-PromptText "transcript"]

param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Text,

    [string]$Output = "generated.wav",

    [string]$PromptAudio,

    [string]$PromptText
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    Write-Host "Copy .env.example to .env and set HF_TOKEN before running." -ForegroundColor Yellow
    exit 1
}

$containerOutput = "/app/output/$Output"
$args = @("compose", "run", "--rm", "generate", "generate", "--text", $Text, "--output", $containerOutput)

if ($PromptAudio) {
    if (-not $PromptText) {
        Write-Host "Provide -PromptText when using -PromptAudio." -ForegroundColor Yellow
        exit 1
    }
    $args += @("--prompt-audio", "/app/data/$PromptAudio", "--prompt-text", $PromptText)
}

docker @args
Write-Host "Output: $PSScriptRoot\output\$Output"