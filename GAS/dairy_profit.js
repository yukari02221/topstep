/**
 * Google Spreadsheetで日次収益を集計するスクリプト
 */

// 日次収益を計算する関数
function calculateDailyProfits() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  // シート名を「取引履歴」に変更
  const dataSheet = ss.getSheetByName('取引履歴');
  
  // 取引履歴シートが存在しない場合は処理を終了
  if (!dataSheet) {
    // トリガーから実行された場合はログに記録
    if (ScriptApp.getAuthMode() === ScriptApp.AuthMode.FULL) {
      console.log('取引履歴シートが見つかりません。処理を終了します。');
      return null;
    }
    
    // 手動実行の場合はアラートを表示
    const ui = SpreadsheetApp.getUi();
    const response = ui.alert(
      '取引履歴シートが見つかりません',
      '取引履歴シートが存在しないため、処理を実行できません。シート名が「取引履歴」であることを確認してください。',
      ui.ButtonSet.OK
    );
    return null;
  }
  
  // 日次収益シートが存在しない場合は作成
  let dailyProfitSheet = ss.getSheetByName('日次収益');
  if (!dailyProfitSheet) {
    dailyProfitSheet = ss.insertSheet('日次収益');
    // ヘッダーを設定
    dailyProfitSheet.getRange('A1:E1').setValues([['日付', '取引数', '総損益', '手数料合計', '純利益']]);
    dailyProfitSheet.getRange('A1:E1').setFontWeight('bold');
  } else {
    // 既存のデータをクリア（ヘッダーは残す）
    if (dailyProfitSheet.getLastRow() > 1) {
      dailyProfitSheet.getRange(2, 1, dailyProfitSheet.getLastRow() - 1, 5).clear();
    }
  }
  
  // データ範囲を取得
  const dataRange = dataSheet.getDataRange();
  const values = dataRange.getValues();
  
  // データが空でないか確認
  if (values.length <= 1) {
    const ui = SpreadsheetApp.getUi();
    ui.alert(
      'データがありません',
      '「取引データ」シートにデータが入力されていません。データを入力してから再度実行してください。',
      ui.ButtonSet.OK
    );
    return null;
  }
  
  // 日付列と損益列のインデックスを特定（ヘッダー行から）
  const headers = values[0];
  const dateColIndex = headers.indexOf('取引日時');
  const profitLossColIndex = headers.indexOf('損益');
  const feeColIndex = headers.indexOf('手数料');
  
  // 必要な列が見つからない場合
  if (dateColIndex === -1 || profitLossColIndex === -1) {
    const ui = SpreadsheetApp.getUi();
    ui.alert(
      '必要な列が見つかりません',
      '「取引日時」または「損益」列が見つかりません。ヘッダー行が正しく設定されているか確認してください。',
      ui.ButtonSet.OK
    );
    return null;
  }
  
  // 日付ごとに集計するためのオブジェクト
  const dailyData = {};
  
  // ヘッダー行をスキップしてデータを処理
  for (let i = 1; i < values.length; i++) {
    const row = values[i];
    
    // 日付部分のみ抽出（時間を除去）
    let dateTime;
    try {
      // 日付が文字列の場合は変換を試みる
      if (typeof row[dateColIndex] === 'string') {
        // 日本語形式の日付文字列「2025-05-09 00:31:28」を処理
        const dateParts = row[dateColIndex].split(' ');
        if (dateParts.length === 2) {
          const [datePart, timePart] = dateParts;
          const [year, month, day] = datePart.split('-').map(Number);
          const [hour, minute, second] = timePart.split(':').map(Number);
          dateTime = new Date(year, month - 1, day, hour, minute, second);
        } else {
          dateTime = new Date(row[dateColIndex]);
        }
      } else {
        // すでにDateオブジェクトの場合はそのまま使用
        dateTime = row[dateColIndex];
      }
      
      // 日付が無効な場合はスキップ
      if (isNaN(dateTime.getTime())) {
        console.log('無効な日付をスキップしました: ' + row[dateColIndex]);
        continue;
      }
    } catch (e) {
      console.log('日付の変換に失敗しました: ' + row[dateColIndex]);
      continue;
    }
    
    const dateStr = Utilities.formatDate(dateTime, Session.getScriptTimeZone(), 'yyyy-MM-dd');
    
    // 損益と手数料を数値として取得
    const profitLoss = parseFloat(row[profitLossColIndex]) || 0;
    const fee = parseFloat(row[feeColIndex]) || 0;
    
    // 日付ごとのデータを集計
    if (!dailyData[dateStr]) {
      dailyData[dateStr] = {
        count: 0,
        totalProfitLoss: 0,
        totalFees: 0
      };
    }
    
    dailyData[dateStr].count++;
    dailyData[dateStr].totalProfitLoss += profitLoss;
    dailyData[dateStr].totalFees += fee;
  }
  
  // 集計データを日付順にソート
  const sortedDates = Object.keys(dailyData).sort();
  
  // 結果を日次収益シートに書き込む
  const resultData = [];
  for (const dateStr of sortedDates) {
    const data = dailyData[dateStr];
    const netProfit = data.totalProfitLoss - data.totalFees;
    resultData.push([
      dateStr,
      data.count,
      data.totalProfitLoss,
      data.totalFees,
      netProfit
    ]);
  }
  
  // データがある場合は書き込む
  if (resultData.length > 0) {
    dailyProfitSheet.getRange(2, 1, resultData.length, 5).setValues(resultData);
  }
  
  // シートの書式を整える
  dailyProfitSheet.autoResizeColumns(1, 5);
  
  // 損益列に通貨書式を適用
  if (resultData.length > 0) {
    dailyProfitSheet.getRange(2, 3, resultData.length, 3).setNumberFormat('#,##0.00');
  }
  
  // グラフを作成
  createProfitChart(dailyProfitSheet, resultData.length);
  
  return dailyProfitSheet;
}

// 日次収益グラフを作成する関数
function createProfitChart(sheet, dataRowCount) {
  // 既存のグラフを削除
  const charts = sheet.getCharts();
  for (let i = 0; i < charts.length; i++) {
    sheet.removeChart(charts[i]);
  }
  
  // データがない場合は処理しない
  if (dataRowCount <= 0) return;
  
  // グラフを作成
  const chartBuilder = sheet.newChart()
    .setChartType(Charts.ChartType.COMBO)
    .addRange(sheet.getRange(1, 1, dataRowCount + 1, 1)) // 日付
    .addRange(sheet.getRange(1, 5, dataRowCount + 1, 1)) // 純利益
    .setPosition(dataRowCount + 5, 1, 0, 0)
    .setOption('title', '日次収益推移')
    .setOption('series', {
      0: {type: 'bars'}
    })
    .setOption('hAxis', {title: '日付'})
    .setOption('vAxis', {title: '純利益'})
    .setOption('legend', {position: 'top'});
  
  sheet.insertChart(chartBuilder.build());
}

// メニューに追加する関数
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('日次収益管理')
    .addItem('日次収益を計算', 'calculateDailyProfits')
    .addSeparator()
    .addItem('毎日9時に自動実行を設定', 'createDailyTrigger')
    .addItem('自動実行を停止', 'removeDailyTrigger')
    .addToUi();
}

// 新しいスプレッドシートを作成する手順
function setupNewTrackingSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  
  // 取引データシートが存在しない場合は作成
  let dataSheet = ss.getSheetByName('取引データ');
  if (!dataSheet) {
    dataSheet = ss.insertSheet('取引データ');
    
    // ヘッダー行の設定
    const headers = [
      'ID', 'アカウントID', '契約ID', '取引日時', '価格', '損益', '手数料', 
      '売買区分', 'サイズ', '無効', '注文ID'
    ];
    dataSheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    dataSheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
  }
  
  // サンプルデータの挿入（実際のデータに置き換え）
  // ここにサンプルデータを入力するコードを追加
  
  // 説明シートの作成
  let instructionSheet = ss.getSheetByName('使用方法');
  if (!instructionSheet) {
    instructionSheet = ss.insertSheet('使用方法');
    
    instructionSheet.getRange('A1').setValue('日次収益管理システムの使用方法');
    instructionSheet.getRange('A1').setFontWeight('bold').setFontSize(14);
    
    const instructions = [
      ['', ''],
      ['手順1:', '「取引データ」シートに取引データを入力または貼り付けてください。'],
      ['手順2:', 'メニューから「日次収益管理」→「日次収益を計算」を選択してください。'],
      ['手順3:', '「日次収益」シートに日付ごとの集計結果とグラフが生成されます。'],
      ['', ''],
      ['注意点:', '• 取引データには「取引日時」と「損益」列が必須です。'],
      ['', '• 日付形式は「YYYY-MM-DD HH:MM:SS」の形式である必要があります。'],
      ['', '• 定期的にデータをバックアップすることをお勧めします。']
    ];
    
    instructionSheet.getRange(3, 1, instructions.length, 2).setValues(instructions);
    instructionSheet.autoResizeColumns(1, 2);
  }
  
  // アクティブシートを説明シートに設定
  instructionSheet.activate();
  
  return ss;
}

// 初期設定を実行する関数
function initializeTracker() {
  setupNewTrackingSheet();
  onOpen(); // メニューを追加
}

// 毎日自動実行するためのトリガーを設定する関数
function createDailyTrigger() {
  // 既存のトリガーを削除
  deleteExistingTriggers();
  
  // 毎日9時に実行するトリガーを作成
  ScriptApp.newTrigger('calculateDailyProfits')
    .timeBased()
    .atHour(9)
    .everyDays(1)
    .create();
  
  // UI経由で実行された場合は完了メッセージを表示
  if (ScriptApp.getAuthMode() !== ScriptApp.AuthMode.FULL) {
    const ui = SpreadsheetApp.getUi();
    ui.alert(
      'トリガー設定完了',
      '毎日9時に自動で日次収益計算が実行されるようにトリガーを設定しました。',
      ui.ButtonSet.OK
    );
  }
}

// 既存のトリガーを削除する補助関数
function deleteExistingTriggers() {
  // プロジェクトに関連付けられた全てのトリガーを取得
  const triggers = ScriptApp.getProjectTriggers();
  
  // calculateDailyProfits関数のトリガーを削除
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === 'calculateDailyProfits') {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
}

// トリガーを削除する関数（必要な場合に手動で実行）
function removeDailyTrigger() {
  deleteExistingTriggers();
  
  // UI経由で実行された場合は完了メッセージを表示
  if (ScriptApp.getAuthMode() !== ScriptApp.AuthMode.FULL) {
    const ui = SpreadsheetApp.getUi();
    ui.alert(
      'トリガー削除完了',
      '日次収益計算の自動実行トリガーを削除しました。',
      ui.ButtonSet.OK
    );
  }
}