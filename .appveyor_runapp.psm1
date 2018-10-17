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

    $Redirect = $true

    if ($ErrLog) {
        $ProcessArgs = $Args

    }
    elseif (!Not ($Args -Like "*--build*")) {
        if ($Executable -Like "*.msi") {
            $ProcessArgs = "/I $Executable /quiet /passive /qn /norestart $Args"
            $Executable = "MsiExec.exe"
        } else {
            $ProcessArgs = "/VerySilent /NoRestart /NoCancel /SupressMessageBoxes /Silent $Args"
        }
    }
    else {
        $ProcessArgs = $Args
        $Redirect = $false
    }


    $process_info = New-Object System.Diagnostics.ProcessStartInfo
    $process_info.FileName = $Executable
    $process_info.RedirectStandardError = $Redirect
    $process_info.RedirectStandardOutput = $Redirect
    $process_info.UseShellExecute = $false
    $process_info.Arguments = $ProcessArgs
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $process_info
    $process.Start() | Out-Null

    if ($Redirect) {
        if ($ErrLog) {
            Out-File "$ErrLog" -Encoding utf8 -InputObject ""
        }

        if ($OutLog) {
            Out-File "$OutLog" -Encoding utf8 -InputObject ""
        }
    }

    Function Print-Logs ($p, $ot_log, $er_log, $prnt) {
        $o_log = $p.StandardOutput.ReadToEnd()
        $e_log = $p.StandardError.ReadToEnd()
        if (-Not ($prnt)) {
            $prnt = $Env:DEBUG -eq "1"
        }

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
        if ($Redirect) {
            Print-Logs $process $OutLog $ErrLog $PrintOutput
        }
    }
    if ($Redirect) {
        Print-Logs $process $OutLog $ErrLog $PrintOutput
    }

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

