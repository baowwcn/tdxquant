# a_share_monthly.db 执行记录

## 1. 运行入库脚本
命令:
```powershell
python store_a_share_data.py
```

结果:
- 失败，报错 `ModuleNotFoundError: No module named 'pandas'`

## 2. 安装依赖
命令:
```powershell
c:/new_tdx64/PYPlugins/user/.venv-1/Scripts/python.exe -m pip install pandas
```

结果:
- 成功安装 `pandas`

## 3. 重新运行入库脚本
命令:
```powershell
c:/new_tdx64/PYPlugins/user/.venv-1/Scripts/python.exe store_a_share_data.py
```

结果:
- 脚本执行成功，开始写入 `a_share_monthly.db`
- 处理了多批股票数据，示例输出包含 `605169.SH`、`605177.SH` 等记录

## 4. 验证数据库文件
命令:
```powershell
c:/new_tdx64/PYPlugins/user/.venv-1/Scripts/python.exe -c "import os, sqlite3; path='a_share_monthly.db'; print('exists', os.path.exists(path)); conn=sqlite3.connect(path); cur=conn.cursor(); cur.execute('SELECT COUNT(*) FROM stock_data'); print('rows', cur.fetchone()[0]); conn.close()"
```

结果:
- 数据库文件存在
- `stock_data` 表行数: `126116`

## 5. 查询万科数据
命令:
```powershell
c:/new_tdx64/PYPlugins/user/.venv-1/Scripts/python.exe -c "import sqlite3; conn=sqlite3.connect('a_share_monthly.db'); cur=conn.cursor(); code='000002.SZ'; cur.execute('SELECT COUNT(*) FROM stock_data WHERE code=?', (code,)); print('code', code, 'count', cur.fetchone()[0]); cur.execute('SELECT date, open, high, low, close, volume FROM stock_data WHERE code=? ORDER BY date', (code,)); rows=cur.fetchall(); print('\n'.join(str(r) for r in rows)); conn.close()"
```

结果:
- 万科代码 `000002.SZ` 数据条数: `23`
- 返回记录（按日期排序）:
  - 2026-03-10: open 4.66, high 4.69, low 4.65, close 4.67, volume 63955628.0
  - 2026-03-11: open 4.66, high 4.69, low 4.64, close 4.67, volume 77062304.0
  - 2026-03-12: open 4.66, high 4.68, low 4.63, close 4.65, volume 75863120.0
  - 2026-03-13: open 4.65, high 4.73, low 4.64, close 4.66, volume 116130128.0
  - 2026-03-16: open 4.66, high 4.72, low 4.64, close 4.66, volume 90004040.0
  - 2026-03-17: open 4.68, high 4.76, low 4.66, close 4.70, volume 155801600.0
  - 2026-03-18: open 4.68, high 4.69, low 4.61, close 4.63, volume 108765304.0
  - 2026-03-19: open 4.61, high 4.63, low 4.50, close 4.50, volume 140671728.0
  - 2026-03-20: open 4.51, high 4.53, low 4.33, close 4.34, volume 182408672.0
  - 2026-03-23: open 4.25, high 4.26, low 4.01, close 4.02, volume 212064800.0
  - 2026-03-24: open 4.09, high 4.11, low 4.02, close 4.09, volume 91531264.0
  - 2026-03-25: open 4.08, high 4.14, low 4.07, close 4.12, volume 86515584.0
  - 2026-03-26: open 4.10, high 4.14, low 4.03, close 4.04, volume 84825888.0
  - 2026-03-27: open 4.01, high 4.07, low 3.98, close 4.06, volume 65723064.0
  - 2026-03-30: open 4.00, high 4.03, low 3.96, close 4.01, volume 94848144.0
  - 2026-03-31: open 4.02, high 4.08, low 3.98, close 3.99, volume 98965736.0
  - 2026-04-01: open 4.04, high 4.07, low 3.99, close 4.04, volume 106846992.0
  - 2026-04-02: open 4.01, high 4.02, low 3.91, close 3.92, volume 123161080.0
  - 2026-04-03: open 3.92, high 3.93, low 3.80, close 3.82, volume 103542096.0
  - 2026-04-07: open 3.80, high 3.82, low 3.76, close 3.81, volume 73291120.0
  - 2026-04-08: open 3.85, high 3.98, low 3.84, close 3.95, volume 122020928.0
  - 2026-04-09: open 3.90, high 3.91, low 3.85, close 3.87, volume 85780320.0
  - 2026-04-10: open 3.87, high 3.94, low 3.87, close 3.91, volume 50572656.0

## 6. 结论
- `a_share_monthly.db` 已成功生成
- 万科数据已写入且可查询

---

> 该记录已保存为 `a_share_monthly_db_execution_log.md`。