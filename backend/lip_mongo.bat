REM starts mongodb (must be on the path) with dbpath set to mongodb subfolder
SET DBPATH=%~dp0%
mongod --dbpath %DBPATH%mongodb
