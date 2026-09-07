@echo off
title IT Navigator - IBM watsonx Orchestrate
cd /d "%~dp0"
set PYTHON_EXE="C:\Users\RePack\AppData\Local\Programs\Python\Python311\python.exe"

:MENU
cls
echo =====================================================================
echo           IT Navigator - Context-Aware IT Support Orchestrator
echo                    Platform: IBM watsonx Orchestrate
echo =====================================================================
echo.
echo   [1] Test Watson Orchestrate API Connection and List Live Agents
echo   [2] Run Deterministic Policy Engine and Security Unit Tests
echo   [3] Run Golden Dataset Evaluation Suite (Section 12 Release Gate)
echo   [4] Run Section 10 Walkthrough Simulation (Salesforce Outage)
echo   [5] Interactive Query Console (Test any custom employee problem)
echo   [6] Start OpenAPI Policy Engine Microservice (FastAPI on port 8000)
echo   [7] Deploy / Sync Agents and Tools to Watson Orchestrate
echo   [8] Exit
echo.
echo =====================================================================
set /p choice="Select an option (1-8): "

if "%choice%"=="1" goto CONN_TEST
if "%choice%"=="2" goto UNIT_TESTS
if "%choice%"=="3" goto GOLDEN_TESTS
if "%choice%"=="4" goto WALKTHROUGH
if "%choice%"=="5" goto INTERACTIVE
if "%choice%"=="6" goto START_API
if "%choice%"=="7" goto DEPLOY
if "%choice%"=="8" goto END
goto MENU

:CONN_TEST
echo.
echo [Running Watson Orchestrate Connection Test...]
%PYTHON_EXE% watson_orchestrate_client.py
echo.
pause
goto MENU

:UNIT_TESTS
echo.
echo [Running Policy Engine and Security Tests...]
%PYTHON_EXE% -m pytest tests/test_policy_engine.py tests/test_security_classifier.py -v
echo.
pause
goto MENU

:GOLDEN_TESTS
echo.
echo [Running 9 Golden Dataset Categories...]
%PYTHON_EXE% -m pytest tests/test_golden_dataset.py -v
echo.
pause
goto MENU

:WALKTHROUGH
echo.
echo [Executing Section 10 Walkthrough Scenario...]
%PYTHON_EXE% src/orchestrator/runner.py --query "I can't access Salesforce and I have a client meeting in 20 minutes."
echo.
pause
goto MENU

:INTERACTIVE
echo.
%PYTHON_EXE% src/orchestrator/runner.py --chat
pause
goto MENU

:START_API
echo.
echo [Starting FastAPI Policy Engine Microservice on http://127.0.0.1:8000/docs ...]
%PYTHON_EXE% -m uvicorn src.api.policy_server:app --reload --port 8000
pause
goto MENU

:DEPLOY
echo.
echo [Deploying IT Navigator Agents and Tools to Watson Orchestrate...]
%PYTHON_EXE% src/orchestrator/deployer.py
echo.
pause
goto MENU

:END
exit /b 0
