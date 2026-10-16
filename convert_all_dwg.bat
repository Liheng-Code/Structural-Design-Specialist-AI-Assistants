@echo off
rem Double-click. Converts every DXF in dwg_test\all to DWG (AutoCAD 2018 format) with AutoCAD 2023 accoreconsole. Output: dwg_test\all_out. Log: dwg_test\all_result.txt
cd /d "%~dp0"
set ACC="C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe"
if not exist dwg_test\all_out mkdir dwg_test\all_out
if exist dwg_test\all_result.txt del dwg_test\all_result.txt
for %%F in (dwg_test\all\*.dxf) do (
  > dwg_test\_one.scr echo _.SAVEAS
  >> dwg_test\_one.scr echo 2018
  >> dwg_test\_one.scr echo dwg_test\all_out\%%~nF.dwg
  >> dwg_test\_one.scr echo _.QUIT
  >> dwg_test\_one.scr echo Y
  %ACC% /i "%~dp0%%F" /s "%~dp0dwg_test\_one.scr" /l en-US > dwg_test\_log_%%~nF.txt 2>&1
  if exist dwg_test\all_out\%%~nF.dwg ( echo OK   %%~nF >> dwg_test\all_result.txt ) else ( echo FAIL %%~nF >> dwg_test\all_result.txt )
)
type dwg_test\all_result.txt
echo.
echo Tell Claude "convert all done".
pause
