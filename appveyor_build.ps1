Write-Host "=============== Start the EventGhost build ==============="
If (
    ($Env:APPVEYOR_REPO_TAG.tolower() -eq "true") -and
    ($Env:APPVEYOR_REPO_TAG_NAME.tolower().startswith("deploy"))
) {
    # to do a release, create a tag in the form "Deploy_VERSION"
    # VERSION must be a valid version string (without leading "v")
    # this tag will be deleted and a new release "vVERSION" created.

    git checkout -q master
    $release = ' --release --version "' + $Env:APPVEYOR_REPO_TAG_NAME.split("_", 2)[1] + '"'
    if ($Env:SFTP_URL) {
        $url = ' --docs --url "$Env:SFTP_URL"'
    } else {
        $url = ""
    }

    Write-Host "=================== Building deploy ====================="

} else {
    Write-Host "=================== Building WIP ===================="
    $release = ""
    $url = ""
}

Start-Process python -ArgumentList "_build\Build.py --build --package$release$url" -NoNewWindow -Wait
    
$Env:SetupExe = gci -recurse -filter "_build\output\*$Env:OUTPUTFILE" -name
$Env:Logfile = $Env:LOGFILE
$Env:ModuleOutput = $Env:MODULEOUTPUT

if (($Env:SetupExe) -and (-Not ($SetupExe -contains '*x64*'))) {
    # update the appveyor build version to be the same as the EventGhost version
    $Start = $Env:SetupExe.IndexOf("_")
    $Length = $Env:SetupExe.LastIndexOf("_") - $Start
    $BuildVersion = $Env:SetupExe.Substring($Start + 1, $Length - 1)
    Update-AppveyorBuild -Version "$BuildVersion"
}

Write-Host " "
Write-Host "=============== EventGhost build finished ================"
Write-Host " "