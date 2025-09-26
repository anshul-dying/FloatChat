@echo off
echo Recreating argo_data table with correct schema...

REM Activate virtual environment
call conda activate ./venv

REM Recreate the table
echo Dropping and recreating argo_data table...
python scripts\recreate_table.py

echo Table recreation completed!
pause
