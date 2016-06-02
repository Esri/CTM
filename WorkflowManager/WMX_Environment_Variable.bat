REM  This .bat files sets the WMX_PATH variable for the CTM Workflow Manager (WMX) Workflows
REM  This file needs to be run on each machine to point the WMX Workflow Script steps to the correct tool location.

cd..
setx WMX_PATH "%CD%" /m
