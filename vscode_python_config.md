# VSCode Python解释器配置

## 问题
VSCode默认使用 `C:/Program Files (x86)/Microsoft Visual Studio/Shared/Python39_64/python.exe`，缺少numpy等库。

## 解决方法

### 方法1：修改默认解释器
1. `Ctrl + Shift + P` 打开命令面板
2. 输入 `Python: Select Interpreter`
3. 选择本地 Python 环境（Base 或 conda）
4. 如果没有，点击 "Enter interpreter path" → "Find" → 选择本地的 python.exe

### 方法2：修改配置文件
在 `.vscode/settings.json` 中添加：
```json
{
    "python.defaultInterpreterPath": "C:/ProgramData/Anaconda3/python.exe"
}
```
路径改为本地 conda 的 python.exe 地址。