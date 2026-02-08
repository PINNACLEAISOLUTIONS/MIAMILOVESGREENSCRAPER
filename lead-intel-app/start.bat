@echo off
echo Starting LeadIntel Intelligence Suite...

start cmd /k "cd server && npm start"
start cmd /k "cd client && npm run dev"

echo LeadIntel is launching!
echo Server: http://localhost:3001
echo Frontend: http://localhost:5173
echo.
echo Note: If it's the first time, make sure npm install finished.
