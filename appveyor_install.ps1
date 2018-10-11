
$SysWOWDLL = "$Env:SYSTEMROOT\SysWOW64\python27.dll"
$SystemDLL = "$Env:SYSTEMROOT\System\python27.dll"

$Env:PATH = $Env:PATH -replace "C:\\Python27", $Env:PYTHON

If (Test-Path $SystemDLL) {
    Remove-Item $SystemDLL
}
If (Test-Path $SysWOWDLL) {
    Remove-Item $SysWOWDLL
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

    Function RUN-APP {
        [CmdletBinding()]
        Param (
           [Parameter(Mandatory=$True)]
           [String]$Executable,
           [Parameter(Mandatory=$False)]
           [String]$Args,
           [Parameter(Mandatory=$False)]
           [String]$StdErr,
           [Parameter(Mandatory=$False)]
           [String]$StdOut,
           [Parameter(Mandatory=$False)]
           [String]$MsiFile,
           [Parameter(Mandatory=$False)]
           [String]$LogDir
        )


        if ($LogDir) {
            $msg = $Args
            $mod = $StdErr

            $StdErr = "$LogDir\$msg.err.log"
            $StdOut = "$LogDir\$msg.out.log"
            $Args = "install --no-cache-dir $mod"

            Write-Host "  ---- Installing $msg $Env:BUILDARCH"
        }

        if (-Not($Args)) {
            $Args = ""
        }
        if ($StdErr) {
            Start-Process $Executable -RedirectStandardError $StdErr -RedirectStandardOutput $StdOut -ArgumentList $Args -NoNewWindow -Wait
        }
        elseif ($Executable -Like '*.msi') {
            Start-Process MsiExec.exe -ArgumentList "/I $Executable /quiet /passive /qn /norestart $Args" -NoNewWindow -Wait
        }
        else {
            Start-Process $Executable -ArgumentList "/VerySilent /NoRestart /NoCancel /SupressMessageBoxes /Silent $Args" -NoNewWindow -Wait
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Host "       Done."
            $host.SetShouldExit(0)
        } else {
            Write-Host "       Failed."
            if ($StdErr)  {
                Write-Host " "
                Write-Host "******************* ERROR LOG ***********************"
                Write-Host " "
                Get-Content -Path "$StdErr"
                Write-Host " "
                Write-Host " "
                Write-Host "******************* OUTPUT LOG ***********************"
                Write-Host " "
                Get-Content -Path "$StdOut"
            }
            $host.SetShouldExit(1)
        }
    }


    Write-Host "==================== Downloading Files ==================="
    Start-FileDownload $VCURL -Timeout 60000 -FileName $VCInstaller
    Start-FileDownload $StacklessURL -Timeout 60000 -FileName $StacklessInstaller
    Start-FileDownload $WXURL -Timeout 60000 -FileName $WXInstaller
    Start-FileDownload $Py2ExeURL -Timeout 60000 -FileName $Py2ExeInstaller

    Write-Host " "
    Write-Host "=============== Installing Requirements =============="

    Write-Host "  ---- Installing Stackless 2.7.12150"
    RUN-APP "$StacklessInstaller" "TARGETDIR=$Env:PYTHON"

    Write-Host "  ---- Installing Visual C Compiler for Python 2.7"
    RUN-APP "$VCInstaller"

    Write-Host "  ---- Upgrading pip 9.0.1"
    RUN-APP "python" "-m pip install --no-cache-dir -U pip==9.0.1" "$ModuleOutputFolder\pip 9.0.1.err.log" "$ModuleOutputFolder\pip 9.0.1.out.log"

    Write-Host "  ---- Upgrading setuptools 40.2.0"
    RUN-APP "python" "-m pip install --no-cache-dir -U setuptools==40.2.0" "$ModuleOutputFolder\setuptools 40.2.0.err.log" "$ModuleOutputFolder\setuptools 40.2.0.out.log"

    Write-Host "  ---- Installing wxPython 3.0.2.0"
    RUN-APP $WXInstaller "/dir=$SitePackages"

    Write-Host "  ---- Installing py2exe 0.6.9"
    RUN-APP "easy_install" "--always-unzip $Py2ExeInstaller" "$ModuleOutputFolder\py2exe 0.6.9.err.log" "$ModuleOutputFolder\py2exe 0.6.9.out.log"

    # *See Changes* PipInstall "pycrypto 2.6.1" "pycrypto==2.6.1"
    # *See Changes* PipInstall "ctypeslib 0.5.6" "svn+http://svn.python.org/projects/ctypes/trunk/ctypeslib/#ctypeslib=0.5.6"
    RUN-APP "pip" "pycryptodome 3.6.6" "pycryptodome==3.6.6" -LogDir $ModuleOutputFolder
    RUN-APP "pip" "wheel 0.29.0" "wheel==0.29.0" -LogDir $ModuleOutputFolder
    RUN-APP "pip" "jinja2 2.8.1" "jinja2==2.8.1" -LogDir $ModuleOutputFolder
    RUN-APP "pip" "sphinx 1.5.6" "sphinx==1.5.6" -LogDir $ModuleOutputFolder
    RUN-APP "pip" "commonmark 0.7.3" "commonmark==0.7.3" -LogDir $ModuleOutputFolder
    RUN-APP "pip" "pillow 3.4.2" "pillow==3.4.2" -LogDir $ModuleOutputFolder
    RUN-APP "pip" "comtypes 1.1.3" "https://github.com/enthought/comtypes/archive/1.1.3.zip" -LogDir $ModuleOutputFolder
    RUN-APP "pip" "paramiko 2.2.1" "paramiko==2.2.1" -LogDir $ModuleOutputFolder
    RUN-APP "pip" "pywin32 223" "pywin32==223" -LogDir $ModuleOutputFolder

} else {
    # we are already using a cached version so
    # there is no need to cache it agian.
    $env:APPVEYOR_CACHE_SKIP_SAVE = "true"
    Out-File "$ModuleOutputFolder\cached build" -InputObject ""

}

Start-Process 7z -ArgumentList "a", "-bsp1", "-bb3", "$ModuleOutputFolder.zip", "-r", "$ModuleOutputFolder\*.*" -NoNewWindow -Wait