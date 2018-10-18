
$Env:PYTHON = "C:\Stackless27_x$Env:BUILDARCH"
$Env:PYTHONPATH = "$Env:PYTHON;$Env:PYTHON\Scripts;$Env:PYTHON\DLLs;$Env:PYTHON\Lib;$Env:PYTHON\Lib\site-packages;"

$SysWOWDLL = "$Env:SYSTEMROOT\SysWOW64\python27.dll"
$SystemDLL = "$Env:SYSTEMROOT\System\python27.dll"

$Env:PATH = $Env:PATH -replace "Python27", "Stackless27_x$Env:BUILDARCH"

If (Test-Path $SystemDLL) {
    Remove-Item $SystemDLL
}
If (Test-Path $SysWOWDLL) {
    Remove-Item $SysWOWDLL
}

$ModuleOutputFolder = $Env:APPVEYOR_BUILD_FOLDER + "\_build\output\ModuleOutput_x$Env:BUILDARCH"

if (-Not(Test-Path $ModuleOutputFolder)) {
    New-Item $ModuleOutputFolder -type directory | Out-Null
}

if (-Not (Test-Path $Env:PYTHON)) {
    # if appveyor image is changed to VS2017 you will need to uncomment these lines
    # $VCInstaller = $InstallersFolder + "VCForPython27.msi"
    # $VCURL = "https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi"

    Import-Module -Name ".\.appveyor_runapp.psm1"

    $InstallersFolder = $Env:APPVEYOR_BUILD_FOLDER + "\_build\installers\"
    if (-Not(Test-Path $InstallersFolder)) {
        New-Item $InstallersFolder -type directory | Out-Null
    }

    if ($Env:BUILDARCH -eq "64") {
        $StacklessInstaller = "python-2.7.12150.amd64-stackless.msi"
        $Py2ExeInstaller = "py2exe-0.6.9.win64-py2.7.amd64.exe"
    } else {
        $StacklessInstaller = "python-2.7.12150-stackless.msi"
        $Py2ExeInstaller = "py2exe-0.6.9.win32-py2.7.exe"
    }

    $StacklessURL = "http://www.stackless.com/binaries/$StacklessInstaller"
    $StacklessInstaller =  $InstallersFolder + $StacklessInstaller

    $Py2ExeURL = "https://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/$Py2ExeInstaller"
    $Py2ExeInstaller = $InstallersFolder + $Py2ExeInstaller

    $WxInstaller = "wxPython3.0-win$Env:BUILDARCH-3.0.2.0-py27.exe"
    $WxURL = "http://downloads.sourceforge.net/wxpython/$WxInstaller"
    $WXInstaller = $InstallersFolder + $WxInstaller


    $SitePackages = "$Env:PYTHON\Lib\site-packages"
    $Python = "$Env:PYTHON\python.exe"
    $Pip = "$Env:PYTHON\Scripts\pip.exe"
    $EasyInstall = "$Env:PYTHON\Scripts\easy_install.exe"

    Write-Host "=============== Installing Requirements =============="

    Write-Host "  ---- Installing Stackless 2.7.12150"
    Start-FileDownload $StacklessURL -Timeout 60000 -FileName $StacklessInstaller
    Invoke-App "MsiExec.exe" $StacklessInstaller -OutLog $Env:PYTHON

    # Write-Host "  ---- Installing Visual C Compiler for Python 2.7"
    # Invoke-App "$VCInstaller"

    Write-Host "  ---- Upgrading pip 9.0.1"
    Invoke-App $Python "-m pip install --no-cache-dir -U pip==9.0.1" "$ModuleOutputFolder\pip 9.0.1.err.log" "$ModuleOutputFolder\pip 9.0.1.out.log"


    Write-Host "  ---- Upgrading setuptools 40.2.0"
    Invoke-App $Python "-m pip install --no-cache-dir -U setuptools==40.2.0" "$ModuleOutputFolder\setuptools 40.2.0.err.log" "$ModuleOutputFolder\setuptools 40.2.0.out.log"

    Write-Host "  ---- Installing py2exe 0.6.9";
    Start-FileDownload $Py2ExeURL -Timeout 60000 -FileName $Py2ExeInstaller
    Invoke-App $EasyInstall "--always-unzip $Py2ExeInstaller" "$ModuleOutputFolder\py2exe 0.6.9.err.log" "$ModuleOutputFolder\py2exe 0.6.9.out.log"

    Write-Host "  ---- Installing wxPython 3.0.2.0"
    Start-FileDownload $WxURL -Timeout 60000 -FileName $WXInstaller
    Invoke-App $WXInstaller "/dir=$SitePackages"

    Invoke-App $Python "-m pip install --no-cache-dir " "$ModuleOutputFolder\pycryptodome 2.6.1.err.log" "$ModuleOutputFolder\pycryptodome 2.6.1.out.log"
    Invoke-App $Pip "pycryptodome 3.6.6" "pycryptodome==3.6.6" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "wheel 0.29.0" "wheel==0.29.0" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "commonmark 0.7.5" "commonmark==0.7.5" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "jinja2 2.8.1" "jinja2==2.8.1" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "sphinx 1.5.6" "sphinx==1.5.6" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "pillow 3.4.2" "pillow==3.4.2" -LogDir $ModuleOutputFolder
    Invoke-App $Pip "comtypes 1.1.7" "comtypes==1.1.7" -LogDir $ModuleOutputFolder
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
