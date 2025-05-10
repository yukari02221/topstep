"""
サンプルコード 1: 基本的な認証とアカウント情報の取得
このサンプルでは、クライアントを初期化し、認証を行い、アカウント情報を取得して表示します。
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

# --- 設定 (必要に応じて変更してください) ---
USERNAME = "your_username"  # ご自身のTopstepXユーザー名
API_KEY = "your_api_key"    # ご自身のTopstepX APIキー
USE_DEMO_ENVIRONMENT = None # デモ環境を使用する場合はTrue

def run_sample():
    print("--- サンプル1: アカウント情報取得 ---")
    
    # クライアントの初期化
    # 認証情報を直接指定する場合:
    client = TopstepXClient(username=USERNAME, api_key=API_KEY, use_demo=USE_DEMO_ENVIRONMENT)
    
    # 環境変数から読み込む場合 (TOPSTEPX_USERNAME, TOPSTEPX_API_KEY を設定):
    # client = TopstepXClient(use_demo=USE_DEMO_ENVIRONMENT)

    # 認証
    if not client.authenticate(verbose=True):
        print("認証に失敗しました。ユーザー名とAPIキーを確認してください。")
        return

    # すべてのアカウント情報を取得 (only_active=False)
    print("\n--- すべてのアカウント情報 ---")
    all_accounts = client.get_accounts(only_active=False, verbose=True)
    if all_accounts:
        client.display_accounts(all_accounts)
    else:
        print("アカウントが見つかりませんでした。")

    # アクティブなアカウントのみを取得
    print("\n--- アクティブなアカウント情報 ---")
    active_accounts = client.get_accounts(only_active=True, verbose=True)
    if active_accounts:
        client.display_accounts(active_accounts)
    else:
        print("アクティブなアカウントが見つかりませんでした。")

if __name__ == "__main__":
    run_sample()