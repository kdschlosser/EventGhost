
$PythonDLL = $Env:SYSTEMROOT + $Env:PYTHONDLL

If (Test-Path $PythonDLL) {
    Remove-Item $PythonDLL
}

$ModuleOutputFolder = $Env:APPVEYOR_BUILD_FOLDER + "\_build\output\$Env:MODULEOUTPUT"
if (-Not(Test-Path $ModuleOutputFolder)) {
    New-Item $ModuleOutputFolder -type directory | Out-Null
}

if (-Not (Test-Path $Env:PYTHON)) {

    $InstallersFolder = $Env:APPVEYOR_BUILD_FOLDER + "\_build\installers\"
    if (-Not(Test-Path $InstallersFolder)) {
        New-Item $InstallersFolder -type directory | Out-Null
    }



    # I am using the VS 2017 appveyor image and this is not installed
    # with that image. It is needed to compile the crypto library
    $VCInstaller = $InstallersFolder + "VCForPython27.msi"
    $VCURL = "https://download.microsoft.com/download/7/9/6/796EF2E4-801B-4FC4-AB28-B59FBF6D907B/VCForPython27.msi"

    $StacklessInstaller = $InstallersFolder + $Env:STACKLESSINSTALLER
    $StacklessURL = "http://www.stackless.com/binaries/$Env:STACKLESSINSTALLER"

    $WXInstaller = $InstallersFolder + $Env:WXINSTALLER
    $WXURL = "http://downloads.sourceforge.net/wxpython/$Env:WXINSTALLER"

    $Py2ExeInstaller = $InstallersFolder + $Env:PY2EXEINSTALLER
    $Py2ExeURL = "https://sourceforge.net/projects/py2exe/files/py2exe/0.6.9/$Env:PY2EXEINSTALLER"


    $SitePackages = "$Env:PYTHON\Lib\site-packages"

    Function PipInstall ($msg, $mod, $log) {
        $StdErr = $log + "\$msg.err.log"
        $StdOut = $log + "\$msg.out.log"

    
        Write-Host "  ---- Installing $msg $Env:BUILDARCH" 
        START-PROCESS pip -RedirectStandardError "$StdErr" -RedirectStandardOutput "$StdOut" -ArgumentList "install", "--no-cache-dir", "$mod"  -NoNewWindow -Wait
        Write-Host "       Done."
    }

    Write-Host "==================== Downloading Files ==================="
    Start-FileDownload $VCURL -Timeout 60000 -FileName $VCInstaller
    Start-FileDownload $StacklessURL -Timeout 60000 -FileName $StacklessInstaller
    Start-FileDownload $WXURL -Timeout 60000 -FileName $WXInstaller
    Start-FileDownload $Py2ExeURL -Timeout 60000 -FileName $Py2ExeInstaller

    Write-Host " "
    Write-Host "=============== Installing Requirements =============="

    Write-Host "  ---- Installing Stackless 2.7.12150"
    Start-Process MsiExec.exe -ArgumentList "/I", "$StacklessInstaller", "/quiet", "/passive", "/qn", "/norestart", "TARGETDIR=$Env:PYTHON" -NoNewWindow -Wait
    Write-Host "       Done."


    Write-Host "  ---- Installing Visual C Compiler for Python 2.7"
    Start-Process MsiExec.exe -ArgumentList "/I", "$VCInstaller", "/quiet", "/passive", "/qn", "/norestart" -NoNewWindow -Wait
    Write-Host "       Done."
    Write-Host " "

    Write-Host "  ---- Upgrading pip 9.0.1"
    Start-Process python -RedirectStandardError "$ModuleOutputFolder\pip 9.0.1.err.log" -RedirectStandardOutput "$ModuleOutputFolder\pip 9.0.1.out.log" -ArgumentList "-m", "pip", "install", "--no-cache-dir", "-U", "pip==9.0.1" -NoNewWindow -Wait
    Write-Host "       Done."

    Write-Host "  ---- Upgrading setuptools 40.2.0"
    Start-Process python -RedirectStandardError "$ModuleOutputFolder\setuptools 40.2.0.err.log" -RedirectStandardOutput "$ModuleOutputFolder\setuptools 40.2.0.out.log" -ArgumentList "-m", "pip", "install", "--no-cache-dir", "-U", "setuptools==40.2.0" -NoNewWindow -Wait
    Write-Host "       Done."

    Write-Host "  ---- Installing wxPython 3.0.2.0"
    Start-Process $WXInstaller -ArgumentList "/VerySilent", "/NoRestart", "/NoCancel", "/SupressMessageBoxes", "/Silent", "/dir=$SitePackages" -NoNewWindow -Wait
    Write-Host "       Done"

    Write-Host "  ---- Installing py2exe 0.6.9"
    Start-Process easy_install -RedirectStandardError "$ModuleOutputFolder\py2exe 0.6.9.err.log" -RedirectStandardOutput "$ModuleOutputFolder\py2exe 0.6.9.out.log" -ArgumentList "--always-unzip", "$Py2ExeInstaller" -NoNewWindow -Wait
    Write-Host "       Done."

    # *See Changes* PipInstall "pycrypto 2.6.1" "pycrypto==2.6.1"
    # *See Changes* PipInstall "ctypeslib 0.5.6" "svn+http://svn.python.org/projects/ctypes/trunk/ctypeslib/#ctypeslib=0.5.6"
    PipInstall "pycryptodome 3.6.6" "pycryptodome==3.6.6" $ModuleOutputFolder
    PipInstall "wheel 0.29.0" "wheel==0.29.0" $ModuleOutputFolder
    PipInstall "jinja2 2.8.1" "jinja2==2.8.1" $ModuleOutputFolder
    PipInstall "sphinx 1.5.6" "sphinx==1.5.6" $ModuleOutputFolder
    PipInstall "commonmark 0.7.3" "commonmark==0.7.3" $ModuleOutputFolder
    PipInstall "pillow 3.4.2" "pillow==3.4.2" $ModuleOutputFolder
    PipInstall "comtypes 1.1.3" "https://github.com/enthought/comtypes/archive/1.1.3.zip" $ModuleOutputFolder
    PipInstall "paramiko 2.2.1" "paramiko==2.2.1" $ModuleOutputFolder
    PipInstall "pywin32 223" "pywin32==223" $ModuleOutputFolder

    If (Test-Path $PythonDLL) {
        Copy-Item $PythonDLL -Destination $Env:PYTHON
        Remove-Item $PythonDLL
    }
     
} else {
    # we are already using a cached version so
    # there is no need to cache it agian.
    $env:APPVEYOR_CACHE_SKIP_SAVE = "true"
    Out-File "$ModuleOutputFolder\cached build" -InputObject ""

}

Start-Process 7z -ArgumentList "a", "-bsp1", "-bb3", "$ModuleOutputFolder.zip", "-r", "$ModuleOutputFolder\*.*" -NoNewWindow -Wait