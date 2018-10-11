﻿Function Invoke-App {
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


    $process_info = New-Object System.Diagnostics.ProcessStartInfo
    $process_info.FileName = $Executable
    $process_info.RedirectStandardError = $true
    $process_info.RedirectStandardOutput = $true
    $process_info.UseShellExecute = $false
    $process_info.Arguments = $ProcessArgs
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $process_info
    $process.Start() | Out-Null

    
    if ($ErrLog) {
        Out-File "$ErrLog" -Encoding utf8 -InputObject ""
    }

    if ($OutLog) {
        Out-File "$OutLog" -Encoding utf8 -InputObject ""
    }

    Function Print-Logs ($p, $ot_log, $er_log) {
        $o_log = $p.StandardOutput.ReadToEnd()
        $e_log = $p.StandardError.ReadToEnd()
        $prnt = $Env:DEBUG -eq "1"

        if ($o_log) {
            if ($ot_log) {
                Out-File "$ot_log" -Encoding utf8 -Append -InputObject $o_log
            }
            if ($prnt) {
                Write-Host $o_log
            }
        }

        if ($e_log) {
            if ($er_log) {
                Out-File "$er_log" -Encoding utf8 -Append -InputObject $e_log
            }
            if ($prnt) {
                Write-Host $e_log
            }
        }

    }


    while (-Not ($process.HasExited)) {
        Start-Sleep -Milliseconds 100
        Print-Logs $process $OutLog $ErrLog
    }

    Print-Logs $process $OutLog $ErrLog

    $Env:EXITCODE = $process.ExitCode
     

    if ($process.ExitCode -eq 0) {
        Write-Host "       Done."
        $host.SetShouldExit(0)
    } else {
        Write-Host "       Failed."

        if ($ErrLog -and (-Not($Env:DEBUG -eq "1")))  {
            Write-Host " "
            Write-Host "******************* ERROR LOG ***********************"
            Write-Host " "
            Get-Content  -Path $ErrLog -Encoding UTF8
            Write-Host " "
            Write-Host " "
            Write-Host "******************* OUTPUT LOG ***********************"
            Write-Host " "
            Get-Content -Path $OutLog -Encoding UTF8 
        }
        $host.SetShouldExit(1)
        exit
    }
}

