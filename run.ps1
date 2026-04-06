# start the backend in powershell

# cd "C:\VScode\Python\Projects\Hiring-Pipeline-Automation"
# $env:OAUTHLIB_INSECURE_TRANSPORT = "1"
# & "C:\Envs\hiring-pipeline\Scripts\Activate.ps1"
# cd backend 
# uvicorn main:app --reload

Start-Process powershell -ArgumentList '-NoExit', '-Command', '& "C:\Envs\hiring-pipeline\Scripts\Activate.ps1"; cd Backend; uvicorn main:app --reload'

# start the frontend
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd Frontend; npm run dev'
