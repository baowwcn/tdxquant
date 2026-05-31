---
name: etf-holdings
description: Query ETF holdings (top constituents) and holder structure (institutional/retail ratio) via EastMoney API, with optional TdxQuant real-time market data
---

# ETF 持仓 & 持有人结构查询 Skill

通过天天基金 API 查询 ETF 重仓成分股和持有人结构，并可叠加通达信实时行情。

## 前提

- **持仓模式**（默认）需要 TdxW.exe 运行并登录，因调用 `tq.get_market_snapshot` / `tq.get_more_info`
- **持有人结构模式**（`--holder`）无需通达信登录，纯 HTTP 请求

## 脚本

| 脚本 | 说明 |
|------|------|
| `query_etf_holdings.py <CODE> [--holder]` | **通用脚本（推荐）**，传基金代码即可 |
| `query_etf_515180_holdings.py` | 515180.SH 红利ETF易方达 |
| `query_etf_512170_holdings.py` | 512170.SH 医疗ETF华宝 |
| `query_etf_515220_holdings.py` | 515220.SH 煤炭ETF国泰 |

## 通用脚本用法

```bash
# 查询持仓（需通达信登录）
.venv\Scripts\python.exe query_etf_holdings.py 515180
.venv\Scripts\python.exe query_etf_holdings.py 512170.SH

# 查询持有人结构（免登录）
.venv\Scripts\python.exe query_etf_holdings.py 515220 --holder

# 查看帮助
.venv\Scripts\python.exe query_etf_holdings.py -h
```

`<CODE>` 可以是纯数字（如 `515180`）或带后缀（如 `515180.SH`），脚本会自动处理。

## 功能说明

### 持仓模式（默认）

1. 从天天基金 `FundArchivesDatas.aspx?type=jjcc` 获取披露持仓（html 正则解析）
2. 调用通达信 `get_market_snapshot` + `get_more_info` 补充实时行情
3. 输出表格：代码、名称、占净值%、最新价、总市值(亿)、涨幅%、市盈率、换手%
4. 汇总：前10大占比、沪市/深市/科创板分布

### 持有人结构模式（`--holder`）

1. 从天天基金 `FundArchivesDatas.aspx?type=cyrjg` 获取持有人结构时序数据
2. 逐年度查询（从最新往前查，找到有数据的年份即停）
3. 输出：公告日期、机构%、个人%、内部持有%、总份额(亿份)
4. 自动保存 CSV 到 `{CODE}_holder_{yyyymmdd}.csv`

## 字段说明（持仓模式）

| 列名 | 来源 | 说明 |
|------|------|------|
| 占净值% | 天天基金 | 该股票占基金净资产比例 |
| 最新价 | `get_market_snapshot` | 实时现价 |
| 总市值(亿) | `get_more_info` Zsz | 该股票总市值 |
| 涨幅% | `get_more_info` ZAF | 当日涨跌幅 |
| 市盈率 | `get_more_info` DynaPE | 动态市盈率 |
| 换手% | `get_more_info` fHSL | 换手率 |

## 基金代码参考

| 代码 | 名称 |
|------|------|
| 515180 | 红利ETF易方达 |
| 512170 | 医疗ETF华宝 |
| 515220 | 煤炭ETF国泰 |

## 数据来源说明

- **持仓数据**：天天基金 `type=jjcc`（html 表格 → 正则提取）
- **持有人结构**：天天基金 `type=cyrjg`（JavaScript variable `apidata.content` → html 解析）
- **实时行情**：通达信 TdxQuant（通过 `tqcenter.py` 调用）
- 天天基金数据无需登录，通达信数据需 TdxW.exe 运行中
