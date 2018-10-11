Function Invoke-App {
    [CmdletBinding()]
    Param (
       [Parameter(Mandatory=$True)]
       [String]$Executable,
       [Parameter(Mandatory=$False)]
       [String]$Args,
       [Parameter(Mandatory=$False)]
       [String]$ErrLog,
       [Parameter(Mandatory=$False)]
       [String]$OutLog,
       [Parameter(Mandatory=$False)]
       [String]$LogDir,
       [Parameter(Mandatory=$False)]
       [Switch]$PrintOutput

    )

    $Env:EXITCODE = 0

    if ($Env:DEBUG -eq "1") {
        $PrintOutput = $true
    }


    if ($LogDir) {
        $msg = $Args
        $mod = $ErrLog

        $ErrLog = "$LogDir\$msg.err.log"
        $OutLog = "$LogDir\$msg.out.log"
        $Args = "install --no-cache-dir $mod"

        Write-Host "  ---- Installing $msg $Env:BUILDARCH"
    }

    if (-Not($Args)) {
        $Args = ""
    }

    if ($ErrLog) {
        $ProcessArgs = $Args
    }

    elseif ($Executable -Like '*.msi') {
        $ProcessArgs = "/I $Executable /quiet /passive /qn /norestart $Args"
        $Executable = "MsiExec.exe"
    }
    else {
        $ProcessArgs = "/VerySilent /NoRestart /NoCancel /SupressMessageBoxes /Silent $Args"
    }


    if ($ErrLog) {
        Out-File "$ErrLog" -InputObject ""
    }

    if ($OutLog) {
        Out-File "$OutLog" -InputObject ""
    }

    if ($Executable -eq 'python') {
        $Executable = "$Env:PYTHON\$Executable.exe"
    }

    if (($Executable -eq 'pip') -or ($Executable -eq 'easy_install')) {
        $Executable = "$Env:PYTHON\Scripts\$Executable.exe"
    }

    $process_info = New-Object System.Diagnostics.ProcessStartInfo
    $process_info.FileName = $Executable
    $process_info.RedirectStandardError = $true
    $process_info.RedirectStandardOutput = $true
    $process_info.UseShellExecute = $false
    $process_info.Arguments = $ProcessArgs
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $process_info
    $process.Start() | Out-Null

    $oldstdout = ""
    $oldstderr = ""

    $origpos = $host.UI.RawUI.CursorPosition
    $origpos.Y++

    $scroll = "/-\|/-\|"
    $idx = 0

    While (!(Get-Process python)) {
        Start-Sleep -Milliseconds 100
    }

    While ((Get-Process python)) {
        $host.UI.RawUI.CursorPosition = $origpos
	    Write-Host $scroll[$idx] -NoNewline
	    $idx++
	    if ($idx -ge $scroll.Length) {
		    $idx = 0
	    }

	    Start-Sleep -Milliseconds 100


        $stdout = $p.StandardOutput.ReadToEnd()
        $stderr = $p.StandardError.ReadToEnd()

        if (-Not ($oldstdout -eq $stdout)) {
            
            $diff = $stdout -replace $oldstdout, ""

            if ($PrintOutput) {
                $host.UI.RawUI.CursorPosition = $origpos
                Write-Host ' '
                Write-Host $diff
                $origpos = $host.UI.RawUI.CursorPosition
                $origpos.Y++
            }

            $oldstdout = $stdout
            
            if ($OutLog) {
                Out-File "$OutLog" -Append -InputObject $diff
            }
        }

        if (-Not ($oldstderr -eq $stderr)) {
            $diff = $stderr -replace $oldstderr, ""
            if ($PrintOutput) {
                $host.UI.RawUI.CursorPosition = $origpos
                Write-Host ' '
                Write-Host $diff
                $origpos = $host.UI.RawUI.CursorPosition
                $origpos.Y++
            }

            $oldstderr = $stderr
            
            if ($ErrLog) {
                Out-File "$ErrLog" -Append -InputObject $diff
            }
        }
    }

    $Env:EXITCODE = $process.ExitCode


    $host.UI.RawUI.CursorPosition = $origpos
    Write-Host ' '


    if ($process.ExitCode -eq 0) {
        Write-Host "       Done."
        $host.SetShouldExit(0)
    } else {
        Write-Host "       Failed."
        if ($ErrLog -and (-Not($PrintOutput)))  {
            Write-Host " "
            Write-Host "******************* ERROR LOG ***********************"
            Write-Host " "
            Get-Content -Path "$ErrLog"
            Write-Host " "
            Write-Host " "
            Write-Host "******************* OUTPUT LOG ***********************"
            Write-Host " "
            Get-Content -Path "$OutLog"
        }
        $host.SetShouldExit(1)
        exit
    }
}

