#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import sys
import getpass
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

class TopstepXClient:
    """
    TopstepX APIとの連携を行うクライアントクラス
    """
    
    def __init__(self, username: str = None, api_key: str = None, api_url: str = "https://api.topstepx.com"):
        """
        TopstepXクライアントの初期化
        
        Args:
            username (str, optional): TopstepXのユーザー名。None の場合は環境変数から取得
            api_key (str, optional): TopstepXのAPIキー。None の場合は環境変数から取得
            api_url (str, optional): APIエンドポイントのベースURL
        """
        self.api_url = api_url
        self.token = None
        self.username = username or os.getenv("TOPSTEPX_USERNAME")
        self.api_key = api_key or os.getenv("TOPSTEPX_API_KEY")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain"
        }
        
        # 認証情報が環境変数にもなく、初期化時にも提供されなかった場合は対話的に取得
        if not self.username:
            self.username = input("TopstepXユーザー名を入力: ")
        
        if not self.api_key:
            self.api_key = getpass.getpass("TopstepX APIキーを入力: ")
    
    def authenticate(self) -> bool:
        """
        APIに認証して、トークンを取得する
        
        Returns:
            bool: 認証に成功した場合はTrue、それ以外はFalse
        """
        login_url = f"{self.api_url}/api/Auth/loginKey"
        
        payload = {
            "userName": self.username,
            "apiKey": self.api_key
        }
        
        try:
            print(f"認証リクエスト送信先: {login_url}")
            response = requests.post(
                login_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                
                if data.get("success") and data.get("errorCode") == 0:
                    self.token = data.get("token")
                    
                    # トークンをヘッダーに追加
                    self.headers["Authorization"] = f"Bearer {self.token}"
                    
                    print("認証に成功しました！")
                    print(f"トークンの有効期限: 24時間")
                    return True
                else:
                    print(f"認証エラー: {data.get('errorMessage')}")
            else:
                print(f"認証エラー: {response.status_code} {response.reason}")
                print(f"エラー詳細: {response.text}")
            
            return False
        
        except Exception as e:
            print(f"認証リクエスト中にエラーが発生しました: {str(e)}")
            return False
    
    def search_accounts(self, only_active: bool = True) -> Optional[Dict[str, Any]]:
        """
        アカウントを検索する
        
        Args:
            only_active (bool): アクティブなアカウントのみを検索するかどうか
            
        Returns:
            Optional[Dict[str, Any]]: アカウント情報を含むレスポンス。失敗した場合はNone
        """
        # 認証が済んでいない場合は認証を行う
        if not self.token and not self.authenticate():
            print("認証されていません。先に認証を行ってください。")
            return None
        
        search_url = f"{self.api_url}/api/Account/search"
        
        payload = {
            "onlyActiveAccounts": only_active
        }
        
        try:
            print(f"アカウント検索リクエスト送信先: {search_url}")
            response = requests.post(
                search_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.ok:
                data = response.json()
                
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
    
    def get_accounts(self, only_active: bool = True) -> List[Dict[str, Any]]:
        """
        アカウント一覧を取得する（便利メソッド）
        
        Args:
            only_active (bool): アクティブなアカウントのみを検索するかどうか
            
        Returns:
            List[Dict[str, Any]]: アカウント情報のリスト。失敗した場合は空リスト
        """
        result = self.search_accounts(only_active)
        if result and "accounts" in result:
            return result["accounts"]
        return []
    
    def get_token(self) -> Optional[str]:
        """
        現在の認証トークンを取得する
        
        Returns:
            Optional[str]: 認証トークン。認証されていない場合はNone
        """
        return self.token
    
    def save_token(self, filename: str = "token.txt") -> bool:
        """
        現在の認証トークンをファイルに保存する
        
        Args:
            filename (str): 保存するファイル名
            
        Returns:
            bool: 保存に成功した場合はTrue、それ以外はFalse
        """
        if not self.token:
            print("トークンがありません。先に認証を行ってください。")
            return False
        
        try:
            with open(filename, "w") as f:
                f.write(self.token)
            print(f"トークンが{filename}に保存されました")
            return True
        except Exception as e:
            print(f"ファイル保存中にエラーが発生しました: {str(e)}")
            return False
    
    def load_token(self, filename: str = "token.txt") -> bool:
        """
        ファイルから認証トークンを読み込む
        
        Args:
            filename (str): 読み込むファイル名
            
        Returns:
            bool: 読み込みに成功した場合はTrue、それ以外はFalse
        """
        try:
            with open(filename, "r") as f:
                self.token = f.read().strip()
            
            # トークンをヘッダーに追加
            self.headers["Authorization"] = f"Bearer {self.token}"
            
            print(f"トークンを{filename}から読み込みました")
            return True
        except Exception as e:
            print(f"ファイル読み込み中にエラーが発生しました: {str(e)}")
            return False
    
    def save_result_to_json(self, data: Dict[str, Any], filename: str = "result.json") -> bool:
        """
        データをJSONファイルに保存する
        
        Args:
            data (Dict[str, Any]): 保存するデータ
            filename (str): 保存するファイル名
            
        Returns:
            bool: 保存に成功した場合はTrue、それ以外はFalse
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"データが{filename}に保存されました")
            return True
        except Exception as e:
            print(f"ファイル保存中にエラーが発生しました: {str(e)}")
            return False


def display_accounts(accounts: List[Dict[str, Any]]) -> None:
    """
    アカウント情報を表示する
    
    Args:
        accounts (List[Dict[str, Any]]): アカウント情報のリスト
    """
    if not accounts:
        print("アカウントが見つかりませんでした")
        return
    
    print(f"アカウント数: {len(accounts)}")
    
    for i, account in enumerate(accounts, 1):
        print(f"\nアカウント {i}:")
        print(f"  ID: {account.get('id')}")
        print(f"  名前: {account.get('name')}")
        print(f"  残高: {account.get('balance')}")
        print(f"  取引可能: {'はい' if account.get('canTrade') else 'いいえ'}")
        print(f"  表示状態: {'表示' if account.get('isVisible') else '非表示'}")


def main():
    # TopstepXクライアントの初期化
    client = TopstepXClient()
    
    # 認証する
    print("\n---- 認証処理を開始します ----")
    if not client.authenticate():
        print("認証に失敗しました。処理を終了します。")
        sys.exit(1)
    
    # 成功したらトークンの一部を表示
    token = client.get_token()
    print(f"トークン: {token[:10]}...{token[-5:]} (セキュリティのため一部表示)")
    
    # アクティブアカウントのみか全アカウントかを選択
    active_choice = input("アクティブアカウントのみ検索しますか？(y/n、デフォルト: y): ").lower()
    only_active = active_choice != 'n'
    
    # アカウント検索を実行
    print("\n---- アカウント検索を開始します ----")
    accounts = client.get_accounts(only_active)
    
    # 結果の表示
    print("\n===== アカウント検索結果 =====")
    display_accounts(accounts)

if __name__ == "__main__":
    main()