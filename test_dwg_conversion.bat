@echo off
rem Double-click. Tries ONE DXF -> DWG conversion with AutoCAD 2023 accoreconsole, then checks the result. Writes dwg_test\dwg_test_result.txt
cd /d "%~dp0"
if not exist dwg_test\out mkdir dwg_test\out
set ACC="C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe"
if not exist %ACC% (echo accoreconsole 2023 not found > dwg_test\dwg_test_result.txt & type dwg_test\dwg_test_result.txt & pause & exit /b 1)
%ACC% /i "%~dp0dwg_test\WH-STR-SD-001_R00.dxf" /s "%~dp0dwg_test\convert_one.scr" /l en-US > dwg_test\accore_log.txt 2>&1
echo exit code %errorlevel% > dwg_test\dwg_test_result.txt
if exist dwg_test\out\WH-STR-SD-001_R00.dwg (
  echo DWG file created >> dwg_test\dwg_test_result.txt
  powershell -NoProfile -Command "$b=[IO.File]::ReadAllBytes('dwg_test\out\WH-STR-SD-001_R00.dwg'); 'size '+$b.Length; 'header '+[Text.Encoding]::ASCII.GetString($b,0,6)" >> dwg_test\dwg_test_result.txt
) else (
  echo NO DWG created >> dwg_test\dwg_test_result.txt
)
type dwg_test\dwg_test_result.txt
echo.
echo Tell Claude "dwg test done".
pause
