@echo off
echo "Setting up virtual environment..."
if not exist venv (
    python -m venv venv
)
call venv\\Scripts\\activate

echo "Installing dependencies..."
pip install -r ..\\requirements.txt

echo "Building executable..."
pyinstaller ..\\SalonBillingSystem.spec --distpath ..\\dist --workpath ..\\build

echo "Build complete. Executable is in dist\\SalonBillingSystem"
deactivate
pause
