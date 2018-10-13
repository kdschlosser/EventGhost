
Import-Module -Name ".\appveyor_runapp.psm1"

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

Invoke-App "$Env:PYTHON\python.exe" "$Env:APPVEYOR_BUILD_FOLDER\_build\Build.py --build --package$release$url" "$Env:APPVEYOR_BUILD_FOLDER\_build\output\build_error.log" "$Env:APPVEYOR_BUILD_FOLDER\_build\output\build_output.log" -PrintOutput
    
$Env:SetupExe = Get-ChildItem "$Env:APPVEYOR_BUILD_FOLDER\_build\output\*" -File -include "*Setup_$Env:BUILDARCH.exe" -name

# EventGhost_WIP-2018.10.13-07.17.46_Setup_x64.exe
if (($Env:SetupExe) -and (-Not ($SetupExe -like '*_x64'))) {
    # update the appveyor build version to be the same as the EventGhost version

    $Start = $Env:SetupExe.IndexOf("_")
    $Length = $Env:SetupExe.LastIndexOf("_") - $Start

    $BuildVersion = $Env:SetupExe.Substring($Start + 1, $Length - 1)
    $Length = $BuildVersion.LastIndexOf("_")
    $BuildVersion = $BuildVersion.Substring(0, $Length - 1)

    Update-AppveyorBuild -Version "$BuildVersion"
}

Start-Process 7z -ArgumentList "a", "-bsp1", "-bb3", "$ModuleOutputFolder.zip", "-r", "$ModuleOutputFolder\*.*" -NoNewWindow -Wait

Write-Host " "
Write-Host "=============== EventGhost build finished ================"
Write-Host " "