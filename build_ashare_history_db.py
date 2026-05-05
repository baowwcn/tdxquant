import os
import sqlite3
import time
import json
import sys
from datetime import datetime

import pandas as pd
from tqcenter import tq


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'ashare_daily')
DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'ashare_daily.db')
PROGRESS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'download_progress.json')


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_progress():
    """加载下载进度"""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_progress(progress):
    """保存下载进度"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def is_stock_downloaded(code):
    """检查股票是否已下载"""
    csv_file = os.path.join(DATA_DIR, f'{code}.csv')
    return os.path.exists(csv_file)


def build_stock_list():
    """获取A股列表，优先使用市场代码 5。"""
    stock_list = tq.get_stock_list(market='5')
    if not stock_list:
        stock_list = tq.get_stock_list()
    return [code for code in stock_list if code.endswith(('.SH', '.SZ'))]


def fetch_stock_history(code: str, start_time: str = '19900101', end_time: str = '', dividend_type: str = 'front', max_retries: int = 3) -> pd.DataFrame:
    """获取单只股票的日线历史数据，并转换成DataFrame。带重试机制"""
    for attempt in range(max_retries):
        try:
            result = tq.get_market_data(
                field_list=['Open', 'High', 'Low', 'Close', 'Volume', 'Amount', 'ForwardFactor'],
                stock_list=[code],
                period='1d',
                start_time=start_time,
                end_time=end_time,
                count=-1,
                dividend_type=dividend_type,
                fill_data=False,
            )

            if not result or 'ErrorId' in result:
                if attempt < max_retries - 1:
                    print(f'  {code} 第{attempt+1}次尝试失败，等待重试...')
                    time.sleep(2)
                    continue
                return pd.DataFrame()

            # 检查是否有数据
            sample_field = next(iter(result.keys()))
            if sample_field not in result or code not in result[sample_field].index:
                return pd.DataFrame()

            row = {}
            for field in result:
                if field == 'ErrorId':
                    continue
                try:
                    row[field] = result[field].loc[code]
                except KeyError:
                    return pd.DataFrame()

            df = pd.DataFrame(row)
            df.index = pd.to_datetime(df.index.astype(str), format='%Y%m%d', errors='coerce')
            df.index.name = 'Date'
            df = df.sort_index()
            return df

        except Exception as e:
            if attempt < max_retries - 1:
                print(f'  {code} 第{attempt+1}次尝试异常: {e}，等待重试...')
                time.sleep(2)
            else:
                print(f'  {code} 最终失败: {e}')
                return pd.DataFrame()

    return pd.DataFrame()


def save_to_csv(code: str, df: pd.DataFrame):
    file_path = os.path.join(DATA_DIR, f'{code}.csv')
    df.to_csv(file_path, index=True, float_format='%.6f')
    return file_path


def save_to_sqlite(code: str, df: pd.DataFrame, conn: sqlite3.Connection):
    table_name = code.replace('.', '_')
    df.reset_index(inplace=True)
    df.to_sql(table_name, conn, if_exists='replace', index=False)


def build_database(batch_size: int = 200, max_stocks: int = None):
    """构建A股历史数据库"""
    print("正在初始化TQ接口...")
    try:
        tq.initialize(__file__)
        print("TQ接口初始化成功")
    except Exception as e:
        raise RuntimeError(f"TQ接口初始化失败: {e}")

    ensure_data_dir()

    # 刷新缓存
    print("正在刷新缓存...")
    try:
        tq.refresh_cache(market='AG', force=False)
        print("缓存刷新完成")
    except Exception as e:
        print(f"缓存刷新失败: {e}")

    # 获取股票列表
    print("正在获取股票列表...")
    stock_list = build_stock_list()
    if not stock_list:
        raise RuntimeError('未能获取A股股票列表，请检查通达信客户端是否已启动并登录。')

    # 限制股票数量（如果指定）
    if max_stocks:
        stock_list = stock_list[:max_stocks]

    total_stocks = len(stock_list)
    print(f'共 {total_stocks} 只股票待处理')

    # 加载进度
    progress = load_progress()
    downloaded_count = sum(1 for code in stock_list if is_stock_downloaded(code))
    print(f'已下载 {downloaded_count}/{total_stocks} 只股票')

    # 过滤未下载的股票
    remaining_stocks = [code for code in stock_list if not is_stock_downloaded(code)]
    print(f'剩余 {len(remaining_stocks)} 只股票需要下载')

    if not remaining_stocks:
        print("所有股票已下载完成！")
        return

    conn = sqlite3.connect(DB_PATH)
    success_count = 0
    error_count = 0

    try:
        for i in range(0, len(remaining_stocks), batch_size):
            batch = remaining_stocks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(remaining_stocks) + batch_size - 1) // batch_size
            print(f'\n处理第 {batch_num}/{total_batches} 批，共 {len(batch)} 只股票...')

            batch_success = 0
            batch_error = 0

            for code in batch:
                print(f'下载 {code} 历史数据...')
                df = fetch_stock_history(code)
                if df.empty:
                    print(f'  {code} 无数据，跳过')
                    error_count += 1
                    batch_error += 1
                    continue

                try:
                    save_to_csv(code, df)
                    save_to_sqlite(code, df, conn)
                    print(f'  {code} 保存成功，{len(df)} 条记录')
                    success_count += 1
                    batch_success += 1

                    # 更新进度
                    progress[code] = {
                        'downloaded_at': datetime.now().isoformat(),
                        'records': len(df),
                        'start_date': df.index.min().strftime('%Y-%m-%d') if not df.empty else None,
                        'end_date': df.index.max().strftime('%Y-%m-%d') if not df.empty else None
                    }
                    save_progress(progress)

                except Exception as e:
                    print(f'  {code} 保存失败: {e}')
                    error_count += 1
                    batch_error += 1

                time.sleep(1)  # 每下载1个股票暂停1秒

            print(f'第 {batch_num} 批完成: 成功 {batch_success}, 失败 {batch_error}')

    finally:
        conn.close()

    # 最终统计
    total_downloaded = downloaded_count + success_count
    print("\n下载完成统计:")
    print(f"  总股票数: {total_stocks}")
    print(f"  已下载: {total_downloaded}")
    print(f"  本次成功: {success_count}")
    print(f"  本次失败: {error_count}")
    print(f"  完成率: {total_downloaded/total_stocks*100:.1f}%")


if __name__ == '__main__':
    # 命令行参数处理
    batch_size = 5  # 默认测试模式
    max_stocks = None

    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
        except:
            pass

    if len(sys.argv) > 2:
        try:
            max_stocks = int(sys.argv[2])
        except:
            pass

    print(f"启动参数: batch_size={batch_size}, max_stocks={max_stocks}")
    build_database(batch_size=batch_size, max_stocks=max_stocks)
    print('A股历史数据构建完成。数据目录：', DATA_DIR)
    print('SQLite数据库：', DB_PATH)
    print('进度文件：', PROGRESS_FILE)
