$ErrorActionPreference='Stop'
try {
 Add-Type -AssemblyName System.Speech
 $inputData=[Console]::In.ReadToEnd() | ConvertFrom-Json
 $s=New-Object System.Speech.Synthesis.SpeechSynthesizer
 $names=@{en='Microsoft David Desktop';es='Microsoft Helena Desktop'}
 $available=@($s.GetInstalledVoices() | Where-Object {$_.Enabled} | ForEach-Object {$_.VoiceInfo.Name})
 if($inputData.operation -eq 'status'){
  $out=@{};foreach($lang in @('en','es')){if($available -contains $names[$lang]){$out[$lang]=$names[$lang]}}
  [Console]::Out.Write(($out | ConvertTo-Json -Compress))
 } elseif($inputData.operation -eq 'synthesize' -and $inputData.language -in @('en','es') -and $inputData.text.Length -le 3500 -and $inputData.rate -ge -3 -and $inputData.rate -le 3){
  $s.SelectVoice($names[$inputData.language]);$s.Rate=[int]$inputData.rate
  $memory=New-Object IO.MemoryStream
  $format=New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000,[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,[System.Speech.AudioFormat.AudioChannel]::Mono)
  $s.SetOutputToAudioStream($memory,$format)
  $s.Speak([string]$inputData.text)
  $pcm=$memory.ToArray();$memory.Dispose()
  # Build a standard PCM WAV in memory. No audio file or cloud engine is used.
  $wav=New-Object IO.MemoryStream;$writer=New-Object IO.BinaryWriter($wav)
  $writer.Write([Text.Encoding]::ASCII.GetBytes('RIFF'));$writer.Write([int](36+$pcm.Length));$writer.Write([Text.Encoding]::ASCII.GetBytes('WAVEfmt '));$writer.Write([int]16);$writer.Write([int16]1);$writer.Write([int16]1);$writer.Write([int]16000);$writer.Write([int]32000);$writer.Write([int16]2);$writer.Write([int16]16);$writer.Write([Text.Encoding]::ASCII.GetBytes('data'));$writer.Write([int]$pcm.Length);$writer.Write($pcm);$writer.Flush()
  [Console]::Out.Write((@{audio=[Convert]::ToBase64String($wav.ToArray());voice=$names[$inputData.language]} | ConvertTo-Json -Compress));$writer.Dispose();$wav.Dispose()
 } else {exit 2}
 $s.Dispose()
} catch {exit 3}