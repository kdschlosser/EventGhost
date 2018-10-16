

$SysWOWDLL = "$Env:SYSTEMROOT\SysWOW64\python27.dll"
$SystemDLL = "$Env:SYSTEMROOT\System\python27.dll"

$Env:PATH = $Env:PATH -replace "C:\\Python27", $Env:PYTHON

If (Test-Path $SystemDLL) {
    Remove-Item $SystemDLL
}
If (Test-Path $SysWOWDLL) {
    Remove-Item $SysWOWDLL
}

$ModuleOutputFolder = $Env:APPVEYOR_BUILD_FOLDER + "\_build\output\ModuleOutput$Env:BUILDARCH"
if (-Not(Test-Path $ModuleOutputFolder)) {
    New-Item $ModuleOutputFolder -type directory | Out-Null
}

if (-Not (Test-Path $Env:PYTHON)) {
    Import-Module -Name ".\.appveyor_runapp.psm1"

    $InstallersFolder = $Env:APPVEYOR_BUILD_FOLDER + "\_build\installers\"
    if (-Not(Test-Path $InstallersFolder)) {
        New-Item $InstallersFolder -type directory | Out-Null
    }

    # I am using the VS 2017 appveyor image and this is not installed
    # with that image. It is needed to compile the crypto library
    # $VCInstaller = $InstallersFolder + "VCForPython27.msi"
    # $VCURL = "https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi"

    $StacklessInstaller = $InstallersFolder + $Env:STACKLESSINSTALLER
    $StacklessURL = "http://www.stackless.com/binaries/$Env:STACKLESSINSTALLER"

    $WXInstaller = $InstallersFolder + $Env:WXINSTALLER
    $WXURL = "http://downloads.sourceforge.net/wxpython/$Env:WXINSTALLER"

    $Py2ExeInstaller = $InstallersFolder + $Env:PY2EXEINSTALLER
    $Py2ExeURL = "https://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/$Env:PY2EXEINSTALLER"


    $SitePackages = "$Env:PYTHON\Lib\site-packages"

    $Python = "$Env:PYTHON\python.exe"
    $Pip = "$Env:PYTHON\Scripts\pip.exe"
    $EasyInstall = "$Env:PYTHON\Scripts\easy_install.exe"


    Write-Host "==================== Downloading Files ==================="
    # Start-FileDownload $VCURL -Timeout 60000 -FileName $VCInstaller
    Start-Job -ScriptBlock {Start-FileDownload $args[0] -Timeout 60000 -FileName $args[1]} -Name "Stackless" -ArgumentList $StacklessURL, $StacklessInstaller
    Start-Job -ScriptBlock {Start-FileDownload $args[0] -Timeout 60000 -FileName $args[1]} -Name "wxPython" -ArgumentList  $WXURL, $WXInstaller
    Start-Job -ScriptBlock {Start-FileDownload $args[0] -Timeout 60000 -FileName $args[1]} -Name "py2exe" -ArgumentList $Py2ExeURL, $Py2ExeInstaller

    Wait-Job -Name "Stackless"
    Write-Host " "
    Write-Host "=============== Installing Requirements =============="

    Write-Host "  ---- Installing Stackless 2.7.12150"
    Invoke-App "$StacklessInstaller" "TARGETDIR=$Env:PYTHON"

    # Write-Host "  ---- Installing Visual C Compiler for Python 2.7"
    # Invoke-App "$VCInstaller"

    Write-Host "  ---- Upgrading pip 9.0.1"
    Invoke-App $Python "-m pip install --no-cache-dir -U pip==9.0.1" "$ModuleOutputFolder\pip 9.0.1.err.log" "$ModuleOutputFolder\pip 9.0.1.out.log"

    Write-Host "  ---- Upgrading setuptools 40.2.0"
    Invoke-App $Python "-m pip install --no-cache-dir -U setuptools==40.2.0" "$ModuleOutputFolder\setuptools 40.2.0.err.log" "$ModuleOutputFolder\setuptools 40.2.0.out.log"

    Write-Host "  ---- Installing py2exe 0.6.9";
    Wait-Job -Name "py2exe"
    Invoke-App $EasyInstall "--always-unzip $Py2ExeInstaller" "$ModuleOutputFolder\py2exe 0.6.9.err.log" "$ModuleOutputFolder\py2exe 0.6.9.out.log"

    Write-Host "  ---- Installing wxPython 3.0.2.0"
    Wait-Job -Name "wxPython"
    Invoke-App $WXInstaller "/dir=$SitePackages"


    Invoke-App $Pip "pycrypto 2.6.1" "pycrypto==2.6.1" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "wheel 0.29.0" "wheel==0.29.0" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "commonmark 0.7.3" "commonmark==0.7.3" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "jinja2 2.8.1" "jinja2==2.8.1" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "sphinx 1.5.6" "sphinx==1.5.6" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "pillow 3.4.2" "pillow==3.4.2" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "comtypes 1.1.3" "https://github.com/enthought/comtypes/archive/1.1.3.zip" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "paramiko 2.2.1" "paramiko==2.2.1" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "pywin32 223" "pywin32==223" -LogDir $ModuleOutputFolder
    # *See Changes* PipInstall "pycrypto 2.6.1" "pycrypto==2.6.1"
    # *See Changes* PipInstall "ctypeslib 0.5.6" "svn+http://svn.python.org/projects/ctypes/trunk/ctypeslib/#ctypeslib=0.5.6"

} else {
    # we are already using a cached version so
    # there is no need to cache it agian.
    $env:APPVEYOR_CACHE_SKIP_SAVE = "true"
    Out-File "$ModuleOutputFolder\cached build" -InputObject ""

}
