import sqlite3
import pandas as pd

def query_stock_data(code=None, start_date=None, end_date=None, limit=10):
    """
    查询股票数据
    :param code: 股票代码，如 '000001.SZ'
    :param start_date: 开始日期，如 '2026-03-10'
    :param end_date: 结束日期，如 '2026-04-09'
    :param limit: 返回记录数限制
    """
    conn = sqlite3.connect('a_share_monthly.db')
    query = "SELECT * FROM stock_data WHERE 1=1"
    params = []

    if code:
        query += " AND code = ?"
        params.append(code)

    if start_date:
        query += " AND date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += f" ORDER BY code, date LIMIT {limit}"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_stock_summary():
    """获取数据库统计信息"""
    conn = sqlite3.connect('a_share_monthly.db')
    cursor = conn.cursor()

    # 总股票数
    cursor.execute('SELECT COUNT(DISTINCT code) FROM stock_data')
    total_stocks = cursor.fetchone()[0]

    # 总记录数
    cursor.execute('SELECT COUNT(*) FROM stock_data')
    total_records = cursor.fetchone()[0]

    # 日期范围
    cursor.execute('SELECT MIN(date), MAX(date) FROM stock_data')
    date_range = cursor.fetchone()

    # 最新数据日期
    cursor.execute('SELECT MAX(date) FROM stock_data')
    latest_date = cursor.fetchone()[0]

    conn.close()

    return {
        'total_stocks': total_stocks,
        'total_records': total_records,
        'date_range': date_range,
        'latest_date': latest_date
    }

if __name__ == "__main__":
    # 数据库统计
    summary = get_stock_summary()
    print("=== A股数据库统计 ===")
    print(f"总股票数: {summary['total_stocks']}")
    print(f"总记录数: {summary['total_records']}")
    print(f"日期范围: {summary['date_range'][0]} 到 {summary['date_range'][1]}")
    print(f"最新数据日期: {summary['latest_date']}")

    # 示例查询
    print("\n=== 示例查询: 000001.SZ 最近5天数据 ===")
    df = query_stock_data(code='000001.SZ', limit=5)
    print(df.to_string(index=False))

    print("\n=== 示例查询: 2026-04-01 到 2026-04-09 的数据（前10条）===")
    df = query_stock_data(start_date='2026-04-01', end_date='2026-04-09', limit=10)
    print(df.to_string(index=False))