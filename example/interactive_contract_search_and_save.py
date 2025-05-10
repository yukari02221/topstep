"""
サンプルコード 3: 対話的な契約検索と1時間足データの取得、JSON保存
このサンプルでは、ユーザーが入力したシンボルで契約を検索し、対話的に選択された契約の1時間足データを取得してJSONファイルに保存します。
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
import json

# --- 設定 (必要に応じて変更してください) ---
USERNAME = "your_username"
API_KEY = "your_api_key"
USE_DEMO_ENVIRONMENT = None
OUTPUT_FILENAME_PREFIX = "contract_data"

def run_sample():
    print("--- サンプル3: 対話的契約検索と価格データ保存 ---")
    
    client = TopstepXClient(username=USERNAME, api_key=API_KEY, use_demo=USE_DEMO_ENVIRONMENT)

    if not client.authenticate(verbose=True):
        return

    search_symbol = input("検索したい契約のシンボルを入力してください (例: NQ, GC, CL): ")
    if not search_symbol:
        print("シンボルが入力されませんでした。")
        return

    # 期間の設定 (例: 直近7日間)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)

    # 対話的に契約を選択して履歴データを取得
    # search_and_get_bars は内部で select_contract と get_bars を呼び出す
    selected_contract, bars = client.search_and_get_bars(
        search_text=search_symbol,
        start_time=start_time,
        end_time=end_time,
        unit=client.UNIT_HOUR,  # 1時間足
        unit_number=1,
        limit=1000, # 最大取得件数
        # live=False, # 必要に応じて
        # include_partial_bar=False # 必要に応じて
    )

    if selected_contract and bars:
        print(f"\n{selected_contract.get('description')} の1時間足データを {len(bars)} 件取得しました。")
        client.display_bars(bars, limit=5)

        # 結果をJSONファイルに保存
        output_data = {
            "selected_contract": selected_contract,
            "bars_data": bars,
            "query_details": {
                "search_symbol": search_symbol,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "time_unit": "1 Hour"
            }
        }
        filename = f"{OUTPUT_FILENAME_PREFIX}_{selected_contract.get('name', 'unknown').replace('.', '_')}.json"
        if client.save_result_to_json(output_data, filename):
            print(f"データを {filename} に保存しました。")
        else:
            print("データのファイル保存に失敗しました。")
            
    elif selected_contract and not bars:
        print(f"{selected_contract.get('description')} は選択されましたが、指定期間の価格データが見つかりませんでした。")
    else:
        print(f"'{search_symbol}' に関連する契約が見つからないか、データ取得に失敗しました。")

if __name__ == "__main__":
    run_sample()