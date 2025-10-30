@echo off
echo ================================
echo Article Analyser Setup Script
echo ================================
echo.

echo [1/4] Setting up Downloader...
cd Downloader
python -m venv .venv
call .venv\Scripts\activate
pip install -e .
call deactivate
cd ..
echo Downloader setup complete!
echo.

echo [2/4] Setting up Tokenizer...
cd Tokenizer
python -m venv .venv
call .venv\Scripts\activate
pip install -e .
call deactivate
cd ..
echo Tokenizer setup complete!
echo.

echo [3/4] Setting up Summarizer...
cd Summarizer
python -m venv .venv
call .venv\Scripts\activate
pip install -e .
call deactivate
cd ..
echo Summarizer setup complete!
echo.

echo [4/4] Setting up WebProgram...
cd WebProgram
python -m venv .venv
call .venv\Scripts\activate
pip install -r requirements.txt
reflex init
call deactivate
cd ..
echo WebProgram setup complete!
echo.

echo ================================
echo Setup Complete!
echo ================================
echo.
echo To run the web application:
echo   cd WebProgram
echo   .venv\Scripts\activate
echo   reflex run
echo.
pause
