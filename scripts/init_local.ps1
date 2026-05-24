# TeamMind AI Windows 初始化
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

pip install -r backend/requirements.txt --index-url https://pypi.org/simple/
python database/init_db.py

Write-Host ""
Write-Host "初始化完成。启动方式:"
Write-Host "  python main.py"
Write-Host "  局域网/公网: python main.py --host 0.0.0.0 --no-browser"
