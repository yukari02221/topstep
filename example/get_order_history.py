"""
サンプルコード 4: 特定アカウントの特定期間における注文履歴の取得と表示
このサンプルでは、指定したアカウントIDと期間の注文履歴を取得し、表示します。
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
TARGET_ACCOUNT_ID = 4707456 # ご自身のアカウントID、またはテスト用ID
DAYS_FOR_ORDERS = 100 # 何日分の注文履歴を取得するか

def run_sample():
    print(f"--- サンプル4: アカウントID {TARGET_ACCOUNT_ID} の注文履歴取得 ---")
    
    client = TopstepXClient(username=USERNAME, api_key=API_KEY, use_demo=USE_DEMO_ENVIRONMENT)

    if not client.authenticate(verbose=True):
        return

    # 期間の設定
    end_time_orders = datetime.now()
    # APIのタイムスタンプ精度に合わせて調整が必要な場合がある
    # start_time_orders = (end_time_orders - timedelta(days=DAYS_FOR_ORDERS)).replace(hour=0, minute=0, second=0, microsecond=0)
    start_time_orders = end_time_orders - timedelta(days=DAYS_FOR_ORDERS)


    print(f"\n注文検索期間: {start_time_orders.strftime('%Y-%m-%dT%H:%M:%SZ')} から {end_time_orders.strftime('%Y-%m-%dT%H:%M:%SZ')}")

    # 注文履歴を取得
    orders = client.get_orders(
        account_id=TARGET_ACCOUNT_ID,
        start_timestamp=start_time_orders,
        end_timestamp=end_time_orders, # 省略するとAPI側で現在時刻などが使われる可能性がある
        verbose=True
    )

    if orders:
        print(f"\n取得した注文の数: {len(orders)}")
        print("--- 注文詳細 (最初の10件まで) ---")
        for i, order in enumerate(orders[:10]):
            print(f"  注文 {i+1}:")
            print(f"    ID: {order.get('id')}")
            print(f"    アカウントID: {order.get('accountId')}")
            print(f"    契約ID: {order.get('contractId')}")
            print(f"    作成日時: {order.get('creationTimestamp')}")
            # print(f"    更新日時: {order.get('updateTimestamp')}") # nullの場合が多い
            print(f"    ステータス: {order.get('status')}") # (例: 2=Filled, 1=Working, etc.)
            print(f"    タイプ: {order.get('type')}")     # (例: 1=Limit, 2=Market, etc.)
            print(f"    サイド: {order.get('side')}")     # (例: 0=Buy, 1=Sell)
            print(f"    サイズ: {order.get('size')}")
            print(f"    指値価格: {order.get('limitPrice')}") # nullの場合がある
            print(f"    逆指値価格: {order.get('stopPrice')}") # nullの場合がある
            print("-" * 20)
        if len(orders) > 10:
            print(f"...他 {len(orders) - 10} 件の注文があります。")
    else:
        print(f"アカウントID {TARGET_ACCOUNT_ID} の注文履歴を取得できませんでした、または該当期間に注文がありませんでした。")

if __name__ == "__main__":
    run_sample()