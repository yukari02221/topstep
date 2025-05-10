import requests
import json
import os
import sys
import getpass
from dotenv import load_dotenv

load_dotenv()

# 本番環境のAPIえんどポイント
API_URL = "https://api.topstepx.com"

def get_auth_token(username, api_key):
    """
    TopstepX APIの認証トークンを取得する
    
    Args:
        username (str): ユーザー名
        api_key (str): APIキー

    Returns:
        str: 認証トークン。失敗した場合はNone
    """
    # ログインエンドポイント
    login_url = f"{API_URL}/api/Auth/loginKey"
    
    # リクエストヘッダー
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain"
    }
    
    # リクエストボディ
    payload = {
        "userName": username,
        "apiKey": api_key
    }
    
    try:
        # POSTリクエストを送信
        print(f"認証リクエスト送信先: {login_url}")
        response = requests.post(
            login_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        # レスポンスの処理
        if response.ok:
            data = response.json()
            
            # 成功を確認
            if data.get("success") and data.get("errorCode") == 0:
                token = data.get("token")
                print("認証に成功しました！")
                print(f"トークンの有効期限: 24時間")
                
                # トークンを返す
                return token
            else:
                print(f"認証エラー: {data.get('errorMessage')}")
        else:
            print(f"認証エラー: {response.status_code} {response.reason}")
            print(f"エラー詳細: {response.text}")
        
        return None
    
    except Exception as e:
        print(f"認証リクエスト中にエラーが発生しました: {str(e)}")
        return None    

def search_accounts(token, only_active=True):
    """
    アカウントを検索する
    
    Args:
        token (str): 認証トークン
        only_active (bool): アクティブなアカウントのみを検索するかどうか
        
    Returns:
        dict: アカウント情報を含むレスポンス。失敗した場合はNone
    """
    # アカウント検索エンドポイント
    search_url = f"{API_URL}/api/Account/search"
    
    # リクエストヘッダー
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "text/plain"
    }
    
    # リクエストボディ
    payload = {
        "onlyActiveAccounts": only_active
    }        
    try:
        # POSTリクエストを送信
        print(f"アカウント検索リクエスト送信先: {search_url}")
        response = requests.post(
            search_url,
            headers=headers,
            data=json.dumps(payload),
            timeout=10
        )
        
        # レスポンスの処理
        if response.ok:
            data = response.json()
            
            # 成功を確認
            if data.get("success") and data.get("errorCode") == 0:
                return data
            else:
                print(f"検索エラー: {data.get('errorMessage')}")
        else:
            print(f"検索エラー: {response.status_code} {response.reason}")
            if response.text:
                print(f"エラー詳細: {response.text}")
        
        return None
    
    except Exception as e:
        print(f"アカウント検索中にエラーが発生しました: {str(e)}")
        return None

def main():
    username = os.getenv("TOPSTEPX_USERNAME")
    api_key = os.getenv("TOPSTEPX_API_KEY")
    
    # 認証情報がない場合はプロンプトで入力を求める
    if not username:
        username = input("TopstepXユーザー名を入力: ")
    
    if not api_key:
        api_key = getpass.getpass("TopstepX APIキーを入力: ")
    
    # アクティブアカウントのみか全アカウントかを選択
    active_choice = input("アクティブアカウントのみ検索しますか？(y/n、デフォルト: y): ").lower()
    only_active = active_choice != 'n'
    
    # 認証トークンを取得
    print("\n---- 認証処理を開始します ----")
    token = get_auth_token(username, api_key)
    
    if not token:
        print("認証に失敗しました。処理を終了します。")
        sys.exit(1)    

    # 成功したらトークンの一部を表示
    print(f"トークン: {token[:10]}...{token[-5:]} (セキュリティのため一部表示)")
    
    # アカウント検索を実行
    print("\n---- アカウント検索を開始します ----")
    result = search_accounts(token, only_active)

    # 結果の表示
    if result:
        accounts = result.get("accounts", [])
        print("\n===== アカウント検索結果 =====")
        
        if accounts:
            print(f"アカウント数: {len(accounts)}")
            
            # アカウント情報を表示
            for i, account in enumerate(accounts, 1):
                print(f"\nアカウント {i}:")
                print(f"  ID: {account.get('id')}")
                print(f"  名前: {account.get('name')}")
                print(f"  残高: {account.get('balance')}")
                print(f"  取引可能: {'はい' if account.get('canTrade') else 'いいえ'}")
                print(f"  表示状態: {'表示' if account.get('isVisible') else '非表示'}")
        else:
            print("アカウントが見つかりませんでした")
    else:
        print("\nアカウント検索に失敗しました")

if __name__=="__main__":
    main()