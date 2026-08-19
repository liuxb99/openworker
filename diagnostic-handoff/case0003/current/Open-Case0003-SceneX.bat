@echo off
setlocal
title Case 0003 Yujing Bridge - SceneX Launcher v3
echo CASE0003_SCENEX_LAUNCHER_VERSION=v3-explicit-scene
set "SCENEX_REPO=C:\github-runners\SceneX\_work\SceneX\SceneX"
set "SCENEX_PROJECT=C:\github-runners\SceneX\_work\SceneX\SceneX\godot"
set "SCENEX_MAIN_SCENE=C:\github-runners\SceneX\_work\SceneX\SceneX\godot\scenes\region_pack_race_demo.tscn"
set "SCENEX_MAIN_RESOURCE=res://scenes/region_pack_race_demo.tscn"
set "GODOT_EXE=C:\github-runners\SceneX\_work\_tool\SceneX\Godot\4.6.3\Godot_v4.6.3-stable_win64_console.exe"
set "REGION_PACK=D:\AI-Work\jobs\0003-YUJING-BRIDGE\scenex\terrain.region.json"
set "SCENEX_LAUNCH_LOG=D:\AI-Work\jobs\0003-YUJING-BRIDGE\scenex\scenex-launch.log"
if not exist "%GODOT_EXE%" (echo [ERROR] Godot not found: %GODOT_EXE% & pause & exit /b 2)
if not exist "%SCENEX_PROJECT%\project.godot" (echo [ERROR] SceneX project not found: %SCENEX_PROJECT% & pause & exit /b 3)
if not exist "%SCENEX_MAIN_SCENE%" (echo [ERROR] SceneX main scene not found: %SCENEX_MAIN_SCENE% & pause & exit /b 5)
if not exist "%REGION_PACK%" (echo [ERROR] Case 0003 Region Pack not found: %REGION_PACK% & pause & exit /b 4)
echo GODOT_EXE=%GODOT_EXE%
echo SCENEX_PROJECT=%SCENEX_PROJECT%
echo SCENEX_MAIN_RESOURCE=%SCENEX_MAIN_RESOURCE%
echo REGION_PACK=%REGION_PACK%
if /I "%~1"=="--check-only" (echo CASE0003_SCENEX_LAUNCHER_CHECK_PASS version=v3-explicit-scene & exit /b 0)
echo [%date% %time%] CASE0003_SCENEX_LAUNCHER_VERSION=v3-explicit-scene>"%SCENEX_LAUNCH_LOG%"
echo GODOT_EXE=%GODOT_EXE%>>"%SCENEX_LAUNCH_LOG%"
echo SCENEX_PROJECT=%SCENEX_PROJECT%>>"%SCENEX_LAUNCH_LOG%"
echo SCENEX_MAIN_RESOURCE=%SCENEX_MAIN_RESOURCE%>>"%SCENEX_LAUNCH_LOG%"
echo REGION_PACK=%REGION_PACK%>>"%SCENEX_LAUNCH_LOG%"
echo Opening Case 0003 Yujing Bridge in SceneX...
start "Case 0003 SceneX" "%GODOT_EXE%" --path "%SCENEX_PROJECT%" --scene "%SCENEX_MAIN_RESOURCE%" --resolution 1280x720 -- --region-pack="%REGION_PACK%"
exit /b 0
