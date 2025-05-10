"""
サンプルコード 2: 特定銘柄の最新価格データ（日足）取得とPandasでの表示
このサンプルでは、指定した契約IDの過去の価格データ（日足）を取得し、Pandas DataFrameで表示します。
"""

import sys
import os

# このファイルの絶対パスを取得
current_file_path = os.path.abspath(__file__)
# このファイルのディレクトリ (example/) を取得
example_dir = os.path.dirname(current_file_path)
# 親ディレクトリ (プロジェクトのルートを想定) を取得
project_root = os.path.dirname(example_dir)

# sys.path の先頭に親ディレクトリを追加して、topstepx_clientモジュールを見つけられるようにする
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from topstep_API import TopstepXClient
from datetime import datetime, timedelta
# --- 設定 (必要に応じて変更してください) ---
USERNAME = "your_username"
API_KEY = "your_api_key"
USE_DEMO_ENVIRONMENT = None
TARGET_CONTRACT_ID = "CON.F.US.TYA.M25" # 例: E-mini S&P 500 (適宜変更)
DAYS_AGO = 30 # 何日前までのデータを取得するか

def run_sample():
    print(f"--- サンプル2: {TARGET_CONTRACT_ID} の日足データを取得しPandasで表示 ---")
    
    client = TopstepXClient(username=USERNAME, api_key=API_KEY, use_demo=USE_DEMO_ENVIRONMENT)

    if not client.authenticate(verbose=True):
        return

    # 期間の設定
    end_time = datetime.now()
    start_time = end_time - timedelta(days=DAYS_AGO)

    print(f"\n取得期間: {start_time.strftime('%Y-%m-%d')} から {end_time.strftime('%Y-%m-%d')}")

    # 履歴データ（日足）の取得
    bars = client.get_bars(
        contract_id=TARGET_CONTRACT_ID,
        start_time=start_time,
        end_time=end_time,
        unit=client.UNIT_DAY,  # 日足
        unit_number=1,
        limit=1000, # 必要に応じて調整
        verbose=True
    )

    if bars:
        print(f"\n取得したバーの数: {len(bars)}")
        client.display_bars(bars, limit=5) # 最初の5件を表示

        # Pandas DataFrameに変換
        print("\n--- Pandas DataFrameでの表示 (先頭5行) ---")
        df = client.to_pandas(bars)
        if df is not None and not df.empty:
            print(df.head())
            # 't' 列をインデックスに設定したい場合:
            # if 't' in df.columns:
            #     df = df.set_index('t')
            #     print("\nインデックス設定後:")
            #     print(df.head())
        elif df is not None and df.empty:
             print("バーデータは空でした。")
        else:
            print("Pandasがインストールされていないか、変換に失敗しました。")
            
    else:
        print(f"{TARGET_CONTRACT_ID} の価格データを取得できませんでした。")

if __name__ == "__main__":
    # Pandasをインストールしていない場合は、このサンプルはエラーになる可能性があります
    # pip install pandas
    run_sample()