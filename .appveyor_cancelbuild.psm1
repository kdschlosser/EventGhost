Function Check_Build {
    [CmdletBinding()]
    Param ()

    $Records = Invoke-RestMethod "https://ci.appveyor.com/api/projects/$env:APPVEYOR_ACCOUNT_NAME/$env:APPVEYOR_PROJECT_SLUG/history?recordsNumber=50"
    $BuildNumber = ($Records.builds | Where-Object pullRequestId -eq $Env:APPVEYOR_PULL_REQUEST_NUMBER)[0].buildNumber

    if ($Env:APPVEYOR_PULL_REQUEST_NUMBER -and ($Env:APPVEYOR_BUILD_NUMBER -ne $BuildNumber)) {
        throw "There are newer queued builds for this pull request, failing early."
    }
}
