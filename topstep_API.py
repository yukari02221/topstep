#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TopstepX API Client

TopstepXのAPIと連携して、アカウント情報の取得、契約検索、価格データ取得などの機能を提供します。

使用例:
    from topstepx_client import TopstepXClient
    
    # クライアントの初期化
    client = TopstepXClient(username="your_username", api_key="your_api_key")
    
    # または環境変数から認証情報を読み込む場合
    # export TOPSTEPX_USERNAME=your_username
    # export TOPSTEPX_API_KEY=your_api_key
    # client = TopstepXClient()
    
    # 認証
    if client.authenticate():
        # アカウント情報の取得
        accounts = client.get_accounts()
        
        # 契約検索
        contracts = client.get_contracts("RTY")
        
        # 価格データの取得
        bars = client.get_bars(
            contract_id="CON.F.US.RTY.Z24",
            start_time="2025-04-01T00:00:00Z",
            end_time="2025-05-01T00:00:00Z",
            unit=3,  # 時間足
            unit_number=1
        )

依存関係:
    - requests: HTTPリクエスト用
    - python-dotenv: 環境変数読み込み用
"""

import requests
import json
import os
import sys
import getpass
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()  # .envファイルから環境変数を読み込む
except ImportError:
    print("注意: python-dotenvがインストールされていません。環境変数を使用する場合はインストールしてください。")
    print("pip install python-dotenv")

class TopstepXClient:
    """
    TopstepX APIとの連携を行うクライアントクラス
    
    Attributes:
        api_url (str): TopstepX APIのベースURL
        username (str): TopstepXのユーザー名
        api_key (str): TopstepXのAPIキー
        token (str): 認証後に設定される認証トークン
        headers (dict): API呼び出し時に使用されるHTTPヘッダー
    """
    # 時間単位の定義
    UNIT_SECOND = 1
    UNIT_MINUTE = 2
    UNIT_HOUR = 3
    UNIT_DAY = 4
    UNIT_WEEK = 5
    UNIT_MONTH = 6
    
    # 注文タイプの定義
    ORDER_TYPE_LIMIT = 1
    ORDER_TYPE_MARKET = 2 
    ORDER_TYPE_STOP = 4
    ORDER_TYPE_TRAILING_STOP = 5
    ORDER_TYPE_JOIN_BID = 6
    ORDER_TYPE_JOIN_ASK = 7

    # 注文方向の定義
    ORDER_SIDE_BUY = 0
    ORDER_SIDE_SELL = 1
    
    # APIエンドポイント
    DEFAULT_API_URL = "https://api.topstepx.com"
    DEMO_API_URL = "https://gateway-api-demo.s2f.projectx.com"
    
    def __init__(self, username: str = None, api_key: str = None, api_url: str = DEFAULT_API_URL, use_demo: bool = False):
        """
        TopstepXクライアントの初期化
        
        Args:
            username (str, optional): TopstepXのユーザー名。None の場合は環境変数から取得
            api_key (str, optional): TopstepXのAPIキー。None の場合は環境変数から取得
            api_url (str, optional): APIエンドポイントのベースURL
            use_demo (bool, optional): Trueの場合はデモ環境のAPIを使用する
        """
        if use_demo:
            self.api_url = self.DEMO_API_URL
        else:
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
    
    def authenticate(self, verbose: bool = True) -> bool:
        """
        APIに認証して、トークンを取得する
        
        Args:
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか
            
        Returns:
            bool: 認証に成功した場合はTrue、それ以外はFalse
        """
        login_url = f"{self.api_url}/api/Auth/loginKey"
        
        payload = {
            "userName": self.username,
            "apiKey": self.api_key
        }
        
        try:
            if verbose:
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
                    
                    if verbose:
                        print("認証に成功しました！")
                        print(f"トークンの有効期限: 24時間")
                    return True
                else:
                    if verbose:
                        print(f"認証エラー: {data.get('errorMessage')}")
            else:
                if verbose:
                    print(f"認証エラー: {response.status_code} {response.reason}")
                    print(f"エラー詳細: {response.text}")
            
            return False
        
        except Exception as e:
            if verbose:
                print(f"認証リクエスト中にエラーが発生しました: {str(e)}")
            return False

    def check_auth(self) -> bool:
        """
        認証状態をチェックし、必要に応じて認証を行う
        
        Returns:
            bool: 認証トークンが利用可能な場合はTrue、認証に失敗した場合はFalse
        """
        if not self.token:
            return self.authenticate(verbose=False)
        return True
    
    def search_accounts(self, only_active: bool = True, verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        アカウントを検索する
        
        Args:
            only_active (bool): アクティブなアカウントのみを検索するかどうか
            verbose (bool): 詳細なログメッセージを表示するかどうか
            
        Returns:
            Optional[Dict[str, Any]]: アカウント情報を含むレスポンス。失敗した場合はNone
        """
        # 認証が済んでいない場合は認証を行う
        if not self.check_auth():
            if verbose:
                print("認証されていません。先に認証を行ってください。")
            return None
        
        search_url = f"{self.api_url}/api/Account/search"
        
        payload = {
            "onlyActiveAccounts": only_active
        }
        
        try:
            if verbose:
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
                    if verbose:
                        print(f"検索エラー: {data.get('errorMessage')}")
            else:
                if verbose:
                    print(f"検索エラー: {response.status_code} {response.reason}")
                    if response.text:
                        print(f"エラー詳細: {response.text}")
            
            return None
        
        except Exception as e:
            if verbose:
                print(f"アカウント検索中にエラーが発生しました: {str(e)}")
            return None

    def search_contracts(self, search_text: str = "", live: bool = False, verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        契約を検索する
        
        Args:
            search_text (str): 検索するテキスト（契約名や一部）
            live (bool): ライブデータを使用するかどうか
            verbose (bool): 詳細なログメッセージを表示するかどうか
            
        Returns:
            Optional[Dict[str, Any]]: 契約情報を含むレスポンス。失敗した場合はNone
        """
        # 認証が済んでいない場合は認証を行う
        if not self.check_auth():
            if verbose:
                print("認証されていません。先に認証を行ってください。")
            return None
        
        search_url = f"{self.api_url}/api/Contract/search"
        
        payload = {
            "searchText": search_text,
            "live": live
        }
        
        try:
            if verbose:
                print(f"契約検索リクエスト送信先: {search_url}")
            
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
                    if verbose:
                        print(f"契約検索エラー: {data.get('errorMessage')}")
            else:
                if verbose:
                    print(f"契約検索エラー: {response.status_code} {response.reason}")
                    if response.text:
                        print(f"エラー詳細: {response.text}")
            
            return None
        
        except Exception as e:
            if verbose:
                print(f"契約検索中にエラーが発生しました: {str(e)}")
            return None

    def get_contracts(self, search_text: str = "", live: bool = False, verbose: bool = True) -> List[Dict[str, Any]]:
        """
        契約情報のリストを取得する（便利メソッド）
        
        Args:
            search_text (str): 検索するテキスト
            live (bool): ライブデータを使用するかどうか
            verbose (bool): 詳細なログメッセージを表示するかどうか
            
        Returns:
            List[Dict[str, Any]]: 契約情報のリスト。失敗した場合は空リスト
        """
        result = self.search_contracts(search_text, live, verbose)
        if result and "contracts" in result:
            return result["contracts"]
        return []

    def select_contract(self, search_text: str = "", live: bool = False) -> Optional[Dict[str, Any]]:
        """
        契約を検索し、ユーザーに選択させる（対話型メソッド）
        
        Args:
            search_text (str): 検索するテキスト
            live (bool): ライブデータを使用するかどうか
            
        Returns:
            Optional[Dict[str, Any]]: 選択された契約情報。キャンセルされた場合はNone
        """
        contracts = self.get_contracts(search_text, live)
        
        if not contracts:
            print(f"検索テキスト '{search_text}' に一致する契約が見つかりませんでした")
            return None
        
        print(f"\n==== 検索結果: {len(contracts)}件の契約が見つかりました ====")
        
        for i, contract in enumerate(contracts, 1):
            print(f"{i}. {contract.get('name')} - {contract.get('description')}")
            print(f"   ID: {contract.get('id')}")
            print(f"   ティックサイズ: {contract.get('tickSize')}, ティック値: {contract.get('tickValue')}")
            print(f"   アクティブ契約: {'はい' if contract.get('activeContract') else 'いいえ'}")
            print()
        
        while True:
            try:
                choice = input("使用する契約の番号を選択してください (1-{0}), または 'q' で中止: ".format(len(contracts)))
                
                if choice.lower() == 'q':
                    return None
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(contracts):
                    selected_contract = contracts[choice_idx]
                    print(f"\n選択された契約: {selected_contract.get('name')} - {selected_contract.get('description')}")
                    return selected_contract
                else:
                    print("無効な選択です。1から{0}までの数字を入力してください".format(len(contracts)))
            
            except ValueError:
                print("数字を入力してください")

    def retrieve_bars(self,
                      contract_id: str,
                      start_time: Union[str, datetime],
                      end_time: Union[str, datetime],
                      unit: int = UNIT_MINUTE,
                      unit_number: int = 1,
                      limit: int = 1000,
                      live: bool = False,
                      include_partial_bar: bool = False,
                      verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        履歴データ（バー）を取得する
        
        Args:
            contract_id (str): 取得する契約ID
            start_time (Union[str, datetime]): 開始時間（ISO8601形式の文字列またはdatetimeオブジェクト）
            end_time (Union[str, datetime]): 終了時間（ISO8601形式の文字列またはdatetimeオブジェクト）
            unit (int, optional): 時間単位 - UNIT_SECOND(1), UNIT_MINUTE(2), UNIT_HOUR(3), 
                                 UNIT_DAY(4), UNIT_WEEK(5), UNIT_MONTH(6)
            unit_number (int, optional): 単位数。デフォルトは1
            limit (int, optional): 取得する最大バー数。デフォルトは1000
            live (bool, optional): ライブデータを使用するかどうか。デフォルトはFalse
            include_partial_bar (bool, optional): 現在の時間単位の部分的なバーを含めるかどうか。デフォルトはFalse
            verbose (bool): 詳細なログメッセージを表示するかどうか
            
        Returns:
            Optional[Dict[str, Any]]: 履歴データを含むレスポンス。失敗した場合はNone
        """
        # 認証が済んでいない場合は認証を行う
        if not self.check_auth():
            if verbose:
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
            if verbose:
                print(f"履歴データ取得リクエスト送信先: {retrieve_url}")
                print(f"契約ID: {contract_id}")
                print(f"期間: {start_time} から {end_time}")
                print(f"単位: {unit}, 単位数: {unit_number}, 上限: {limit}バー")
            
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
                    if verbose:
                        print(f"履歴データ取得エラー: {data.get('errorMessage')}")
            else:
                if verbose:
                    print(f"履歴データ取得エラー: {response.status_code} {response.reason}")
                    if response.text:
                        print(f"エラー詳細: {response.text}")
            
            return None
        
        except Exception as e:
            if verbose:
                print(f"履歴データ取得中にエラーが発生しました: {str(e)}")
            return None
        
    def get_bars(self, 
                contract_id: str, 
                start_time: Union[str, datetime], 
                end_time: Union[str, datetime], 
                unit: int = UNIT_MINUTE,
                unit_number: int = 1, 
                limit: int = 1000, 
                live: bool = False, 
                include_partial_bar: bool = False,
                verbose: bool = True) -> List[Dict[str, Any]]:
        """
        履歴データ（バー）のリストを取得する（便利メソッド）
        
        Args:
            contract_id (str): 取得する契約ID
            start_time (Union[str, datetime]): 開始時間
            end_time (Union[str, datetime]): 終了時間
            unit (int, optional): 時間単位 - UNIT_SECOND(1), UNIT_MINUTE(2), UNIT_HOUR(3), 
                                 UNIT_DAY(4), UNIT_WEEK(5), UNIT_MONTH(6)
            unit_number (int, optional): 単位数
            limit (int, optional): 取得する最大バー数
            live (bool, optional): ライブデータを使用するかどうか
            include_partial_bar (bool, optional): 現在の時間単位の部分的なバーを含めるかどうか
            verbose (bool): 詳細なログメッセージを表示するかどうか
            
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
            include_partial_bar=include_partial_bar,
            verbose=verbose
        )
        
        if result and "bars" in result:
            return result["bars"]
        return []
    
    def search_and_get_bars(self, 
                           search_text: str,
                           start_time: Union[str, datetime], 
                           end_time: Union[str, datetime], 
                           unit: int = UNIT_MINUTE,
                           unit_number: int = 1, 
                           limit: int = 1000, 
                           live: bool = False, 
                           include_partial_bar: bool = False) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        契約を検索し、選択された契約の履歴データを取得する（対話型メソッド）
        
        Args:
            search_text (str): 検索するテキスト
            start_time (Union[str, datetime]): 開始時間
            end_time (Union[str, datetime]): 終了時間
            unit (int, optional): 時間単位 - UNIT_SECOND(1), UNIT_MINUTE(2), UNIT_HOUR(3), 
                                 UNIT_DAY(4), UNIT_WEEK(5), UNIT_MONTH(6)
            unit_number (int, optional): 単位数
            limit (int, optional): 取得する最大バー数
            live (bool, optional): ライブデータを使用するかどうか
            include_partial_bar (bool, optional): 現在の時間単位の部分的なバーを含めるかどうか
            
        Returns:
            Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]: (選択された契約, 履歴データのリスト)
        """
        # 契約を検索して選択
        selected_contract = self.select_contract(search_text, live)
        
        if not selected_contract:
            print("契約が選択されませんでした")
            return None, []
        
        # 選択された契約IDで履歴データを取得
        contract_id = selected_contract.get("id")
        
        print(f"\n{selected_contract.get('description')}の履歴データを取得します...")
        
        bars = self.get_bars(
            contract_id=contract_id,
            start_time=start_time,
            end_time=end_time,
            unit=unit,
            unit_number=unit_number,
            limit=limit,
            live=live,
            include_partial_bar=include_partial_bar
        )
        
        if bars:
            print(f"{len(bars)}件のバーデータを取得しました")
        else:
            print("バーデータを取得できませんでした")
        
        return selected_contract, bars

    def search_orders(self,
                      account_id: int,
                      start_timestamp: Union[str, datetime],
                      end_timestamp: Optional[Union[str, datetime]] = None,
                      verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        指定されたアカウントIDと期間で注文を検索する

        Args:
            account_id (int): 検索対象のアカウントID
            start_timestamp (Union[str, datetime]): 検索期間の開始日時 (ISO8601形式文字列またはdatetimeオブジェクト)
            end_timestamp (Optional[Union[str, datetime]], optional): 検索期間の終了日時 (ISO8601形式文字列またはdatetimeオブジェクト)。
                                                                  デフォルトはNone。
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか。デフォルトはTrue。

        Returns:
            Optional[Dict[str, Any]]: 注文情報を含むAPIレスポンス。失敗した場合はNone。
        """
        if not self.check_auth():
            if verbose:
                print("認証されていません。先に認証を行ってください。")
            return None

        # datetimeオブジェクトをISO8601形式の文字列に変換
        if isinstance(start_timestamp, datetime):
            start_timestamp_str = start_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            start_timestamp_str = start_timestamp

        end_timestamp_str: Optional[str] = None
        if isinstance(end_timestamp, datetime):
            end_timestamp_str = end_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif isinstance(end_timestamp, str):
            end_timestamp_str = end_timestamp

        search_url = f"{self.api_url}/api/Order/search"
        
        payload: Dict[str, Any] = {
            "accountId": account_id,
            "startTimestamp": start_timestamp_str
        }
        if end_timestamp_str:
            payload["endTimestamp"] = end_timestamp_str                
        try:
            if verbose:
                print(f"注文検索リクエスト送信先: {search_url}")
                print(f"ペイロード: {json.dumps(payload)}")

            response = requests.post(
                search_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30 # 必要に応じて調整
            )

            if response.ok:
                data = response.json()
                if data.get("success") and data.get("errorCode") == 0:
                    if verbose:
                        print(f"注文検索に成功しました。取得件数: {len(data.get('orders', []))}")
                    return data
                else:
                    if verbose:
                        print(f"注文検索APIエラー: {data.get('errorMessage')}")
                        print(f"エラーコード: {data.get('errorCode')}")
            else:
                if verbose:
                    print(f"注文検索リクエストエラー: {response.status_code} {response.reason}")
                    if response.text:
                        print(f"エラー詳細: {response.text}")
            
            return None

        except Exception as e:
            if verbose:
                print(f"注文検索中にエラーが発生しました: {str(e)}")
            return None

    def get_orders(self,
                   account_id: int,
                   start_timestamp: Union[str, datetime],
                   end_timestamp: Optional[Union[str, datetime]] = None,
                   verbose: bool = True) -> List[Dict[str, Any]]:
        """
        指定されたアカウントIDと期間で注文リストを取得する（便利メソッド）

        Args:
            account_id (int): 検索対象のアカウントID
            start_timestamp (Union[str, datetime]): 検索期間の開始日時
            end_timestamp (Optional[Union[str, datetime]], optional): 検索期間の終了日時。デフォルトはNone。
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか。デフォルトはTrue。

        Returns:
            List[Dict[str, Any]]: 注文情報のリスト。失敗した場合は空リスト。
        """
        result = self.search_orders(
            account_id=account_id,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            verbose=verbose
        )
        if result and "orders" in result:
            return result["orders"]
        return []

    def select_account(self, only_active: bool = True, verbose_selection: bool = True) -> Optional[Dict[str, Any]]:
        """
        アカウントを検索し、ユーザーに対話的に選択させる。

        Args:
            only_active (bool, optional): アクティブなアカウントのみを検索対象とするか。デフォルトはTrue。
            verbose_selection (bool, optional): アカウント選択プロセス中のメッセージを表示するか。デフォルトはTrue。

        Returns:
            Optional[Dict[str, Any]]: 選択されたアカウント情報。キャンセルされた場合や見つからない場合はNone。
        """
        # アカウントリストを取得 (このメソッド内でのAPIエラー詳細は表示しないことが多いので verbose=False)
        accounts = self.get_accounts(only_active=only_active, verbose=False)

        if not accounts:
            if verbose_selection:
                print("利用可能なアカウントが見つかりませんでした。")
            return None

        if verbose_selection:
            print(f"\n==== 利用可能なアカウント: {len(accounts)}件 ====")
            for i, account in enumerate(accounts, 1):
                print(f"{i}. ID: {account.get('id')}, "
                      f"名前: {account.get('name')}, "
                      f"残高: {account.get('balance', 'N/A')}, " # balance がない場合も考慮
                      f"取引可能: {'はい' if account.get('canTrade') else 'いいえ'}")

        while True:
            try:
                choice_str = input(f"使用するアカウントの番号を選択してください (1-{len(accounts)}), または 'q' で中止: ")
                if choice_str.lower() == 'q':
                    if verbose_selection:
                        print("アカウント選択を中止しました。")
                    return None
                
                choice_idx = int(choice_str) - 1
                if 0 <= choice_idx < len(accounts):
                    selected_account = accounts[choice_idx]
                    if verbose_selection:
                        print(f"\n選択されたアカウント: ID={selected_account.get('id')}, 名前={selected_account.get('name')}")
                    return selected_account
                else:
                    if verbose_selection:
                        print(f"無効な選択です。1から{len(accounts)}までの数字を入力してください。")
            except ValueError:
                if verbose_selection:
                    print("数字を入力するか、'q'で中止してください。")
            except Exception as e:
                if verbose_selection:
                    print(f"アカウント選択中にエラーが発生しました: {str(e)}")
                return None #予期せぬエラーの場合はNoneを返す

    def search_trades(self,
                    account_id: int,
                    start_timestamp: Union[str, datetime],
                    end_timestamp: Optional[Union[str, datetime]] = None,
                    verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        指定されたアカウントIDと期間でトレード履歴を検索する

        Args:
            account_id (int): 検索対象のアカウントID
            start_timestamp (Union[str, datetime]): 検索期間の開始日時 (ISO8601形式文字列またはdatetimeオブジェクト)
            end_timestamp (Optional[Union[str, datetime]], optional): 検索期間の終了日時 (ISO8601形式文字列またはdatetimeオブジェクト)。
                                                                デフォルトはNone。
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか。デフォルトはTrue。

        Returns:
            Optional[Dict[str, Any]]: トレード情報を含むAPIレスポンス。失敗した場合はNone。
        """
        if not self.check_auth():
            if verbose:
                print("認証されていません。先に認証を行ってください。")
            return None

        # datetimeオブジェクトをISO8601形式の文字列に変換
        if isinstance(start_timestamp, datetime):
            start_timestamp_str = start_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            start_timestamp_str = start_timestamp

        end_timestamp_str: Optional[str] = None
        if isinstance(end_timestamp, datetime):
            end_timestamp_str = end_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif isinstance(end_timestamp, str):
            end_timestamp_str = end_timestamp

        search_url = f"{self.api_url}/api/Trade/search"
        
        payload: Dict[str, Any] = {
            "accountId": account_id,
            "startTimestamp": start_timestamp_str
        }
        if end_timestamp_str:
            payload["endTimestamp"] = end_timestamp_str                
        try:
            if verbose:
                print(f"トレード検索リクエスト送信先: {search_url}")
                print(f"ペイロード: {json.dumps(payload)}")

            response = requests.post(
                search_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )

            if response.ok:
                data = response.json()
                if data.get("success") and data.get("errorCode") == 0:
                    if verbose:
                        print(f"トレード検索に成功しました。取得件数: {len(data.get('trades', []))}")
                    return data
                else:
                    if verbose:
                        print(f"トレード検索APIエラー: {data.get('errorMessage')}")
                        print(f"エラーコード: {data.get('errorCode')}")
            else:
                if verbose:
                    print(f"トレード検索リクエストエラー: {response.status_code} {response.reason}")
                    if response.text:
                        print(f"エラー詳細: {response.text}")
            
            return None

        except Exception as e:
            if verbose:
                print(f"トレード検索中にエラーが発生しました: {str(e)}")
            return None

    def get_trades(self,
                account_id: int,
                start_timestamp: Union[str, datetime],
                end_timestamp: Optional[Union[str, datetime]] = None,
                verbose: bool = True) -> List[Dict[str, Any]]:
        """
        指定されたアカウントIDと期間でトレード履歴リストを取得する（便利メソッド）

        Args:
            account_id (int): 検索対象のアカウントID
            start_timestamp (Union[str, datetime]): 検索期間の開始日時
            end_timestamp (Optional[Union[str, datetime]], optional): 検索期間の終了日時。デフォルトはNone。
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか。デフォルトはTrue。

        Returns:
            List[Dict[str, Any]]: トレード情報のリスト。失敗した場合は空リスト。
        """
        result = self.search_trades(
            account_id=account_id,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            verbose=verbose
        )
        if result and "trades" in result:
            return result["trades"]
        return []
    
    def get_accounts(self, only_active: bool = True, verbose: bool = True) -> List[Dict[str, Any]]:
        """
        アカウント一覧を取得する（便利メソッド）
        
        Args:
            only_active (bool): アクティブなアカウントのみを検索するかどうか
            verbose (bool): 詳細なログメッセージを表示するかどうか
            
        Returns:
            List[Dict[str, Any]]: アカウント情報のリスト。失敗した場合は空リスト
        """
        result = self.search_accounts(only_active, verbose)
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

    def place_order(self,
                    account_id: int,
                    contract_id: str,
                    order_type: int,
                    side: int,
                    size: int,
                    limit_price: Optional[float] = None,
                    stop_price: Optional[float] = None,
                    trail_price: Optional[float] = None,
                    custom_tag: Optional[str] = None,
                    linked_order_id: Optional[int] = None,
                    verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        注文を発注する
        
        Args:
            account_id (int): 注文を発注するアカウントID
            contract_id (str): 注文対象の契約ID
            order_type (int): 注文タイプ - 1=指値(Limit), 2=成行(Market), 4=逆指値(Stop), 
                            5=トレイリングストップ(TrailingStop), 6=買い気配値(JoinBid), 7=売り気配値(JoinAsk)
            side (int): 注文の方向 - 0=買い(Bid/Buy), 1=売り(Ask/Sell)
            size (int): 注文数量
            limit_price (float, optional): 指値注文の価格（該当する場合）
            stop_price (float, optional): 逆指値注文の価格（該当する場合）
            trail_price (float, optional): トレイリングストップの値幅（該当する場合）
            custom_tag (str, optional): 注文に付けるカスタムタグ
            linked_order_id (int, optional): 関連付ける注文ID
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか。デフォルトはTrue
            
        Returns:
            Optional[Dict[str, Any]]: 注文結果を含むAPIレスポンス。失敗した場合はNone
        """
        # 認証が済んでいない場合は認証を行う
        if not self.check_auth():
            if verbose:
                print("認証されていません。先に認証を行ってください。")
            return None

        order_url = f"{self.api_url}/api/Order/place"
        
        # 注文タイプの名称マッピング（ログ表示用）
        order_type_names = {
            1: "指値(Limit)",
            2: "成行(Market)",
            4: "逆指値(Stop)",
            5: "トレイリングストップ(TrailingStop)",
            6: "買い気配値(JoinBid)",
            7: "売り気配値(JoinAsk)"
        }
        
        # 注文方向の名称マッピング（ログ表示用）
        side_names = {
            0: "買い(Bid/Buy)",
            1: "売り(Ask/Sell)"
        }
        
        payload = {
            "accountId": account_id,
            "contractId": contract_id,
            "type": order_type,
            "side": side,
            "size": size,
            "limitPrice": limit_price,
            "stopPrice": stop_price,
            "trailPrice": trail_price,
            "customTag": custom_tag,
            "linkedOrderId": linked_order_id
        }

        try:
            if verbose:
                print(f"注文発注リクエスト送信先: {order_url}")
                print(f"アカウントID: {account_id}")
                print(f"契約ID: {contract_id}")
                print(f"注文タイプ: {order_type_names.get(order_type, order_type)}")
                print(f"方向: {side_names.get(side, side)}")
                print(f"数量: {size}")
                
                if limit_price is not None:
                    print(f"指値価格: {limit_price}")
                if stop_price is not None:
                    print(f"逆指値価格: {stop_price}")
                if trail_price is not None:
                    print(f"トレイリング値幅: {trail_price}")
                if custom_tag:
                    print(f"カスタムタグ: {custom_tag}")
                if linked_order_id:
                    print(f"関連注文ID: {linked_order_id}")
            
            response = requests.post(
                order_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                
                if data.get("success") and data.get("errorCode") == 0:
                    if verbose:
                        print(f"注文発注に成功しました！注文ID: {data.get('orderId')}")
                    return data
                else:
                    if verbose:
                        print(f"注文発注エラー: {data.get('errorMessage')}")
                        print(f"エラーコード: {data.get('errorCode')}")
            else:
                if verbose:
                    print(f"注文発注リクエストエラー: {response.status_code} {response.reason}")
                    if response.text:
                        print(f"エラー詳細: {response.text}")
            
            return None
        
        except Exception as e:
            if verbose:
                print(f"注文発注中にエラーが発生しました: {str(e)}")
            return None

    def search_open_orders(self,
                        account_id: int,
                        verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        指定されたアカウントIDのオープンオーダー（未約定の注文）を検索する

        Args:
            account_id (int): 検索対象のアカウントID
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか。デフォルトはTrue。

        Returns:
            Optional[Dict[str, Any]]: オープンオーダー情報を含むAPIレスポンス。失敗した場合はNone。
        """
        if not self.check_auth():
            if verbose:
                print("認証されていません。先に認証を行ってください。")
            return None

        search_url = f"{self.api_url}/api/Order/searchOpen"
        
        payload = {
            "accountId": account_id
        }
                
        try:
            if verbose:
                print(f"オープンオーダー検索リクエスト送信先: {search_url}")
                print(f"アカウントID: {account_id}")

            response = requests.post(
                search_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )

            if response.ok:
                data = response.json()
                if data.get("success") and data.get("errorCode") == 0:
                    if verbose:
                        print(f"オープンオーダー検索に成功しました。取得件数: {len(data.get('orders', []))}")
                    return data
                else:
                    if verbose:
                        print(f"オープンオーダー検索APIエラー: {data.get('errorMessage')}")
                        print(f"エラーコード: {data.get('errorCode')}")
            else:
                if verbose:
                    print(f"オープンオーダー検索リクエストエラー: {response.status_code} {response.reason}")
                    if response.text:
                        print(f"エラー詳細: {response.text}")
            
            return None

        except Exception as e:
            if verbose:
                print(f"オープンオーダー検索中にエラーが発生しました: {str(e)}")
            return None

    def get_open_orders(self,
                        account_id: int,
                        verbose: bool = True) -> List[Dict[str, Any]]:
        """
        指定されたアカウントIDのオープンオーダー（未約定の注文）リストを取得する（便利メソッド）

        Args:
            account_id (int): 検索対象のアカウントID
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか。デフォルトはTrue。

        Returns:
            List[Dict[str, Any]]: オープンオーダー情報のリスト。失敗した場合は空リスト。
        """
        result = self.search_open_orders(
            account_id=account_id,
            verbose=verbose
        )
        if result and "orders" in result:
            return result["orders"]
        return []

    def display_orders(self, orders: List[Dict[str, Any]], limit: int = 10) -> None:
        """
        注文情報を表示する
        
        Args:
            orders (List[Dict[str, Any]]): 注文情報のリスト
            limit (int, optional): 表示する最大注文数。デフォルトは10
        """
        if not orders:
            print("注文が見つかりませんでした")
            return
        
        print(f"取得した注文数: {len(orders)}")
        
        # 表示する注文数を制限
        display_orders = orders[:min(limit, len(orders))]
        
        # ステータスの名称マッピング
        status_map = {
            0: "不明",
            1: "オープン",
            2: "部分約定",
            3: "約定済",
            4: "キャンセル",
            5: "拒否",
            6: "期限切れ"
        }
        
        # 注文タイプの名称マッピング
        type_map = {
            1: "指値(Limit)",
            2: "成行(Market)",
            4: "逆指値(Stop)",
            5: "トレイリングストップ(TrailingStop)",
            6: "買い気配値(JoinBid)",
            7: "売り気配値(JoinAsk)"
        }
        
        # サイド（売買）の表示用マッピング
        side_map = {0: "買", 1: "売"}
        
        # テーブルヘッダーを表示
        print("\nID    | 契約ID           | 日時                    | 状態   | タイプ             | 方向 | サイズ | 指値価格  | 逆指値価格")
        print("-" * 110)
        
        # 注文データを表示
        for order in display_orders:
            order_id = order.get("id", "N/A")
            contract_id = order.get("contractId", "N/A")
            time_str = order.get("creationTimestamp", "")[:19].replace("T", " ")  # ISO8601形式から日時部分のみを抽出
            
            status = status_map.get(order.get("status", 0), "不明")
            order_type = type_map.get(order.get("type", 0), "不明")
            side = side_map.get(order.get("side", -1), "不明")
            size = order.get("size", 0)
            
            limit_price = order.get("limitPrice")
            limit_price_str = f"{limit_price:<9.3f}" if limit_price is not None else "N/A     "
            
            stop_price = order.get("stopPrice")
            stop_price_str = f"{stop_price:<9.3f}" if stop_price is not None else "N/A     "
            
            print(f"{order_id:<8} | {contract_id:<17} | {time_str} | {status:<6} | {order_type:<18} | {side}  | {size:<6} | {limit_price_str} | {stop_price_str}")
        
        # 表示されていない注文がある場合
        if len(orders) > limit:
            print(f"\n... 他 {len(orders) - limit} 件の注文データがあります")

    def cancel_order(self,
                    account_id: int,
                    order_id: int,
                    verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        指定された注文をキャンセルする

        Args:
            account_id (int): 対象のアカウントID
            order_id (int): キャンセルする注文ID
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか。デフォルトはTrue。

        Returns:
            Optional[Dict[str, Any]]: APIレスポンス。失敗した場合はNone。
        """
        # 認証が済んでいない場合は認証を行う
        if not self.check_auth():
            if verbose:
                print("認証されていません。先に認証を行ってください。")
            return None
        
        cancel_url = f"{self.api_url}/api/Order/cancel"
        
        payload = {
            "accountId": account_id,
            "orderId": order_id
        }
        
        try:
            if verbose:
                print(f"注文キャンセルリクエスト送信先: {cancel_url}")
                print(f"アカウントID: {account_id}")
                print(f"注文ID: {order_id}")
            
            response = requests.post(
                cancel_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                
                if data.get("success") and data.get("errorCode") == 0:
                    if verbose:
                        print(f"注文ID {order_id} のキャンセルに成功しました！")
                    return data
                else:
                    if verbose:
                        print(f"注文キャンセルエラー: {data.get('errorMessage')}")
                        print(f"エラーコード: {data.get('errorCode')}")
            else:
                if verbose:
                    print(f"注文キャンセルリクエストエラー: {response.status_code} {response.reason}")
                    if response.text:
                        print(f"エラー詳細: {response.text}")
            
            return None
        
        except Exception as e:
            if verbose:
                print(f"注文キャンセル中にエラーが発生しました: {str(e)}")
            return None

    def cancel_open_order_by_index(self, account_id: int, index: int = 0) -> Optional[Dict[str, Any]]:
        """
        指定されたアカウントのオープンオーダーを取得し、インデックスで指定された注文をキャンセルする
        
        Args:
            account_id (int): 対象のアカウントID
            index (int, optional): キャンセルするオープンオーダーのインデックス（0から始まる）。デフォルトは0（最新の注文）。
            
        Returns:
            Optional[Dict[str, Any]]: キャンセル操作のAPIレスポンス。失敗した場合はNone。
        """
        # オープンオーダーを取得
        open_orders = self.get_open_orders(account_id, verbose=False)
        
        if not open_orders:
            print(f"アカウントID {account_id} にオープンオーダーはありません。")
            return None
        
        if index < 0 or index >= len(open_orders):
            print(f"無効なインデックスです。0から{len(open_orders)-1}までの数値を指定してください。")
            return None
        
        target_order = open_orders[index]
        order_id = target_order.get("id")
        
        if not order_id:
            print("注文IDが見つかりませんでした。")
            return None
        
        # 注文情報を表示
        print(f"\n以下の注文をキャンセルします:")
        print(f"  注文ID: {order_id}")
        print(f"  契約ID: {target_order.get('contractId')}")
        print(f"  種類: {self.get_order_type_name(target_order.get('type'))}")
        print(f"  方向: {self.get_order_side_name(target_order.get('side'))}")
        print(f"  サイズ: {target_order.get('size')}")
        
        # 確認
        confirm = input("この注文をキャンセルしますか？(y/n): ").lower()
        if confirm != 'y':
            print("キャンセルを中止しました。")
            return None
        
        # 注文をキャンセル
        return self.cancel_order(account_id, order_id)

    def get_order_type_name(self, order_type: int) -> str:
        """
        注文タイプの数値を名前に変換する
        
        Args:
            order_type (int): 注文タイプ
                
        Returns:
            str: 注文タイプの名前
        """
        type_map = {
            1: "指値(Limit)",
            2: "成行(Market)",
            4: "逆指値(Stop)",
            5: "トレイリングストップ(TrailingStop)",
            6: "買い気配値(JoinBid)",
            7: "売り気配値(JoinAsk)"
        }
        return type_map.get(order_type, f"不明({order_type})")

    def get_order_side_name(self, side: int) -> str:
        """
        注文方向の数値を名前に変換する
        
        Args:
            side (int): 注文方向
                
        Returns:
            str: 注文方向の名前
        """
        side_map = {
            0: "買い(Bid/Buy)",
            1: "売り(Ask/Sell)"
        }
        return side_map.get(side, f"不明({side})")
    
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

    def modify_order(self,
                    account_id: int,
                    order_id: int,
                    size: Optional[int] = None,
                    limit_price: Optional[float] = None,
                    stop_price: Optional[float] = None,
                    trail_price: Optional[float] = None,
                    verbose: bool = True) -> Optional[Dict[str, Any]]:
        """
        オープンオーダー（未約定の注文）を修正する

        Args:
            account_id (int): 対象のアカウントID
            order_id (int): 修正する注文ID
            size (Optional[int], optional): 新しい注文数量。Noneの場合は変更しない
            limit_price (Optional[float], optional): 新しい指値価格。Noneの場合は変更しない
            stop_price (Optional[float], optional): 新しい逆指値価格。Noneの場合は変更しない
            trail_price (Optional[float], optional): 新しいトレイリング値幅。Noneの場合は変更しない
            verbose (bool, optional): 詳細なログメッセージを表示するかどうか。デフォルトはTrue

        Returns:
            Optional[Dict[str, Any]]: APIレスポンス。失敗した場合はNone
        """
        # 認証が済んでいない場合は認証を行う
        if not self.check_auth():
            if verbose:
                print("認証されていません。先に認証を行ってください。")
            return None
        
        modify_url = f"{self.api_url}/api/Order/modify"
        
        # 必須パラメータ
        payload = {
            "accountId": account_id,
            "orderId": order_id
        }
        
        # オプションパラメータ（指定された場合のみ追加）
        if size is not None:
            payload["size"] = size
        
        # 以下は常に含める必要があるパラメータ（APIの仕様に従う）
        payload["limitPrice"] = limit_price
        payload["stopPrice"] = stop_price
        payload["trailPrice"] = trail_price
        
        try:
            if verbose:
                print(f"注文修正リクエスト送信先: {modify_url}")
                print(f"アカウントID: {account_id}")
                print(f"注文ID: {order_id}")
                
                if size is not None:
                    print(f"新しい数量: {size}")
                if limit_price is not None:
                    print(f"新しい指値価格: {limit_price}")
                if stop_price is not None:
                    print(f"新しい逆指値価格: {stop_price}")
                if trail_price is not None:
                    print(f"新しいトレイリング値幅: {trail_price}")
            
            response = requests.post(
                modify_url,
                headers=self.headers,
                data=json.dumps(payload),
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                
                if data.get("success") and data.get("errorCode") == 0:
                    if verbose:
                        print(f"注文ID {order_id} の修正に成功しました！")
                    return data
                else:
                    if verbose:
                        print(f"注文修正エラー: {data.get('errorMessage')}")
                        print(f"エラーコード: {data.get('errorCode')}")
            else:
                if verbose:
                    print(f"注文修正リクエストエラー: {response.status_code} {response.reason}")
                    if response.text:
                        print(f"エラー詳細: {response.text}")
            
            return None
        
        except Exception as e:
            if verbose:
                print(f"注文修正中にエラーが発生しました: {str(e)}")
            return None

    def modify_open_order_by_index(self, account_id: int, index: int = 0) -> Optional[Dict[str, Any]]:
        """
        指定されたアカウントのオープンオーダーを取得し、インデックスで指定された注文を修正する
        
        Args:
            account_id (int): 対象のアカウントID
            index (int, optional): 修正するオープンオーダーのインデックス（0から始まる）。デフォルトは0（最新の注文）。
            
        Returns:
            Optional[Dict[str, Any]]: 修正操作のAPIレスポンス。失敗した場合はNone。
        """
        # オープンオーダーを取得
        open_orders = self.get_open_orders(account_id, verbose=False)
        
        if not open_orders:
            print(f"アカウントID {account_id} にオープンオーダーはありません。")
            return None
        
        if index < 0 or index >= len(open_orders):
            print(f"無効なインデックスです。0から{len(open_orders)-1}までの数値を指定してください。")
            return None
        
        target_order = open_orders[index]
        order_id = target_order.get("id")
        
        if not order_id:
            print("注文IDが見つかりませんでした。")
            return None
        
        # 注文情報を表示
        print(f"\n以下の注文を修正します:")
        print(f"  注文ID: {order_id}")
        print(f"  契約ID: {target_order.get('contractId')}")
        print(f"  種類: {self.get_order_type_name(target_order.get('type'))}")
        print(f"  方向: {self.get_order_side_name(target_order.get('side'))}")
        print(f"  現在のサイズ: {target_order.get('size')}")
        
        current_limit_price = target_order.get('limitPrice')
        current_stop_price = target_order.get('stopPrice')
        current_trail_price = target_order.get('trailPrice')
        
        if current_limit_price is not None:
            print(f"  現在の指値価格: {current_limit_price}")
        if current_stop_price is not None:
            print(f"  現在の逆指値価格: {current_stop_price}")
        if current_trail_price is not None:
            print(f"  現在のトレイリング値幅: {current_trail_price}")
        
        # 修正値の入力
        print("\n修正する値を入力してください（変更しない場合は空欄）:")
        
        # サイズの修正
        size_input = input(f"新しいサイズ （現在: {target_order.get('size')}）: ")
        new_size = int(size_input) if size_input.strip() else None
        
        # 価格の修正
        new_limit_price = None
        new_stop_price = None
        new_trail_price = None
        
        # 注文タイプに応じて適切な価格入力フィールドを表示
        order_type = target_order.get('type')
        
        if order_type == self.ORDER_TYPE_LIMIT:
            limit_input = input(f"新しい指値価格 （現在: {current_limit_price}）: ")
            new_limit_price = float(limit_input) if limit_input.strip() else current_limit_price
        
        elif order_type == self.ORDER_TYPE_STOP:
            stop_input = input(f"新しい逆指値価格 （現在: {current_stop_price}）: ")
            new_stop_price = float(stop_input) if stop_input.strip() else current_stop_price
        
        elif order_type == self.ORDER_TYPE_TRAILING_STOP:
            trail_input = input(f"新しいトレイリング値幅 （現在: {current_trail_price}）: ")
            new_trail_price = float(trail_input) if trail_input.strip() else current_trail_price
        
        # 確認
        print("\n===== 修正内容の確認 =====")
        print(f"  注文ID: {order_id}")
        
        if new_size is not None:
            print(f"  サイズ: {target_order.get('size')} → {new_size}")
        
        if new_limit_price is not None and new_limit_price != current_limit_price:
            print(f"  指値価格: {current_limit_price} → {new_limit_price}")
        
        if new_stop_price is not None and new_stop_price != current_stop_price:
            print(f"  逆指値価格: {current_stop_price} → {new_stop_price}")
        
        if new_trail_price is not None and new_trail_price != current_trail_price:
            print(f"  トレイリング値幅: {current_trail_price} → {new_trail_price}")
        
        confirm = input("\nこの内容で注文を修正しますか？(y/n): ").lower()
        if confirm != 'y':
            print("修正を中止しました。")
            return None
        
        # 注文を修正
        return self.modify_order(
            account_id=account_id,
            order_id=order_id,
            size=new_size,
            limit_price=new_limit_price,
            stop_price=new_stop_price,
            trail_price=new_trail_price
        )

    @staticmethod
    def get_time_unit_name(unit: int) -> str:
        """
        時間単位の数値を名前に変換する
        
        Args:
            unit (int): 時間単位（1=秒, 2=分, 3=時間, 4=日, 5=週, 6=月）
            
        Returns:
            str: 時間単位の名前
        """
        unit_names = {
            1: "秒",
            2: "分",
            3: "時間",
            4: "日",
            5: "週",
            6: "月"
        }
        return unit_names.get(unit, "不明")

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def display_trades(trades: List[Dict[str, Any]], limit: int = 10) -> None:
        """
        トレード履歴を表示する
        
        Args:
            trades (List[Dict[str, Any]]): トレード履歴のリスト
            limit (int, optional): 表示する最大トレード数。デフォルトは10
        """
        if not trades:
            print("トレード履歴が見つかりませんでした")
            return
        
        print(f"取得したトレード数: {len(trades)}")
        
        # 表示するトレード数を制限
        display_trades = trades[:min(limit, len(trades))]
        
        # テーブルヘッダーを表示
        print("\nID    | 契約ID           | 日時                    | 価格      | 損益      | 手数料   | 売買 | サイズ | 注文ID")
        print("-" * 100)
        
        # サイド（売買）の表示用マッピング
        side_map = {0: "買", 1: "売"}
        
        # トレードデータを表示
        for trade in display_trades:
            trade_id = trade.get("id", "N/A")
            contract_id = trade.get("contractId", "N/A")
            time_str = trade.get("creationTimestamp", "")[:19].replace("T", " ")  # ISO8601形式から日時部分のみを抽出
            price = trade.get("price", 0)
            
            # ここが問題の箇所 - profitAndLossがNoneの場合の処理
            pnl = trade.get("profitAndLoss")
            if pnl is None:
                pnl_str = "N/A     "  # NoneならN/Aとして表示（空白でパディング）
            else:
                pnl_str = f"{pnl:<9.3f}"
                
            fees = trade.get("fees", 0)
            side = side_map.get(trade.get("side", -1), "不明")
            size = trade.get("size", 0)
            order_id = trade.get("orderId", "N/A")
            
            print(f"{trade_id:<8} | {contract_id:<17} | {time_str} | {price:<9.3f} | {pnl_str} | {fees:<7.4f} | {side}  | {size:<6} | {order_id}")
        
        # 表示されていないトレードがある場合
        if len(trades) > limit:
            print(f"\n... 他 {len(trades) - limit} 件のトレードデータがあります")

    def to_pandas(self, bars: List[Dict[str, Any]]) -> Any:
        """
        履歴データをPandasのDataFrameに変換する
        
        Args:
            bars (List[Dict[str, Any]]): 履歴データのリスト
            
        Returns:
            pandas.DataFrame: 変換されたDataFrame。Pandasがインストールされていない場合はNone
            
        Note:
            このメソッドを使用するには、pandasがインストールされている必要があります。
            インストールされていない場合はエラーメッセージが表示されます。
        """
        try:
            import pandas as pd
            
            if not bars:
                return pd.DataFrame()
            
            df = pd.DataFrame(bars)
            
            # 日時列をdatetime型に変換
            if 't' in df.columns:
                df['t'] = pd.to_datetime(df['t'])
            
            return df
        
        except ImportError:
            print("Pandasがインストールされていません。DataFrameへの変換を行うには以下のコマンドでインストールしてください:")
            print("pip install pandas")
            return None

# コマンドラインから直接実行された場合のエントリーポイント
def main():
    """
    TopstepXClientの主要機能を対話的に実行するコマンドラインインターフェース
    """
    # TopstepXクライアントの初期化
    print("TopstepX API クライアント")
    print("-" * 50)
    
    # デモ環境の選択
    use_demo = input("デモ環境を使用しますか？(y/n、デフォルト: n): ").lower() == 'y'
    
    client = TopstepXClient(use_demo=use_demo)
    
    # 認証する
    print("\n---- 認証処理を開始します ----")
    if not client.authenticate():
        print("認証に失敗しました。処理を終了します。")
        sys.exit(1)
    
    # 成功したらトークンの一部を表示
    token = client.get_token()
    print(f"トークン: {token[:10]}...{token[-5:]} (セキュリティのため一部表示)")
    
    # 機能を選択
    while True:
        print("\n実行する機能を選択してください:")
        print("1. アカウント検索")
        print("2. 契約検索")
        print("3. 契約検索から履歴データ取得")
        print("4. 契約IDを直接指定して履歴データ取得")
        print("5. アカウント検索後、指定したIDの注文履歴を取得")
        print("6. アカウント検索後、指定したIDのトレード履歴を取得")
        print("7. 注文発注")
        print("8. オープンオーダー検索")
        print("9. 注文キャンセル")
        print("10. 注文修正")
        print("0. 終了")
        
        choice = input("選択（0-10）: ")
        
        if choice == "0":
            print("プログラムを終了します。")
            break
        
        elif choice == "1":
            # アクティブアカウントのみか全アカウントかを選択
            active_choice = input("アクティブアカウントのみ検索しますか？(y/n、デフォルト: y): ").lower()
            only_active = active_choice != 'n'
            
            # アカウント検索を実行
            print("\n---- アカウント検索を開始します ----")
            accounts = client.get_accounts(only_active)
            
            # 結果の表示
            print("\n===== アカウント検索結果 =====")
            client.display_accounts(accounts)
        
        elif choice == "2":
            # 契約検索
            search_text = input("検索するテキストを入力（例: ES, NQ, RTY）: ")
            
            live_choice = input("ライブデータを使用しますか？(y/n、デフォルト: n): ").lower()
            live = live_choice == 'y'
            
            # 契約検索を実行
            print("\n---- 契約検索を開始します ----")
            contracts = client.get_contracts(search_text, live)
            
            # 結果の表示
            print("\n===== 契約検索結果 =====")
            
            if contracts:
                print(f"{len(contracts)}件の契約が見つかりました:")
                
                for i, contract in enumerate(contracts, 1):
                    print(f"\n契約 {i}:")
                    print(f"  ID: {contract.get('id')}")
                    print(f"  名前: {contract.get('name')}")
                    print(f"  説明: {contract.get('description')}")
                    print(f"  ティックサイズ: {contract.get('tickSize')}")
                    print(f"  ティック値: {contract.get('tickValue')}")
                    print(f"  アクティブ契約: {'はい' if contract.get('activeContract') else 'いいえ'}")
                
                # 結果を保存するかどうか
                save_result_choice = input("\n検索結果をJSONファイルに保存しますか？(y/n、デフォルト: n): ").lower()
                if save_result_choice == 'y':
                    result_filename = input("ファイル名を入力 (デフォルト: contracts.json): ") or "contracts.json"
                    result_data = {"contracts": contracts, "success": True, "errorCode": 0, "errorMessage": None}
                    client.save_result_to_json(result_data, result_filename)
            else:
                print("契約が見つかりませんでした")
        
        elif choice == "3":
            # 契約検索から履歴データ取得
            search_text = input("検索するテキストを入力（例: ES, NQ, RTY）: ")
            
            # ライブデータを使用するかどうか
            live_choice = input("ライブデータを使用しますか？(y/n、デフォルト: n): ").lower()
            live = live_choice == 'y'
            
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
            
            # 部分的なバーを含めるかどうか
            partial_choice = input("現在の時間単位の部分的なバーを含めますか？(y/n、デフォルト: n): ").lower()
            include_partial_bar = partial_choice == 'y'
            
            # 契約検索から履歴データ取得
            print("\n---- 契約検索と履歴データ取得を開始します ----")
            selected_contract, bars = client.search_and_get_bars(
                search_text=search_text,
                start_time=start_time,
                end_time=end_time,
                unit=unit,
                unit_number=unit_number,
                limit=limit,
                live=live,
                include_partial_bar=include_partial_bar
            )
            
            if selected_contract and bars:
                # 結果の表示
                print(f"\n===== {selected_contract.get('description')}の履歴データ =====")
                print(f"時間単位: {unit_number}{client.get_time_unit_name(unit)}")
                print(f"期間: {start_time.date()} から {end_time.date()}")
                
                client.display_bars(bars)
                
                # 結果をJSONファイルに保存するかどうか
                save_result_choice = input("\n取得した履歴データをJSONファイルに保存しますか？(y/n、デフォルト: n): ").lower()
                if save_result_choice == 'y':
                    symbol = selected_contract.get('name', '').lower()
                    result_filename = input(f"ファイル名を入力 (デフォルト: {symbol}_bars.json): ") or f"{symbol}_bars.json"
                    
                    result_data = {
                        "contract": selected_contract,
                        "bars": bars,
                        "unit": unit,
                        "unitNumber": unit_number,
                        "startTime": start_time.isoformat() if isinstance(start_time, datetime) else start_time,
                        "endTime": end_time.isoformat() if isinstance(end_time, datetime) else end_time,
                        "success": True,
                        "errorCode": 0,
                        "errorMessage": None
                    }
                    
                    client.save_result_to_json(result_data, result_filename)
        
        elif choice == "4":
            # 契約IDを直接指定して履歴データ取得
            contract_id = input("契約IDを入力（例: CON.F.US.RTY.Z24）: ")
            
            # ライブデータを使用するかどうか
            live_choice = input("ライブデータを使用しますか？(y/n、デフォルト: n): ").lower()
            live = live_choice == 'y'
            
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
            
            # 部分的なバーを含めるかどうか
            partial_choice = input("現在の時間単位の部分的なバーを含めますか？(y/n、デフォルト: n): ").lower()
            include_partial_bar = partial_choice == 'y'
            
            # 履歴データの取得
            print("\n---- 履歴データの取得を開始します ----")
            print(f"契約ID: {contract_id}")
            print(f"期間: {start_time.date()} から {end_time.date()}")
            print(f"時間単位: {unit_number}{client.get_time_unit_name(unit)}")
            
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
            
            if bars:
                # 結果の表示
                print(f"\n===== 契約ID: {contract_id}の履歴データ =====")
                client.display_bars(bars)
                
                # 結果をJSONファイルに保存するかどうか
                save_result_choice = input("\n取得した履歴データをJSONファイルに保存しますか？(y/n、デフォルト: n): ").lower()
                if save_result_choice == 'y':
                    # 契約IDから簡易的なファイル名を生成
                    file_prefix = contract_id.split('.')[-2].lower() if len(contract_id.split('.')) > 2 else "contract"
                    result_filename = input(f"ファイル名を入力 (デフォルト: {file_prefix}_bars.json): ") or f"{file_prefix}_bars.json"
                    
                    result_data = {
                        "contractId": contract_id,
                        "bars": bars,
                        "unit": unit,
                        "unitNumber": unit_number,
                        "startTime": start_time.isoformat() if isinstance(start_time, datetime) else start_time,
                        "endTime": end_time.isoformat() if isinstance(end_time, datetime) else end_time,
                        "success": True,
                        "errorCode": 0,
                        "errorMessage": None
                    }
                    
                    client.save_result_to_json(result_data, result_filename)
            else:
                print(f"契約ID '{contract_id}' の履歴データを取得できませんでした。")
                print("契約IDが正しいか確認してください。")

        elif choice == "5": # 注文検索
            print("\n---- 注文検索を開始します ----")
            try:
                # --- アカウントID選択部分の変更 ---
                print("まず、注文を検索するアカウントを選択してください。")
                # only_active=True は適宜変更してください
                selected_account_info = client.select_account(only_active=True, verbose_selection=True)

                if not selected_account_info:
                    continue 

                account_id = selected_account_info.get("id")
                if account_id is None: # 万が一IDが取得できなかった場合
                    print("エラー: 選択されたアカウントからIDを取得できませんでした。注文検索を中止します。")
                    continue
                
                print(f"アカウントID {account_id} の注文を検索します。")
                # --- アカウントID選択部分の変更ここまで ---
                
                # デフォルトの時間範囲を設定（過去7日間）
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=7)
                
                custom_range = input(f"カスタム期間を指定しますか？(y/n、デフォルト: n、期間: {start_dt.date()} から {end_dt.date()}): ").lower()
                if custom_range == 'y':
                    start_date_str = input(f"開始日（YYYY-MM-DD、デフォルト: {start_dt.strftime('%Y-%m-%d')}）: ") or start_dt.strftime("%Y-%m-%d")
                    end_date_str = input(f"終了日（YYYY-MM-DD、デフォルト: {end_dt.strftime('%Y-%m-%d')}）: ") or end_dt.strftime("%Y-%m-%d")
                    try:
                        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                        # 終了日はその日の終わりまでにする
                        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
                    except ValueError:
                        print("無効な日付形式です。デフォルト期間を使用します。")
                        # デフォルトに戻す
                        end_dt = datetime.now()
                        start_dt = end_dt - timedelta(days=7)

                # 注文取得 (client.get_orders は client.search_orders を呼び、その中で verbose が制御される)
                orders = client.get_orders(
                    account_id=account_id,
                    start_timestamp=start_dt,
                    end_timestamp=end_dt,
                    verbose=True # API呼び出し時の詳細ログは表示する
                )
                
                if orders:
                    print(f"\n===== 注文検索結果 ({len(orders)}件) =====")
                    # ここで client.display_orders(orders) のような表示関数を呼び出すか、
                    # 簡単なループで表示する
                    for i, order_item in enumerate(orders[:10]): # 最初の10件を表示
                        print(f"  注文 {i+1}: ID={order_item.get('id')}, Contract={order_item.get('contractId')}, "
                              f"Status={order_item.get('status')}, Type={order_item.get('type')}, "
                              f"Side={order_item.get('side')}, Size={order_item.get('size')}, "
                              f"Created={order_item.get('creationTimestamp')}")
                    if len(orders) > 10:
                        print(f"  ... 他 {len(orders)-10} 件の注文があります。")
                        
                    save_choice = input("\n結果をJSONファイルに保存しますか？ (y/n、デフォルト: n): ").lower()
                    if save_choice == 'y':
                        filename = input("ファイル名を入力 (デフォルト: orders_result.json): ") or "orders_result.json"
                        # search_orders を使って完全なレスポンスを取得して保存する
                        # この時、API呼び出しの詳細ログは不要なので verbose=False にする
                        full_response = client.search_orders(account_id, start_dt, end_dt, verbose=False)
                        if full_response:
                             client.save_result_to_json(full_response, filename)
                        else:
                            # get_orders で成功していても、search_orders で再度APIを叩くので、
                            # ネットワークエラー等で失敗する可能性も考慮
                            print("ファイル保存用のデータ取得に失敗しました。")
                else:
                    # get_orders が空リストを返した場合 (API呼び出し自体は成功したがデータが0件、またはAPIエラー)
                    # client.get_orders の verbose=True により、APIエラーの場合はメッセージが出力されているはず
                    print("指定された条件で注文は見つかりませんでした、または取得中にエラーが発生しました。")
                    
            except Exception as e:
                print(f"注文検索処理全体で予期せぬエラーが発生しました: {str(e)}")
                import traceback
                traceback.print_exc() # デバッグ情報としてスタックトレースを表示

        elif choice == "6": # トレード検索
            print("\n---- トレード履歴検索を開始します ----")
            try:
                # アカウント選択
                print("まず、トレード履歴を検索するアカウントを選択してください。")
                selected_account_info = client.select_account(only_active=True, verbose_selection=True)

                if not selected_account_info:
                    continue 

                account_id = selected_account_info.get("id")
                if account_id is None:
                    print("エラー: 選択されたアカウントからIDを取得できませんでした。トレード検索を中止します。")
                    continue
                
                print(f"アカウントID {account_id} のトレード履歴を検索します。")
                
                # デフォルトの時間範囲を設定（過去7日間）
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=7)
                
                custom_range = input(f"カスタム期間を指定しますか？(y/n、デフォルト: n、期間: {start_dt.date()} から {end_dt.date()}): ").lower()
                if custom_range == 'y':
                    start_date_str = input(f"開始日（YYYY-MM-DD、デフォルト: {start_dt.strftime('%Y-%m-%d')}）: ") or start_dt.strftime("%Y-%m-%d")
                    end_date_str = input(f"終了日（YYYY-MM-DD、デフォルト: {end_dt.strftime('%Y-%m-%d')}）: ") or end_dt.strftime("%Y-%m-%d")
                    try:
                        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                        # 終了日はその日の終わりまでにする
                        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
                    except ValueError:
                        print("無効な日付形式です。デフォルト期間を使用します。")
                        # デフォルトに戻す
                        end_dt = datetime.now()
                        start_dt = end_dt - timedelta(days=7)

                # トレード履歴取得
                trades = client.get_trades(
                    account_id=account_id,
                    start_timestamp=start_dt,
                    end_timestamp=end_dt,
                    verbose=True
                )
                
                if trades:
                    print(f"\n===== トレード履歴検索結果 ({len(trades)}件) =====")
                    # トレード履歴表示
                    client.display_trades(trades)
                        
                    save_choice = input("\n結果をJSONファイルに保存しますか？ (y/n、デフォルト: n): ").lower()
                    if save_choice == 'y':
                        filename = input("ファイル名を入力 (デフォルト: trades_result.json): ") or "trades_result.json"
                        # 完全なレスポンスを取得して保存
                        full_response = client.search_trades(account_id, start_dt, end_dt, verbose=False)
                        if full_response:
                            client.save_result_to_json(full_response, filename)
                        else:
                            print("ファイル保存用のデータ取得に失敗しました。")
                else:
                    print("指定された条件でトレード履歴は見つかりませんでした、または取得中にエラーが発生しました。")
                        
            except Exception as e:
                print(f"トレード履歴検索処理全体で予期せぬエラーが発生しました: {str(e)}")
                import traceback
                traceback.print_exc()

        elif choice == "7":
            print("\n---- 注文発注を開始します ----")
            try:
                # アカウント選択
                print("まず、注文を発注するアカウントを選択してください。")
                selected_account = client.select_account(only_active=True)
                
                if not selected_account:
                    print("アカウントが選択されませんでした。処理を中止します。")
                    continue
                
                account_id = selected_account.get("id")
                
                # 契約検索
                contract_search = input("契約を検索するテキストを入力（例: ES, NQ, RTY）: ")
                selected_contract = client.select_contract(contract_search)
                
                if not selected_contract:
                    print("契約が選択されませんでした。処理を中止します。")
                    continue
                
                contract_id = selected_contract.get("id")
                
                # 注文方向の選択
                print("\n注文方向を選択してください:")
                print("1. 買い (Bid/Buy)")
                print("2. 売り (Ask/Sell)")
                side_choice = input("選択 (1-2): ")
                
                side = client.ORDER_SIDE_BUY if side_choice == "1" else client.ORDER_SIDE_SELL
                
                # 注文タイプの選択
                print("\n注文タイプを選択してください:")
                print("1. 成行 (Market)")
                print("2. 指値 (Limit)")
                print("3. 逆指値 (Stop)")
                order_type_choice = input("選択 (1-3): ")
                
                if order_type_choice == "1":
                    order_type = client.ORDER_TYPE_MARKET
                elif order_type_choice == "2":
                    order_type = client.ORDER_TYPE_LIMIT
                else:
                    order_type = client.ORDER_TYPE_STOP
                
                # 数量の入力
                size_str = input("\n注文数量を入力: ")
                size = int(size_str)
                
                # 価格の入力（必要な場合）
                limit_price = None
                stop_price = None
                
                if order_type == client.ORDER_TYPE_LIMIT:
                    limit_price_str = input("指値価格を入力: ")
                    limit_price = float(limit_price_str)
                elif order_type == client.ORDER_TYPE_STOP:
                    stop_price_str = input("逆指値価格を入力: ")
                    stop_price = float(stop_price_str)
                
                # カスタムタグ（オプション）
                custom_tag = input("\nカスタムタグを入力 (省略可): ") or None
                
                # 注文確認
                print("\n==== 注文内容の確認 ====")
                print(f"アカウント: ID={account_id}, 名前={selected_account.get('name')}")
                print(f"契約: ID={contract_id}, 名前={selected_contract.get('name')}, 説明={selected_contract.get('description')}")
                print(f"方向: {'買い(Buy)' if side == client.ORDER_SIDE_BUY else '売り(Sell)'}")
                
                if order_type == client.ORDER_TYPE_MARKET:
                    print("タイプ: 成行(Market)")
                elif order_type == client.ORDER_TYPE_LIMIT:
                    print(f"タイプ: 指値(Limit), 価格: {limit_price}")
                elif order_type == client.ORDER_TYPE_STOP:
                    print(f"タイプ: 逆指値(Stop), 価格: {stop_price}")
                
                print(f"数量: {size}")
                
                if custom_tag:
                    print(f"カスタムタグ: {custom_tag}")
                
                confirm = input("\nこの内容で注文を発注しますか？(y/n): ").lower()
                
                if confirm == 'y':
                    # 注文発注
                    result = client.place_order(
                        account_id=account_id,
                        contract_id=contract_id,
                        order_type=order_type,
                        side=side,
                        size=size,
                        limit_price=limit_price,
                        stop_price=stop_price,
                        custom_tag=custom_tag
                    )
                    
                    if result and result.get("success"):
                        print(f"\n注文が正常に発注されました！注文ID: {result.get('orderId')}")
                    else:
                        print("\n注文の発注に失敗しました。")
                else:
                    print("\n注文発注がキャンセルされました。")
            
            except Exception as e:
                print(f"注文発注中にエラーが発生しました: {str(e)}")

        elif choice == "8":
            print("\n---- オープンオーダー検索を開始します ----")
            try:
                # アカウント選択
                print("まず、オープンオーダーを検索するアカウントを選択してください。")
                selected_account = client.select_account(only_active=True)
                
                if not selected_account:
                    print("アカウントが選択されませんでした。処理を中止します。")
                    continue
                
                account_id = selected_account.get("id")
                
                # オープンオーダー取得
                print(f"\nアカウントID {account_id} のオープンオーダーを検索します...")
                open_orders = client.get_open_orders(account_id=account_id)
                
                if open_orders:
                    print("\n===== オープンオーダー検索結果 =====")
                    client.display_orders(open_orders)
                else:
                    print(f"アカウントID {account_id} にオープンオーダーはありません。")
                    
            except Exception as e:
                print(f"オープンオーダー検索処理中にエラーが発生しました: {str(e)}")
                import traceback
                traceback.print_exc()

        elif choice == "9":
            print("\n---- 注文キャンセル処理を開始します ----")
            try:
                # アカウント選択
                print("まず、注文をキャンセルするアカウントを選択してください。")
                selected_account = client.select_account(only_active=True)
                
                if not selected_account:
                    print("アカウントが選択されませんでした。処理を中止します。")
                    continue
                
                account_id = selected_account.get("id")
                
                # オープンオーダー取得
                print(f"\nアカウントID {account_id} のオープンオーダーを検索します...")
                open_orders = client.get_open_orders(account_id=account_id)
                
                if not open_orders:
                    print(f"アカウントID {account_id} にオープンオーダーはありません。")
                    continue
                
                print("\n===== キャンセル可能なオープンオーダー =====")
                client.display_orders(open_orders)
                
                # キャンセルする注文の選択
                while True:
                    try:
                        order_idx_str = input("\nキャンセルする注文の番号を選択してください (1から始まる番号), または 'q' で中止: ")
                        
                        if order_idx_str.lower() == 'q':
                            print("キャンセル処理を中止しました。")
                            break
                        
                        order_idx = int(order_idx_str) - 1  # 表示は1から始まるが、インデックスは0から始まる
                        
                        if 0 <= order_idx < len(open_orders):
                            target_order = open_orders[order_idx]
                            order_id = target_order.get("id")
                            
                            # 注文情報を表示
                            print(f"\n以下の注文をキャンセルします:")
                            print(f"  注文ID: {order_id}")
                            print(f"  契約ID: {target_order.get('contractId')}")
                            print(f"  種類: {client.get_order_type_name(target_order.get('type'))}")
                            print(f"  方向: {client.get_order_side_name(target_order.get('side'))}")
                            print(f"  サイズ: {target_order.get('size')}")
                            
                            # 確認
                            confirm = input("この注文をキャンセルしますか？(y/n): ").lower()
                            if confirm == 'y':
                                result = client.cancel_order(account_id, order_id)
                            else:
                                print("キャンセルを中止しました。")
                            
                            break
                        else:
                            print(f"無効な選択です。1から{len(open_orders)}までの数字を入力してください。")
                    
                    except ValueError:
                        print("数字を入力するか、'q'で中止してください。")
                    except Exception as e:
                        print(f"注文選択中にエラーが発生しました: {str(e)}")
                        break
                
            except Exception as e:
                print(f"注文キャンセル処理中にエラーが発生しました: {str(e)}")
                import traceback
                traceback.print_exc()

        elif choice == "10":
            print("\n---- 注文修正処理を開始します ----")
            try:
                # アカウント選択
                print("まず、注文を修正するアカウントを選択してください。")
                selected_account = client.select_account(only_active=True)
                
                if not selected_account:
                    print("アカウントが選択されませんでした。処理を中止します。")
                    continue
                
                account_id = selected_account.get("id")
                
                # オープンオーダー取得
                print(f"\nアカウントID {account_id} のオープンオーダーを検索します...")
                open_orders = client.get_open_orders(account_id=account_id)
                
                if not open_orders:
                    print(f"アカウントID {account_id} にオープンオーダーはありません。")
                    continue
                
                print("\n===== 修正可能なオープンオーダー =====")
                client.display_orders(open_orders)
                
                # 修正する注文の選択
                while True:
                    try:
                        order_idx_str = input("\n修正する注文の番号を選択してください (1から始まる番号), または 'q' で中止: ")
                        
                        if order_idx_str.lower() == 'q':
                            print("修正処理を中止しました。")
                            break
                        
                        order_idx = int(order_idx_str) - 1  # 表示は1から始まるが、インデックスは0から始まる
                        
                        if 0 <= order_idx < len(open_orders):
                            # 選択された注文の修正処理
                            result = client.modify_open_order_by_index(account_id, order_idx)
                            
                            if result and result.get("success"):
                                # 修正後の最新のオープンオーダーを表示
                                updated_orders = client.get_open_orders(account_id, verbose=False)
                                print("\n===== 修正後のオープンオーダー =====")
                                client.display_orders(updated_orders)
                            
                            break
                        else:
                            print(f"無効な選択です。1から{len(open_orders)}までの数字を入力してください。")
                    
                    except ValueError:
                        print("数字を入力するか、'q'で中止してください。")
                    except Exception as e:
                        print(f"注文選択中にエラーが発生しました: {str(e)}")
                        break
                
            except Exception as e:
                print(f"注文修正処理中にエラーが発生しました: {str(e)}")
                import traceback
                traceback.print_exc()
        
        else:
            print("無効な選択です。0-7の数字を入力してください。")


# このファイルが直接実行された場合のみmain()を実行
if __name__ == "__main__":
    main()