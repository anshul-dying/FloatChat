@echo off
echo Testing PostgreSQL integration...

REM Activate virtual environment
call conda activate ./venv

REM Test PostgreSQL connection and data storage
echo Testing PostgreSQL connection...
python -c "from src.database.relational_db import test_postgresql_connection, get_data_count; success, info = test_postgresql_connection(); print(f'Connection: {success}'); print(f'Info: {info}'); print(f'Data count: {get_data_count()}')"

echo PostgreSQL test completed!
pause
