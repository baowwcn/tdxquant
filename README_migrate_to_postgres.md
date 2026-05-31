# 将 `a_share_full.db` 迁移到 PostgreSQL（在 Windows 主机上）

本文档说明如何在 Windows（192.168.1.111）上安装 PostgreSQL、创建数据库与用户，并使用提供的脚本把 `a_share_full.db` 导入 PostgreSQL。

## 1. 在 Windows 上安装 PostgreSQL

- 推荐使用 EnterpriseDB 官方安装器：https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- 默认安装会创建 `postgres` 超级用户。记下你选择的服务端口（默认 5432）和管理员密码。

## 2. 创建目标数据库与用户（示例）

在 Windows 上打开 `psql` 或使用 `pgAdmin`：

```sql
-- 使用 postgres 超级用户连接
CREATE USER auser WITH PASSWORD 'apassword';
CREATE DATABASE a_share OWNER auser;
GRANT ALL PRIVILEGES ON DATABASE a_share TO auser;
```

## 3. 配置防火墙（如果需要局域网访问）

在 Windows 防火墙允许 `postgres.exe` 或允许 TCP 5432 端口入站。

```powershell
New-NetFirewallRule -DisplayName "Postgres5432" -Direction Inbound -LocalPort 5432 -Protocol TCP -Action Allow
```

## 4. 在项目目录准备 Python 环境并安装依赖

建议在已有虚拟环境中操作：

```powershell
# 激活已有 venv
E:\new_tdx64\PYPlugins\user\.venv-1\Scripts\Activate.ps1
pip install -r requirements_migration.txt
```

文件 `requirements_migration.txt` 包含：
- pandas
- sqlalchemy
- psycopg2-binary

（脚本 `sqlite_to_postgres.py` 使用 `psycopg2` 来插入数据）

## 5. 运行迁移脚本

示例命令：

```powershell
python sqlite_to_postgres.py --sqlite E:\new_tdx64\PYPlugins\user\a_share_full.db --pg postgresql://auser:apassword@localhost:5432/a_share --chunksize 10000
```

参数说明：
- `--sqlite`：SQLite 文件路径
- `--pg`：Postgres 连接字符串
- `--chunksize`：每次从 SQLite 读取并插入的记录数（默认 10000）
- `--drop`：如果添加该参数，会先删除目标表再重新创建导入

## 6. 验证导入

连接 Postgres 后运行：

```sql
SELECT COUNT(*) FROM stock_data;
SELECT MIN(date), MAX(date) FROM stock_data;
```

## 7. 推荐 & 注意事项

- 迁移数据量较大（百万级/千万级），请确保目标 Postgres 有足够磁盘与内存资源。
- 若要实现线上无缝切换，建议先把数据导入到新库再停机切换应用。
- 迁移后可建立索引：

```sql
CREATE INDEX idx_stock_code_date ON stock_data (code, date);
```

- 若需要持续同步（增量更新），建议编写增量同步脚本或采用基于变更日志的方案。

---

如需我在这台 Windows 机器上继续：
- A) 帮你安装并配置 PostgreSQL（我可以输出完整的安装与配置命令与验证步骤，但无法自动点击安装器）；或
- B) 等你手动安装 PostgreSQL 后，我可以帮助你执行第 2-5 步并实际运行 `sqlite_to_postgres.py` 完成迁移。

请选择接下来要我做的具体操作。