@echo off
setlocal

REM Find the path to ffmpeg executable
for /f "tokens=*" %%i in ('where ffmpeg') do (
    set "ffmpeg_path=%%i"
)

REM Define folder paths

set "out_frames=out_frames"
set "results_folder=results"

REM Clean up existing temporary and results folders
if exist "%out_frames%" rmdir /s /q "%out_frames%"
if exist "%results_folder%" rmdir /s /q "%results_folder%"

REM Create temporary and results folders

mkdir "%out_frames%" 2>nul
mkdir "%results_folder%" 2>nul


.\realesrgan-ncnn-vulkan.exe -i "final" -o "%out_frames%" -n realesrgan-x4plus -s 4 -f jpg
REM Check if enhancement process generated output files
if not exist "%out_frames%\*.jpg" (
    echo Enhancement failed. No output files found in %out_frames%.
    goto :cleanup
)

REM Clean up temporary folders
:rmdir_tmp_frames
if exist "%tmp_frames%" (
    rmdir /s /q "%tmp_frames%"
    timeout /t 1 >nul
    goto :rmdir_tmp_frames
)

REM Prompt user to enter the name of the output video file
set /p "output_name=Enter the name of the output video file (without extension): "

REM Merge enhanced frames back into a video and save it in the results folder
ffmpeg -i "%out_frames%\frame_%%08d.jpg" -i "%input_path%" -map 0:v:0 -map 1:a:0 -c:a copy -c:v libx264 -r 23.98 -pix_fmt yuv420p "%results_folder%\%output_name%.mp4"

REM Pause for 5 seconds
timeout /t 5 >nul

echo Process completed successfully.
exit /b 0
