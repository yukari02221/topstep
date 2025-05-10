#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
import sys
import getpass
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
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

    def retrieve_bars(self,
                      contract_id: str,
                      start_time: Union[str, datetime],
                      end_time: Union[str, datetime],
                      unit: int = 2,
                      unit_number: int = 1,
                      limit: int = 1000,
                      live: bool = False,
                      include_partial_bar: bool = False) -> Optional[Dict[str, Any]]:
        """
        履歴データ（バー）を取得する
        
        Args:
            contract_id (str): 取得する契約ID
            start_time (Union[str, datetime]): 開始時間（ISO8601形式の文字列またはdatetimeオブジェクト）
            end_time (Union[str, datetime]): 終了時間（ISO8601形式の文字列またはdatetimeオブジェクト）
            unit (int, optional): 時間単位（1=秒, 2=分, 3=時間, 4=日, 5=週, 6=月）。デフォルトは2（分）
            unit_number (int, optional): 単位数。デフォルトは1
            limit (int, optional): 取得する最大バー数。デフォルトは1000
            live (bool, optional): ライブデータを使用するかどうか。デフォルトはFalse
            include_partial_bar (bool, optional): 現在の時間単位の部分的なバーを含めるかどうか。デフォルトはFalse
            
        Returns:
            Optional[Dict[str, Any]]: 履歴データを含むレスポンス。失敗した場合はNone
        """
        # 認証が済んでいない場合は認証を行う
        if not self.token and not self.authenticate():
            print("認証されていません。先に認証を行ってください。")
            return None
        
        # datetimeオブジェクトをISO8601形式の文字列に変換
        if isinstance(start_time, datetime):
            start_time = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        if isinstance(end_time, datetime):
            end_time = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        retrieve_url = f"{self.api_url}/api/History/retrieveBars"        
        payload = {
            "contractId": contract_id,
            "live": live,
            "startTime": start_time,
            "endTime": end_time,
            "unit": unit,
            "unitNumber": unit_number,
            "limit": limit,
            "includePartialBar": include_partial_bar
        }
        try:
            print(f"履歴データ取得リクエスト送信先: {retrieve_url}")
            response = requests.post(
                retrieve_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=60
            )
            
            if response.ok:
                data = response.json()
                
                if data.get("success") and data.get("errorCode") == 0:
                    return data
                else:
                    print(f"履歴データ取得エラー: {data.get('errorMessage')}")
            else:
                print(f"履歴データ取得エラー: {response.status_code} {response.reason}")
                if response.text:
                    print(f"エラー詳細: {response.text}")
            
            return None
        
        except Exception as e:
            print(f"履歴データ取得中にエラーが発生しました: {str(e)}")
            return None

    def get_bars(self, 
                contract_id: str, 
                start_time: Union[str, datetime], 
                end_time: Union[str, datetime], 
                unit: int = 2,
                unit_number: int = 1, 
                limit: int = 1000, 
                live: bool = False, 
                include_partial_bar: bool = False) -> List[Dict[str, Any]]:
        """
        履歴データ（バー）のリストを取得する（便利メソッド）
        
        Args:
            contract_id (str): 取得する契約ID
            start_time (Union[str, datetime]): 開始時間
            end_time (Union[str, datetime]): 終了時間
            unit (int, optional): 時間単位（1=秒, 2=分, 3=時間, 4=日, 5=週, 6=月）
            unit_number (int, optional): 単位数
            limit (int, optional): 取得する最大バー数
            live (bool, optional): ライブデータを使用するかどうか
            include_partial_bar (bool, optional): 現在の時間単位の部分的なバーを含めるかどうか
            
        Returns:
            List[Dict[str, Any]]: 履歴データのリスト。失敗した場合は空リスト
        """
        result = self.retrieve_bars(
            contract_id=contract_id,
            start_time=start_time,
            end_time=end_time,
            unit=unit,
            unit_number=unit_number,
            limit=limit,
            live=live,
            include_partial_bar=include_partial_bar
        )
        
        if result and "bars" in result:
            return result["bars"]
        return []
    
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

def display_bars(bars: List[Dict[str, Any]], limit: int = 10) -> None:
    """
    履歴データ（バー）を表示する
    
    Args:
        bars (List[Dict[str, Any]]): 履歴データのリスト
        limit (int, optional): 表示する最大バー数。デフォルトは10
    """
    if not bars:
        print("履歴データが見つかりませんでした")
        return
    
    print(f"取得したバー数: {len(bars)}")
    
    # 表示するバー数を制限
    display_bars = bars[:min(limit, len(bars))]
    
    # テーブルヘッダーを表示
    print("\n日時                    | 始値      | 高値      | 安値      | 終値      | 出来高")
    print("-" * 80)
    
    # バーデータを表示
    for bar in display_bars:
        time_str = bar.get("t", "")[:19].replace("T", " ")  # ISO8601形式から日時部分のみを抽出
        open_price = bar.get("o", 0)
        high_price = bar.get("h", 0)
        low_price = bar.get("l", 0)
        close_price = bar.get("c", 0)
        volume = bar.get("v", 0)
        
        print(f"{time_str} | {open_price:<9.2f} | {high_price:<9.2f} | {low_price:<9.2f} | {close_price:<9.2f} | {volume}")
    
    # 表示されていないバーがある場合
    if len(bars) > limit:
        print(f"\n... 他 {len(bars) - limit} 件のバーデータがあります")

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
    
    # 機能を選択
    print("\n実行する機能を選択してください:")
    print("1. アカウント検索")
    print("2. 履歴データ（バー）の取得")
    choice = input("選択（1または2）: ")
    
    if choice == "1":
        # アクティブアカウントのみか全アカウントかを選択
        active_choice = input("アクティブアカウントのみ検索しますか？(y/n、デフォルト: y): ").lower()
        only_active = active_choice != 'n'
        
        # アカウント検索を実行
        print("\n---- アカウント検索を開始します ----")
        accounts = client.get_accounts(only_active)
        
        # 結果の表示
        print("\n===== アカウント検索結果 =====")
        display_accounts(accounts)
        
    elif choice == "2":
        # 履歴データの取得に必要なパラメータを入力
        contract_id = input("契約ID（例: CON.F.US.RTY.Z24）: ")
        
        # デフォルトの時間範囲を設定（過去30日間）
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        # 時間範囲のカスタマイズ
        custom_range = input(f"カスタム期間を指定しますか？(y/n、デフォルト: n、デフォルト期間: {start_time.date()} から {end_time.date()}): ").lower()
        
        if custom_range == 'y':
            start_date_str = input("開始日（YYYY-MM-DD）: ")
            try:
                start_time = datetime.strptime(start_date_str, "%Y-%m-%d")
            except ValueError:
                print(f"無効な日付形式です。デフォルトの開始日（{start_time.date()}）を使用します。")
            
            end_date_str = input("終了日（YYYY-MM-DD）: ")
            try:
                end_time = datetime.strptime(end_date_str, "%Y-%m-%d")
                # 終了日の23:59:59に設定
                end_time = end_time.replace(hour=23, minute=59, second=59)
            except ValueError:
                print(f"無効な日付形式です。デフォルトの終了日（{end_time.date()}）を使用します。")
        
        # 時間単位の選択
        print("\n時間単位を選択してください:")
        print("1. 秒")
        print("2. 分")
        print("3. 時間")
        print("4. 日")
        print("5. 週")
        print("6. 月")
        unit_choice = input("選択（1-6、デフォルト: 2）: ") or "2"
        unit = int(unit_choice) if unit_choice.isdigit() and 1 <= int(unit_choice) <= 6 else 2
        
        # 単位数の入力
        unit_number_str = input("単位数（デフォルト: 1）: ") or "1"
        unit_number = int(unit_number_str) if unit_number_str.isdigit() and int(unit_number_str) > 0 else 1
        
        # 取得するバー数の上限
        limit_str = input("取得する最大バー数（デフォルト: 1000）: ") or "1000"
        limit = int(limit_str) if limit_str.isdigit() and int(limit_str) > 0 else 1000
        
        # ライブデータを使用するかどうか
        live_choice = input("ライブデータを使用しますか？(y/n、デフォルト: n): ").lower()
        live = live_choice == 'y'
        
        # 部分的なバーを含めるかどうか
        partial_choice = input("現在の時間単位の部分的なバーを含めますか？(y/n、デフォルト: n): ").lower()
        include_partial_bar = partial_choice == 'y'
        
        # 履歴データの取得
        print("\n---- 履歴データの取得を開始します ----")
        bars = client.get_bars(
            contract_id=contract_id,
            start_time=start_time,
            end_time=end_time,
            unit=unit,
            unit_number=unit_number,
            limit=limit,
            live=live,
            include_partial_bar=include_partial_bar
        )
        
        # 結果の表示
        print("\n===== 履歴データ取得結果 =====")
        display_bars(bars)
        
        # 結果をJSONファイルに保存するかどうか
        if bars:
            save_result_choice = input("\n取得した履歴データをJSONファイルに保存しますか？(y/n、デフォルト: n): ").lower()
            if save_result_choice == 'y':
                result_filename = input("ファイル名を入力 (デフォルト: bars.json): ") or "bars.json"
                result_data = {"bars": bars, "success": True, "errorCode": 0, "errorMessage": None}
                client.save_result_to_json(result_data, result_filename)
    
    else:
        print("無効な選択です。処理を終了します。")

if __name__ == "__main__":
    main()