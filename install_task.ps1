$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$(Get-Location)\bot_silent.vbs`"" -WorkingDirectory (Get-Location)
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 365)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName "PokeBot Daily" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "PokeBot Discord - Trivia y Verificacion" -Force
Write-Host "Tarea programada creada. El bot se iniciara automaticamente al iniciar sesion."
