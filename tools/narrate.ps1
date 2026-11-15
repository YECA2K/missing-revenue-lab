param(
    [Parameter(Mandatory = $true)][string]$ScriptPath,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)
# Optional Windows-only media tooling. It does not change system speech settings.
Add-Type -AssemblyName System.Speech
$scenes = Get-Content -LiteralPath $ScriptPath -Raw -Encoding UTF8 | ConvertFrom-Json
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $synthesizer.SelectVoice('Microsoft Hazel Desktop')
    $synthesizer.Rate = 0
    for ($index = 0; $index -lt $scenes.Count; $index++) {
        $destination = Join-Path $OutputDirectory ('scene-{0:D2}.wav' -f ($index + 1))
        $synthesizer.SetOutputToWaveFile($destination)
        $synthesizer.Speak($scenes[$index].narration)
        $synthesizer.SetOutputToNull()
    }
} finally {
    $synthesizer.Dispose()
}
