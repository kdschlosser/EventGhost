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
    )

    $Env:EXITCODE = 0


    if ($LogDir) {
        $msg = $Args
        $mod = $ErrLog

        $ErrLog = "$LogDir\$msg.err.log"
        $OutLog = "$LogDir\$msg.out.log"
        $Args = "install --no-cache-dir $mod"

        Write-Host "  ---- Installing $msg x$Env:BUILDARCH"
    }

    if (-Not($Args)) {
        $Args = ""
    }

    $process_info = New-Object System.Diagnostics.ProcessStartInfo
    $process_info.UseShellExecute = $false
    $process = New-Object System.Diagnostics.Process

    $PrintOutput = $false

    if ($ErrLog) {
        $process_info.Arguments = $Args
        $process_info.FileName = $Executable
    }
    elseif ($Args -Like "*--build*")) {
        $process_info.Arguments = $Args
        $process_info.FileName = $Executable
        $PrintOutput = $true
    }
    elseif ($Executable -Like "*.msi") {
        $process_info.Arguments = "/I $Executable /quiet /passive /qn /norestart $Args"
        $process_info.FileName = "MsiExec.exe"
    }
    else {
        $process_info.Arguments = "/VerySilent /NoRestart /NoCancel /SupressMessageBoxes /Silent $Args"
        $process_info.FileName = $Executable
    }

    $process_info.RedirectStandardError = -Not ($PrintOutput)
    $process_info.RedirectStandardOutput = -Not ($PrintOutput)
    $process.StartInfo = $process_info

    if (-Not ($PrintOutput)) {
        $PrintOutput = $Env:DEBUG -eq "1"
    }

    if ($PrintOutput) {
        $process.Start()

    } else {
        $process.Start() | Out-Null
    }

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

        if ($o_log) {
            Out-File "$ot_log" -Encoding utf8 -Append -InputObject $o_log
        }

        if ($e_log) {
            Out-File "$er_log" -Encoding utf8 -Append -InputObject $e_log
        }
    }

    while (-Not ($process.HasExited)) {
        Start-Sleep -Milliseconds 100
        if ($OutLog) {
            Print-Logs $process $OutLog $ErrLog
        }
    }
    if ($OutLog) {
        Print-Logs $process $OutLog $ErrLog
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

