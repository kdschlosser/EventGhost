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


    

    # if ($Executable -like "*\*") {

    #    $Start = $Executable.LastIndexOf("\")
    #    $Length = $Executable.Length - $Start
    #    $process_name = $Executable.Substring($Start + 1, $Length - 1)
    #} else {
    #    $process_name = $Executable
    #}
    

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

    if ($ErrLog) {
        Out-File "$ErrLog" -InputObject $process.StandardError.ReadToEnd()
    }

    if ($OutLog) {
        Out-File "$OutLog" -InputObject $process.StandardOutput.ReadToEnd()
    }

    $Env:EXITCODE = $process.ExitCode


     if ($PrintOutput) {
            Write-Host " "
            Write-Host "******************* ERROR LOG ***********************"
            Write-Host " "
            Write-Host $process.StandardError.ReadToEnd()
            Write-Host " "
            Write-Host " "
            Write-Host "******************* OUTPUT LOG ***********************"
            Write-Host " "
            Write-Host $process.StandardOutput.ReadToEnd()
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
            Write-Host $process.StandardError.ReadToEnd()
            Write-Host " "
            Write-Host " "
            Write-Host "******************* OUTPUT LOG ***********************"
            Write-Host " "
            Write-Host $process.StandardOutput.ReadToEnd()
        }
        $host.SetShouldExit(1)
        exit
    }
}

