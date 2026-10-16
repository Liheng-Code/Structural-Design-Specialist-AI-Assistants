@echo off
rem Double-click. (1) installs the 5 skills into .claude\skills  (2) records which CAD/analysis software and Python libraries exist.
rem Only copies skill folders and writes probe_result.json next to this file.
cd /d "%~dp0"
echo Installing skills into .claude\skills ...
powershell -NoProfile -Command "New-Item -ItemType Directory -Force .claude\skills | Out-Null; Copy-Item -Recurse -Force skills-to-install\structural-* .claude\skills\; Get-ChildItem .claude\skills -Directory | Select-Object -ExpandProperty Name"
echo.
set PYCMD=
where python >nul 2>nul && set PYCMD=python
if not defined PYCMD where py >nul 2>nul && set PYCMD=py
if not defined PYCMD where python3 >nul 2>nul && set PYCMD=python3
if not defined PYCMD (
  echo Python was NOT found on PATH. The skills are installed, but the tools in tools\ need Python 3.9 or newer.
  echo Install it with:  winget install -e --id Python.Python.3.12   ^(tick "Add to PATH" if you use the web installer^)
  echo Then run: pip install pyyaml python-docx openpyxl ezdxf matplotlib pillow numpy   and run this file again.
  if exist probe_result.json del probe_result.json
  pause
  exit /b 1
)
echo Installing Python libraries ^(pip^) ...
%PYCMD% -m pip install --upgrade pyyaml python-docx openpyxl ezdxf matplotlib pillow numpy
if errorlevel 1 echo WARNING: pip install failed - check internet or proxy, then run this file again.
echo.
echo Probing installed software with %PYCMD% ...
%PYCMD% tools\cadgen\probe_cad.py > probe_result.json 2>&1
type probe_result.json
echo.
echo Done. Tell Claude "setup done" so it can read probe_result.json.
pause
