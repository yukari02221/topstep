# TopstepX API Client

TopstepX APIと連携して、アカウント情報の取得、契約検索、価格データ取得などの機能を提供するPythonクライアントライブラリです。

## 機能

- アカウント情報の取得
- 契約（銘柄）の検索
- 履歴価格データ（OHLC）の取得
- 注文情報の検索 
- JWT認証トークンの管理（保存/読み込み）
- 対話型インターフェースの提供
- PandasのDataFrameへの変換サポート
- 本番環境とデモ環境の切り替え

## インストール

依存パッケージをインストールします：

```bash
pip install requests python-dotenv
```

オプションの機能を使用する場合：

```bash
pip install pandas matplotlib
```

## 基本的な使用方法

### クライアントの初期化と認証

```python
from topstep_API import TopstepXClient

# クライアントの初期化（環境変数から認証情報を取得）
client = TopstepXClient()

# または、認証情報を直接指定
# client = TopstepXClient(username="your_username", api_key="your_api_key")

# デモ環境を使用する場合
# client = TopstepXClient(use_demo=True)

# 認証
if client.authenticate():
    print("認証に成功しました！")
else:
    print("認証に失敗しました")
```

### アカウント情報の取得

```python
# アクティブなアカウントのみを取得
accounts = client.get_accounts(only_active=True)

# 結果の表示
client.display_accounts(accounts)
```

### 契約（銘柄）の検索

```python
# E-mini Russell 2000に関連する契約を検索
contracts = client.get_contracts("RTY")

for contract in contracts:
    print(f"ID: {contract['id']}, 名前: {contract['name']}, 説明: {contract['description']}")
```

### 履歴価格データの取得

```python
from datetime import datetime, timedelta

# 期間の設定（過去30日間）
end_time = datetime.now()
start_time = end_time - timedelta(days=30)

# 履歴データ（日足）の取得
bars = client.get_bars(
    contract_id="CON.F.US.RTY.Z24",  # 契約ID
    start_time=start_time,
    end_time=end_time,
    unit=client.UNIT_DAY,  # 日足
    unit_number=1,
    limit=100
)

# 結果の表示
client.display_bars(bars)

# PandasのDataFrameに変換
df = client.to_pandas(bars)
if df is not None:
    print(df.head())
```

### 注文情報の検索

```python
from datetime import datetime, timedelta

# (クライアント初期化と認証後)

# 注文を検索したいアカウントID (実際のIDに置き換えてください)
# アカウントIDは client.get_accounts() や対話型の client.select_account() で確認・選択できます。
account_id_to_search = 202 # 例: 実際の有効なアカウントIDを使用してください

# 検索期間の設定 (例: 過去7日間)
end_time_orders = datetime.now()
start_time_orders = end_time_orders - timedelta(days=7)

# 注文リストを取得
orders = client.get_orders(
    account_id=account_id_to_search,
    start_timestamp=start_time_orders,
    end_timestamp=end_time_orders # end_timestampは省略可能
)

if orders:
    print(f"\nアカウントID {account_id_to_search} の注文 ({len(orders)}件):")
    for order in orders[:5]: # 最初の5件を表示
        print(f"  ID: {order.get('id')}, Contract: {order.get('contractId')}, "
              f"Status: {order.get('status')}, Type: {order.get('type')}, Side: {order.get('side')}, "
              f"Size: {order.get('size')}, Created: {order.get('creationTimestamp')}")
else:
    print("指定された条件で注文は見つかりませんでした。")

```

### 対話型で契約を選択して履歴データを取得

```python
# 対話的に契約を選択して履歴データを取得
selected_contract, bars = client.search_and_get_bars(
    search_text="ES",  # E-mini S&P 500を検索
    start_time=start_time,
    end_time=end_time,
    unit=client.UNIT_HOUR,  # 時間足
    unit_number=1,
    limit=100
)

if selected_contract and bars:
    print(f"{selected_contract['description']}の履歴データを取得しました")
    client.display_bars(bars)
```

### トークンの保存と読み込み

```python
# 認証トークンをファイルに保存
client.save_token("my_token.txt")

# 別のセッションでトークンを読み込む
new_client = TopstepXClient()
if new_client.load_token("my_token.txt"):
    # 既存のトークンで認証する（トークンが有効な限り）
    bars = new_client.get_bars(...)
```

## コマンドラインインターフェース

このライブラリは対話型のコマンドラインインターフェースも提供しています：

```bash
python topstepx_client.py
```

これにより、認証から始まり、アカウント検索、契約検索、履歴データ取得などの機能を対話的に使用できます。

## 使用例

より詳細な使用例については、`example`を参照してください：


## 時間単位の定義

履歴データを取得する際の時間単位は以下の定数で指定できます：

| 定数 | 値 | 説明 |
|-----|-----|-----|
| UNIT_SECOND | 1 | 秒足 |
| UNIT_MINUTE | 2 | 分足 |
| UNIT_HOUR | 3 | 時間足 |
| UNIT_DAY | 4 | 日足 |
| UNIT_WEEK | 5 | 週足 |
| UNIT_MONTH | 6 | 月足 |

## 環境変数

認証情報は環境変数から設定することもできます：

```
TOPSTEPX_USERNAME=your_username
TOPSTEPX_API_KEY=your_api_key
```

`.env`ファイルを使用する場合は、`python-dotenv`パッケージをインストールしてください。

## エラーハンドリング

各メソッドはエラー時に適切な値（`None`や空のリストなど）を返します。詳細なエラーメッセージを表示するには、`verbose=True`パラメータを使用してください：

```python
# 詳細なエラーメッセージを表示
accounts = client.get_accounts(verbose=True)
```

## 注意事項

- TopstepX APIのトークンの有効期限は24時間です
- 認証済みのトークンがない場合、各メソッドは自動的に認証を試みます
- デモ環境と本番環境では契約IDやデータが異なる場合があります
