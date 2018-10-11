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



    $process_info = New-Object System.Diagnostics.ProcessStartInfo
    $process_info.FileName = $Executable
    $process_info.RedirectStandardError = $true
    $process_info.RedirectStandardOutput = $true
    $process_info.UseShellExecute = $false
    $process_info.Arguments = $ProcessArgs
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $process_info
    $process.Start() | Out-Null
    $process.WaitForExit()

    $o_log = $process.StandardOutput.ReadToEnd()
    $e_log = $process.StandardError.ReadToEnd()
    
    if ($ErrLog) {
        Out-File "$ErrLog" -Encoding utf8 -InputObject $e_log $o_log
    }

    if ($OutLog) {
        Out-File "$OutLog" -Encoding utf8 -InputObject $o_log
    }

    $Env:EXITCODE = $process.ExitCode


     if ($PrintOutput) {
            Write-Host " "
            Write-Host "******************* ERROR LOG ***********************"
            Write-Host " "
            Write-Host $e_log
            Write-Host " "
            Write-Host " "
            Write-Host "******************* OUTPUT LOG ***********************"
            Write-Host " "
            Write-Host $o_log
     }

    if ($process.ExitCode -eq 0) {
        Write-Host "       Done."
        $host.SetShouldExit(0)
    } else {
        Write-Host "       Failed."

        if ($ErrLog -and (-Not($PrintOutput)))  {
            Write-Host " "
            Write-Host "******************* ERROR LOG ***********************"
            Write-Host " "
            Write-Host $e_log
            Write-Host " "
            Write-Host " "
            Write-Host "******************* OUTPUT LOG ***********************"
            Write-Host " "
            Write-Host $o_log
        }
        $host.SetShouldExit(1)
        exit
    }
}

