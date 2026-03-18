@setlocal
@if not defined EDK2_EDKREPO_PATH (
  @set EDK2_EDKREPO_PATH=%~dp0
)
@echo edkrepo: EDK2_EDKREPO_PATH=%EDK2_EDKREPO_PATH%
@if not defined PYTHON_COMMAND (
  @REM @set PYTHON_COMMAND=C:/Python312/python.exe
  @set PYTHON_COMMAND=py -3
)
@echo edkrepo: PYTHON_COMMAND=%PYTHON_COMMAND%

@REM %PYTHON_COMMAND% -m pip install -r %EDK2_EDKREPO_PATH%/edkrepo_dev_requirements_windows.txt

@%PYTHON_COMMAND% %EDK2_EDKREPO_PATH%/edkrepo_dev.py %*

