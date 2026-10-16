@echo off
rem Re-converts ONLY sheet 004 (mandrel row corrected to 140/175).
cd /d "%~dp0"
set ACC="C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe"
> dwg_test\_one.scr echo _.SAVEAS
>> dwg_test\_one.scr echo 2018
>> dwg_test\_one.scr echo dwg_test\all_out\WH-STR-SD-004_R00.dwg
>> dwg_test\_one.scr echo _.QUIT
>> dwg_test\_one.scr echo Y
del dwg_test\all_out\WH-STR-SD-004_R00.dwg 2>nul
%ACC% /i "%~dp0dwg_test\all\WH-STR-SD-004_R00.dxf" /s "%~dp0dwg_test\_one.scr" /l en-US > dwg_test\_log_WH-STR-SD-004_R00.txt 2>&1
if exist dwg_test\all_out\WH-STR-SD-004_R00.dwg (echo OK 004) else (echo FAIL 004)
pause
