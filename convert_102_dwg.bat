@echo off
rem Double-click. Re-converts ONLY sheet 102 (previously failed on an undefined HIDDEN linetype).
cd /d "%~dp0"
set ACC="C:\Program Files\Autodesk\AutoCAD 2023\accoreconsole.exe"
if not exist dwg_test\all_out mkdir dwg_test\all_out
> dwg_test\_one.scr echo _.SAVEAS
>> dwg_test\_one.scr echo 2018
>> dwg_test\_one.scr echo dwg_test\all_out\WH-STR-SD-102_R00.dwg
>> dwg_test\_one.scr echo _.QUIT
>> dwg_test\_one.scr echo Y
%ACC% /i "%~dp0dwg_test\all\WH-STR-SD-102_R00.dxf" /s "%~dp0dwg_test\_one.scr" /l en-US > dwg_test\_log_WH-STR-SD-102_R00.txt 2>&1
if exist dwg_test\all_out\WH-STR-SD-102_R00.dwg (echo OK 102) else (echo FAIL 102)
pause
