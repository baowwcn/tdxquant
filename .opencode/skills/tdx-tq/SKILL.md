---
name: tdx-tq
description: Interact with TdxQuant (通达信TQ量化投研平台) via tqcenter.py for fetching market data, building screeners/backtests, real-time quotes, trading signals, limit-up/down detection, custom stock groups, and automated trading.
---

# 通达信TQ Skill

基于 `tqcenter.py` **Version 1.0.6+**，通过 `tq` 类与通达信客户端交互。

## 重要前提

### 运行环境检测

使用本 Skill 前，**必须检测是否有运行中的 TdxW.exe 进程**：

1. 进程所在目录即为通达信安装目录（`tdx_root`）
2. 检测不到 TdxW.exe → 提示用户先启动通达信客户端
3. 找到进程但 `PYPlugins/user/tqcenter.py` 不存在 → 提示用户当前客户端不支持TQ策略，需升级
4. 多个 TdxW.exe 进程时，依次检测直到找到含 `tqcenter.py` 的目录
5. 找到后记住该 `tdx_root`，无需每次重复查找

### Python 路径配置（必须）

```python
import sys, os

# 方式一：自动从注册表读取（推荐）
import winreg
key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\通达信金融终端64"
with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
    tdx_root, _ = winreg.QueryValueEx(key, "InstallLocation")
sys.path.insert(0, os.path.join(tdx_root, 'PYPlugins', 'user'))

# 方式二：手动指定（已知安装目录时）
# sys.path.insert(0, 'E:/App/new_tdx_test64/PYPlugins/user')

from tqcenter import tq
tq.initialize(__file__)
```

**关键：使用 `sys.path.insert(0, ...)` 而非 `append()`，确保加载正确的 tqcenter.py。**

### 目录结构

```
通达信安装目录\
├── Tdxw.exe
├── PYPlugins\
│   ├── TPyth.dll            # 通信DLL（必需）
│   ├── TPythClient.dll      # 通信DLL（必需）
│   ├── user\
│   │   └── tqcenter.py      # TdxQuant核心模块
│   ├── data\                # 下载数据目录
│   └── file\                # 发送文件目录
```

## 核心接口速查

### 初始化

```python
tq.initialize(__file__)   # 必须调用
tq.close()                # 关闭连接（程序退出时自动调用）
```

### 行情数据

| 接口 | 说明 |
|------|------|
| `get_market_data(field_list, stock_list, period, ...)` | 历史K线（返回 Dict of DataFrame） |
| `get_market_snapshot(stock_code, field_list=[])` | 实时快照（单股） |
| `get_stock_info(stock_code, field_list)` | 基础信息（field_list不能为空） |
| `get_more_info(stock_code, field_list=[])` | 扩展信息（涨幅/封单/PE/市值等100+字段） |
| `get_relation(stock_code)` | 所属板块列表 |
| `get_divid_factors(stock_code, start_time, end_time)` | 分红配送数据 |
| `get_gb_info(stock_code, date_list, count)` | 股本信息 |
| `get_kzz_info(stock_code, field_list=[])` | 可转债信息 |
| `get_ipo_info(ipo_type, ipo_date)` | 新股申购信息 |
| `get_trackzs_etf_info(zs_code)` | 跟踪指数的ETF列表 |

### 专业数据

| 接口 | 说明 |
|------|------|
| `get_financial_data(stock_list, field_list, ...)` | 财务报表（FN1~FN584） |
| `get_financial_data_by_date(stock_list, field_list, year, mmdd)` | 按年季度财务数据 |
| `get_gpjy_value(stock_list, field_list, ...)` | 股票交易数据（GP01~GP46） |
| `get_gpjy_value_by_date(stock_list, field_list, year, mmdd)` | 按日期股票交易数据 |
| `get_bkjy_value(stock_list, field_list, ...)` | 板块交易数据（BK5~BK19） |
| `get_scjy_value(field_list, ...)` | 市场宏观数据（SC01~SC42，无需stock_list） |
| `get_gp_one_data(stock_list, field_list)` | 单个数据字段（GO1~GO47，当前值） |

### 股票/板块列表

| 接口 | 说明 |
|------|------|
| `get_stock_list(market='5', list_type=0)` | 市场股票列表（市场代码见参考文档） |
| `get_sector_list(list_type=0)` | 全部板块列表 |
| `get_stock_list_in_sector(block_code, block_type=0)` | 板块内股票列表 |
| `get_user_sector()` | 用户自选股板块列表 |
| `create_sector / delete_sector / rename_sector / clear_sector` | 自定义板块管理 |

### 行情订阅

| 接口 | 说明 |
|------|------|
| `refresh_cache(market='AG', force=False)` | 刷新行情缓存（一般自动触发） |
| `refresh_kline(stock_list, period)` | 刷新历史K线（仅支持1m/5m/1d） |
| `subscribe_hq(stock_list, callback)` | 订阅实时行情（最多100只，推荐每批50只） |
| `unsubscribe_hq(stock_list)` | 取消订阅 |

### 与客户端交互

| 接口 | 说明 |
|------|------|
| `send_message(msg_str)` | 发送文本到TQ策略管理界面（`\|`分行） |
| `send_file(file_path)` | 发送txt/pdf/html到客户端展示 |
| `send_warn(stock_list, ...)` | 发送预警信号到TQ信号界面 |
| `send_bt_data(stock_code, time_list, data_list, count)` | 发送回测序列数据 |
| `send_user_block(block_code, stocks, show=False)` | 发送股票到自定义板块（`block_code=''`→临时条件股） |
| `exec_to_tdx(url)` | 调用客户端功能串 |
| `print_to_tdx(df_list, ...)` | 导出DataFrame到策略数据浏览 |

### 通达信公式

| 接口 | 说明 |
|------|------|
| `formula_set_data / formula_set_data_info` | 预设K线数据（单次调用前必须） |
| `formula_zb / formula_xg / formula_exp` | 单次调用指标/选股/表达式公式 |
| `formula_process_mul_xg(...)` | **批量选股公式（推荐，无需预设数据）** |
| `formula_process_mul_zb(...)` | **批量指标公式（推荐）** |

### 交易接口

| 接口 | 说明 |
|------|------|
| `stock_account(account, account_type)` | 获取账户句柄（≥0有效） |
| `query_stock_orders(account_id, ...)` | 查询当日委托 |
| `query_stock_positions(account_id)` | 查询持仓 |
| `query_stock_asset(account_id)` | 查询账户资产 |
| `order_stock(account_id, stock_code, order_type, order_volume, price_type, price)` | 下单 |
| `cancel_order_stock(account_id, stock_code, order_id)` | 撤单 |

### 辅助工具

```python
tq.price_df(df, price_col, column_names=None)  # 从get_market_data结果中提取价格DataFrame
tq.get_trading_dates(market, start_time, end_time, count=-1)  # 交易日列表
```

## 常用字段摘要

### get_market_data 返回字段

`Date, Time, Open, High, Low, Close, Volume, Amount(万元), ForwardFactor`

### get_market_snapshot 关键字段

`Now`（现价）, `LastClose`（前收）, `Volume`（总手）, `Amount`（总成交额，**万元**，转元×10000）, `Buyp/Buyv`（五档买价量）, `Sellp/Sellv`（五档卖价量）

### get_more_info 关键字段

`FCAmo`（封单额万元，**>0=涨停，<0=跌停，=0=未封板**）, `ZTPrice`（涨停价）, `DTPrice`（跌停价）, `ZAF`（涨幅）, `Zsz`（总市值亿）, `EverZTCount`（连板天数）, `DynaPE`（动态市盈率）

## 重要注意事项

1. **涨停/跌停识别最佳实践**：盘中使用 `get_more_info` 的 `FCAmo` 字段直接判断（>0涨停，<0跌停），无需K线预筛。先 `get_stock_list` 获取全量代码，再循环 `get_more_info`，最后对确认的涨停/跌停股 `get_market_snapshot` 补充数据。

2. **Amount 单位**：`get_market_snapshot` 的 `Amount` 为**万元**，转元需 ×10000。

3. **dividend_type**：传 Python `None` 与传字符串 `'none'` 均为不复权；`'front'`=前复权，`'back'`=后复权。

4. **count 参数**：批量公式 `count` 不足会导致结果少于客户端，应覆盖公式最大回溯K线数。

5. **send_warn 规范**：`price_list/close_list/volum_list` 必须为纯数字字符串；`count` 必须 >0。

6. **实盘下单**：`order_stock` 默认返回 `Value=1`（待用户在客户端确认），自动下单需券商开通支持TQ版本。

## 参考文档

完整 API 参考（所有接口的全部字段、数据样本）：见 `references/api_reference.md`
完整使用示例（含涨停识别、批量选股、回测、预警、交易接口等）：见 `references/examples.md`