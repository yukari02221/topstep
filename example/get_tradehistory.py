"""
サンプルコード 4: アカウント選択とトレード履歴の取得、JSON保存
このサンプルでは、利用可能なアカウントを表示し、ユーザーが選択したアカウントのトレード履歴を取得してJSONファイルに保存します。
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
OUTPUT_FILENAME_PREFIX = "trades_data"

def run_sample():
    print("--- サンプル4: アカウント選択とトレード履歴取得 ---")
    
    client = TopstepXClient(username=USERNAME, api_key=API_KEY, use_demo=USE_DEMO_ENVIRONMENT)
    if not client.authenticate(verbose=True):
        return
    
    # アカウント一覧を表示して選択
    print("利用可能なアカウントを取得しています...")
    accounts = client.get_accounts(only_active=True)
    
    if not accounts:
        print("利用可能なアカウントが見つかりませんでした。")
        return
    
    print("\n利用可能なアカウント:")
    for i, account in enumerate(accounts, 1):
        print(f"{i}. ID: {account.get('id')}, 名前: {account.get('name')}, 残高: {account.get('balance', 'N/A')}")
    
    try:
        account_choice = int(input("\n取引履歴を取得するアカウントの番号を選択してください: "))
        if account_choice < 1 or account_choice > len(accounts):
            print("無効な選択です。")
            return
        
        selected_account = accounts[account_choice - 1]
        account_id = selected_account.get('id')
        
        # 期間の設定
        end_time = datetime.now()
        days_back = int(input("何日前からのトレード履歴を取得しますか？ (デフォルト: 30): ") or "30")
        start_time = end_time - timedelta(days=days_back)
        
        print(f"\n{selected_account.get('name')} (ID: {account_id}) のトレード履歴を取得しています...")
        print(f"期間: {start_time.strftime('%Y-%m-%d')} から {end_time.strftime('%Y-%m-%d')}")
        
        # トレード履歴を取得
        trades = client.get_trades(
            account_id=account_id,
            start_timestamp=start_time,
            end_timestamp=end_time,
            verbose=True
        )
        
        if not trades:
            print("指定された期間内にトレード履歴が見つかりませんでした。")
            return
        
        print(f"\n{len(trades)}件のトレード履歴を取得しました。")
        
        # トレード履歴の詳細を表示
        client.display_trades(trades, limit=10)
        
        # トレード履歴の統計情報を集計
        total_pnl = 0
        total_fees = 0
        buy_trades = 0
        sell_trades = 0
        completed_trades = 0
        
        for trade in trades:
            pnl = trade.get('profitAndLoss')
            if pnl is not None:  # 完了したトレードのみ（半立ちは除く）
                total_pnl += pnl
                completed_trades += 1
            
            total_fees += trade.get('fees', 0)
            
            if trade.get('side') == 0:
                buy_trades += 1
            elif trade.get('side') == 1:
                sell_trades += 1
        
        print("\n=== トレード統計情報 ===")
        print(f"総トレード数: {len(trades)}")
        print(f"売買内訳: 買い {buy_trades}件, 売り {sell_trades}件")
        print(f"完了したトレード: {completed_trades}件")
        print(f"合計損益: {total_pnl:.2f}")
        print(f"合計手数料: {total_fees:.2f}")
        print(f"純損益: {(total_pnl - total_fees):.2f}")
        
        # 結果をJSONファイルに保存
        save_choice = input("\nトレード履歴をJSONファイルに保存しますか？ (y/n, デフォルト: y): ").lower() or "y"
        if save_choice == "y":
            output_data = {
                "account_info": selected_account,
                "trade_history": trades,
                "statistics": {
                    "total_trades": len(trades),
                    "buy_trades": buy_trades,
                    "sell_trades": sell_trades,
                    "completed_trades": completed_trades,
                    "total_pnl": total_pnl,
                    "total_fees": total_fees,
                    "net_pnl": total_pnl - total_fees
                },
                "query_details": {
                    "account_id": account_id,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                }
            }
            
            # アカウント名からファイル名を生成 (特殊文字を除去)
            account_name_safe = ''.join(c if c.isalnum() else '_' for c in selected_account.get('name', 'unknown'))
            filename = f"{OUTPUT_FILENAME_PREFIX}_{account_name_safe}_{start_time.strftime('%Y%m%d')}.json"
            
            if client.save_result_to_json(output_data, filename):
                print(f"データを {filename} に保存しました。")
            else:
                print("データのファイル保存に失敗しました。")
    
    except ValueError:
        print("数値を入力してください。")
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    run_sample()