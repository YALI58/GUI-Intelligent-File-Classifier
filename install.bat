@echo off
chcp 65001 >nul
echo =====================================
echo    智能文件分类器 - 安装脚本
echo =====================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境
    echo 请先安装Python 3.7或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python环境检查通过
echo.

echo 正在安装依赖包...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo 依赖包安装失败！
    echo 请检查网络连接或手动安装
    pause
    exit /b 1
)

echo.
echo =====================================
echo    安装完成！
echo =====================================
echo.
echo 您可以通过以下方式启动应用：
echo 1. 双击 run.py
echo 2. 运行命令: python main.py
echo 3. 双击 start.bat
echo.
pause 