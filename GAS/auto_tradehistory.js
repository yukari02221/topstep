/**
 * TopStepX API 取引履歴自動取得スクリプト
 * 毎日前日のトレード履歴を自動的に取得して蓄積します
 */

// 基本設定
const CONFIG = {
  BASE_URL: 'https://api.topstepx.com/api',
  AUTH_ENDPOINT: '/Auth/loginKey',
  ACCOUNT_SEARCH_ENDPOINT: '/Account/search',
  TRADE_SEARCH_ENDPOINT: '/Trade/search',
  // APIアクセス情報
  USERNAME: 'YOUR_USERNAME',  // ⚠️ 実際のユーザー名に変更してください
  API_KEY: 'YOUR_API_KEY',    // ⚠️ 実際のAPIキーに変更してください
  // 設定値
  HISTORY_SHEET_NAME: '取引履歴', // ユーザー指定のシート名に合わせてください
  CONFIG_SHEET_NAME: '設定',
  LOG_SHEET_NAME: '実行ログ',
  EMAIL_NOTIFICATION: true,
  NOTIFICATION_EMAIL: 'your.email@example.com',  // ⚠️ 通知を受け取るメールアドレスに変更してください
  // 自動実行設定
  EXECUTION_HOUR: 8,  // 毎日の実行時間（24時間制）
  TIMEZONE: 'Asia/Tokyo'  // タイムゾーン
};

/**
 * Google Spreadsheetが開かれたときに実行される関数
 * 初期化と自動実行トリガーの確認を行います
 */
function onOpen() {
  // 設定シートがなければ作成
  createConfigSheetIfNotExists();
  
  // トリガーが設定されているか確認し、なければ設定
  checkAndSetupTrigger();
}

/**
 * スクリプトを初めて使用するときに実行する関数
 * 初期セットアップを行います
 */
function initialize() {
  // 設定シートの作成
  createConfigSheet();
  
  // 自動実行トリガーの設定
  setupDailyTrigger();
  
  // 初期化完了メッセージ
  const ui = SpreadsheetApp.getUi();
  ui.alert('セットアップ完了', 
           `トレード履歴自動取得システムのセットアップが完了しました。\n\n` +
           `毎日${CONFIG.EXECUTION_HOUR}時に前日のトレード履歴が自動取得されます。\n\n` +
           `APIユーザー名とAPIキーが正しく設定されていることを確認してください。`, 
           ui.ButtonSet.OK);
}

/**
 * 設定シートが存在しない場合に作成する関数
 */
function createConfigSheetIfNotExists() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let configSheet = ss.getSheetByName(CONFIG.CONFIG_SHEET_NAME);
  
  if (!configSheet) {
    createConfigSheet();
  }
}

/**
 * 設定シートを作成または更新する関数
 */
function createConfigSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let configSheet = ss.getSheetByName(CONFIG.CONFIG_SHEET_NAME);
  
  if (!configSheet) {
    configSheet = ss.insertSheet(CONFIG.CONFIG_SHEET_NAME);
  } else {
    configSheet.clear();
  }
  
  // ヘッダー
  configSheet.getRange('A1:B1').setValues([['設定項目', '値']]);
  configSheet.getRange('A1:B1').setFontWeight('bold');
  configSheet.getRange('A1:B1').setBackground('#f3f3f3');
  
  // 設定値
  const configValues = [
    ['APIユーザー名', CONFIG.USERNAME],
    ['APIキー', '********'], // セキュリティのため実際のキーは表示しない
    ['ユーザー名とAPIキーの更新が必要', CONFIG.USERNAME === 'YOUR_USERNAME' ? 'はい' : 'いいえ'],
    ['トレード履歴シート名', CONFIG.HISTORY_SHEET_NAME],
    ['自動実行時間', `毎日 ${CONFIG.EXECUTION_HOUR}:00 (${CONFIG.TIMEZONE})`],
    ['メール通知', CONFIG.EMAIL_NOTIFICATION ? 'オン' : 'オフ'],
    ['通知メールアドレス', CONFIG.NOTIFICATION_EMAIL],
    ['最終実行日時', '未実行'],
    ['自動実行ステータス', '有効']
  ];
  
  configSheet.getRange(2, 1, configValues.length, 2).setValues(configValues);
  
  // 書式設定
  configSheet.autoResizeColumns(1, 2);
  
  // セル保護の設定
  const protection = configSheet.protect();
  protection.setDescription('設定シートの保護');
  protection.setWarningOnly(true);
  
  // 注意メッセージ
  configSheet.getRange('A12:B12').merge();
  configSheet.getRange('A12').setValue('⚠️ ユーザー名とAPIキーはスクリプトエディタ内のCONFIG変数で直接変更してください。');
  configSheet.getRange('A12').setFontColor('red');
  
  // 自動実行の説明
  configSheet.getRange('A14:B14').merge();
  configSheet.getRange('A14').setValue('ℹ️ このシステムは毎日自動的に前日のトレード履歴を取得します。手動操作は必要ありません。');
  configSheet.getRange('A14').setFontStyle('italic');
}

/**
 * トリガーが設定されているか確認し、なければ設定する関数
 */
function checkAndSetupTrigger() {
  // 既存のトリガーを確認
  const triggers = ScriptApp.getProjectTriggers();
  let hasTradeHistoryTrigger = false;
  
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'dailyHistoryFetch') {
      hasTradeHistoryTrigger = true;
    }
  });
  
  // トリガーがなければ設定
  if (!hasTradeHistoryTrigger) {
    setupDailyTrigger();
  }
}

/**
 * 自動実行トリガーを設定する関数
 */
function setupDailyTrigger() {
  // 既存のトリガーを削除
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    if (trigger.getHandlerFunction() === 'dailyHistoryFetch') {
      ScriptApp.deleteTrigger(trigger);
    }
  });
  
  // 新しいトリガーを設定（指定時間に毎日実行）
  ScriptApp.newTrigger('dailyHistoryFetch')
    .timeBased()
    .atHour(CONFIG.EXECUTION_HOUR)
    .everyDays(1)
    .inTimezone(CONFIG.TIMEZONE)
    .create();
  
  // 設定シートの更新
  updateTriggerStatus('有効');
  
  // ログ記録
  logExecution({
    date: new Date(),
    function: 'setupDailyTrigger',
    targetDate: '-',
    status: '成功',
    message: `毎日${CONFIG.EXECUTION_HOUR}時に実行する自動トリガーを設定しました`,
    details: ''
  });
}

/**
 * 毎日の自動実行用関数
 * トリガーから呼び出される
 */
function dailyHistoryFetch() {
  try {
    // 前日の日付を計算
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const formattedDate = Utilities.formatDate(yesterday, CONFIG.TIMEZONE, 'yyyy-MM-dd');
    
    Logger.log(`${formattedDate}のトレード履歴自動取得を開始します...`);
    
    // トレード履歴の取得と保存
    const result = fetchAndSaveTradeHistory(formattedDate);
    
    // ログへの記録
    logExecution({
      date: new Date(),
      function: 'dailyHistoryFetch',
      targetDate: formattedDate,
      status: result.success ? '成功' : '失敗',
      message: result.message,
      details: result.details || ''
    });
    
    // 設定シートの更新
    updateConfigLastRun();
    
    // メール通知（設定されている場合）
    if (CONFIG.EMAIL_NOTIFICATION && CONFIG.NOTIFICATION_EMAIL) {
      sendNotificationEmail(result, formattedDate);
    }
    
    Logger.log(`${formattedDate}のトレード履歴自動取得が完了しました。結果: ${result.success ? '成功' : '失敗'}`);
    
    return result;
  } catch (error) {
    const errorMsg = `自動実行中にエラーが発生しました: ${error.message}`;
    Logger.log(errorMsg);
    Logger.log(error.stack);
    
    logExecution({
      date: new Date(),
      function: 'dailyHistoryFetch',
      targetDate: '不明',
      status: '失敗',
      message: errorMsg,
      details: error.stack || ''
    });
    
    if (CONFIG.EMAIL_NOTIFICATION && CONFIG.NOTIFICATION_EMAIL) {
      sendErrorEmail(errorMsg);
    }
    
    return {
      success: false,
      message: errorMsg
    };
  }
}

/**
 * トレード履歴を取得して保存する関数
 * @param {string} targetDate - 対象日（YYYY-MM-DD形式）
 * @return {Object} 処理結果
 */
function fetchAndSaveTradeHistory(targetDate) {
  try {
    Logger.log(`${targetDate}の取引履歴取得を開始します...`);
    
    // 取引履歴の取得
    const tradeHistoryResult = getTradeHistory(targetDate);
    
    if (!tradeHistoryResult.success) {
      const errorMsg = `取引履歴の取得に失敗しました: ${tradeHistoryResult.message}`;
      Logger.log(errorMsg);
      return {
        success: false,
        message: errorMsg
      };
    }
    
    Logger.log(`取引履歴の取得に成功しました。スプレッドシートに保存します...`);
    
    // スプレッドシートへの保存
    const sheetResult = saveTradeHistoryToSheet(targetDate, tradeHistoryResult);
    
    return sheetResult;
  } catch (error) {
    const errorMsg = `実行中にエラーが発生しました: ${error.message}`;
    Logger.log(errorMsg);
    Logger.log(error.stack);
    return {
      success: false,
      message: errorMsg,
      details: error.stack
    };
  }
}

/**
 * 取引履歴をシートに保存する関数
 * @param {string} targetDate - 対象日（YYYY-MM-DD形式）
 * @param {Object} result - 取引履歴データ
 * @return {Object} 処理結果
 */
function saveTradeHistoryToSheet(targetDate, result) {
  if (!result.success) {
    return {
      success: false,
      message: '取引履歴の取得に失敗しました: ' + result.message
    };
  }
  
  try {
    // アクティブなスプレッドシート
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(CONFIG.HISTORY_SHEET_NAME);
    
    const newHeader = ['ID', 'アカウントID', '契約ID', '取引日時', '価格', '損益', '手数料', '売買区分', 'サイズ', '無効', '注文ID']; // 11列
    const numColumns = newHeader.length;

    if (!sheet) {
      // シートが存在しない場合は作成
      sheet = ss.insertSheet(CONFIG.HISTORY_SHEET_NAME);
      // ヘッダー行
      sheet.appendRow(newHeader);
      
      // ヘッダー行の書式設定
      sheet.getRange(1, 1, 1, numColumns).setFontWeight('bold');
      sheet.getRange(1, 1, 1, numColumns).setBackground('#f3f3f3');
    } else {
        // 既存シートのヘッダーが新しいものと一致するか確認、異なれば上書き
        const currentHeader = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
        if (JSON.stringify(currentHeader.slice(0, numColumns)) !== JSON.stringify(newHeader)) {
            sheet.clearContents(); // ヘッダーが異なる場合は全クリアして再作成
            sheet.appendRow(newHeader);
            sheet.getRange(1, 1, 1, numColumns).setFontWeight('bold');
            sheet.getRange(1, 1, 1, numColumns).setBackground('#f3f3f3');
            Logger.log('ヘッダーが不一致のため、クリアして再作成しました。');
        }
    }
    
    // 既存データの確認（対象日の取引が既に存在するか）
    // 新しい形式では「取引日時」列（D列、インデックス3）で日付を比較
    const tradeDateColumnIndex = 4; // D列 (1-indexed)
    const existingDataValues = sheet.getLastRow() > 1 ? sheet.getRange(2, tradeDateColumnIndex, sheet.getLastRow() - 1, 1).getValues() : [];
    const allSheetData = sheet.getLastRow() > 1 ? sheet.getRange(2, 1, sheet.getLastRow() -1, sheet.getLastColumn()).getValues() : [];
    const rowsToDelete = [];
    
    for (let i = 0; i < existingDataValues.length; i++) {
      const cellValue = existingDataValues[i][0];
      if (cellValue) {
        let tradeDateStr = '';
        if (cellValue instanceof Date) {
          tradeDateStr = Utilities.formatDate(cellValue, CONFIG.TIMEZONE, 'yyyy-MM-dd');
        } else if (typeof cellValue === 'string' && cellValue.length >= 10) {
            // 文字列の場合、ISO形式などを想定して日付部分を抽出
            try {
                tradeDateStr = Utilities.formatDate(new Date(cellValue.substring(0,19).replace('T', ' ')), CONFIG.TIMEZONE, 'yyyy-MM-dd');
            } catch(e) {
                // 日付として解釈できない場合はスキップ
                Logger.log(`行 ${i+2} の日付値を解釈できませんでした: ${cellValue}`);
                continue;
            }
        } else {
            // それ以外の型や短い文字列はスキップ
            Logger.log(`行 ${i+2} の日付値の型が不正です: ${cellValue}`);
            continue;
        }

        if (tradeDateStr === targetDate) {
          rowsToDelete.push(i + 2); // +2 はヘッダー行と0-indexed配列のため
        }
      }
    }
    
    // 既存データを削除（重複を避けるため）
    if (rowsToDelete.length > 0) {
      Logger.log(`${targetDate}の既存データを削除します（${rowsToDelete.length}行）...`);
      // 行の削除は後ろから行う
      for (let i = rowsToDelete.length - 1; i >= 0; i--) {
        sheet.deleteRow(rowsToDelete[i]);
      }
    }
    
    // データ行
    let rowCount = 0;
    let totalProfit = 0;
    
    const newRows = [];
    
    result.results.forEach(accountResult => {
      accountResult.trades.forEach(trade => {
        newRows.push([
          trade.id,                   // ID
          accountResult.accountId,    // アカウントID
          trade.contractId,           // 契約ID
          trade.creationTimestamp,    // 取引日時
          trade.price,                // 価格
          trade.profitAndLoss,        // 損益
          trade.fees,                 // 手数料
          trade.side === 0 ? '買い' : '売り', // 売買区分
          trade.size,                 // サイズ
          trade.voided ? 'はい' : 'いいえ', // 無効
          trade.orderId               // 注文ID
        ]);
        
        rowCount++;
        if (trade.profitAndLoss) {
          totalProfit += trade.profitAndLoss;
        }
      });
    });
    
    // データがある場合のみ追加
    if (newRows.length > 0) {
      Logger.log(`${rowCount}件の新しいトレードデータを追加します...`);
      // 最終行を取得して新しい行を追加
      const lastRow = sheet.getLastRow();
      sheet.getRange(lastRow + 1, 1, newRows.length, numColumns).setValues(newRows);
    } else {
      Logger.log(`${targetDate}のトレードデータはありませんでした。`);
    }
    
    // シートの書式設定
    formatHistorySheet(sheet);
    
    return {
      success: true,
      message: `${targetDate}の取引履歴をスプレッドシートに保存しました（合計${rowCount}件、損益合計: ${totalProfit.toFixed(2)}）`,
      details: {
        date: targetDate,
        tradeCount: rowCount,
        totalProfit: totalProfit
      }
    };
  } catch (error) {
    Logger.log('スプレッドシート出力中にエラーが発生しました: ' + error.message);
    Logger.log(error.stack); // エラーの詳細をログに出力
    return {
      success: false,
      message: 'スプレッドシート出力中にエラーが発生しました: ' + error.message,
      details: error.stack
    };
  }
}

/**
 * 履歴シートの書式を設定する関数
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet - 対象シート
 */
function formatHistorySheet(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return; // データがない場合は処理不要

  const numColumns = 11; // 新しい列数

  // 列インデックス (1-based)
  const tradeTimestampCol = 4; // D列: 取引日時
  const priceCol = 5;          // E列: 価格
  const pnlCol = 6;            // F列: 損益
  const feesCol = 7;           // G列: 手数料

  // 日付列のフォーマット
  sheet.getRange(2, tradeTimestampCol, lastRow - 1, 1).setNumberFormat('yyyy-MM-dd HH:mm:ss');
  
  // 数値列のフォーマット
  sheet.getRange(2, priceCol, lastRow - 1, 1).setNumberFormat('#,##0.00');  // 価格
  sheet.getRange(2, pnlCol, lastRow - 1, 1).setNumberFormat('#,##0.00');   // 損益
  sheet.getRange(2, feesCol, lastRow - 1, 1).setNumberFormat('#,##0.00');  // 手数料
  
  // 条件付き書式の設定（損益列 F列）
  removeExistingConditionalFormatRules(sheet); // 既存のルールをクリア
  
  const plRange = sheet.getRange(2, pnlCol, lastRow - 1, 1);
  
  const positiveRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThan(0)
    .setBackground('#d9ead3') // 薄い緑
    .setRanges([plRange])
    .build();
  
  const negativeRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberLessThan(0)
    .setBackground('#f4cccc') // 薄い赤
    .setRanges([plRange])
    .build();
  
  const rules = sheet.getConditionalFormatRules();
  rules.push(positiveRule);
  rules.push(negativeRule);
  sheet.setConditionalFormatRules(rules);
  
  // 列幅の調整
  if (sheet.getLastColumn() > 0) {
      sheet.autoResizeColumns(1, Math.min(numColumns, sheet.getLastColumn()));
  }
  
  // フィルターの設定（ヘッダー行）
  const headerRange = sheet.getRange(1, 1, 1, Math.min(numColumns, sheet.getLastColumn()));
  if (lastRow > 0 && sheet.getLastColumn() > 0) {
    if (sheet.getFilter()) {
      sheet.getFilter().remove();
    }
    headerRange.createFilter();
  }
}


/**
 * 既存の条件付き書式ルールを削除する関数
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet - 対象シート
 */
function removeExistingConditionalFormatRules(sheet) {
  sheet.setConditionalFormatRules([]);
}

/**
 * 設定シートの最終実行日時を更新する関数
 */
function updateConfigLastRun() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const configSheet = ss.getSheetByName(CONFIG.CONFIG_SHEET_NAME);
  
  if (configSheet) {
    const dataRange = configSheet.getDataRange();
    const values = dataRange.getValues();
    
    for (let i = 0; i < values.length; i++) {
      if (values[i][0] === '最終実行日時') {
        configSheet.getRange(i + 1, 2).setValue(new Date().toLocaleString());
        break;
      }
    }
  }
}

/**
 * トリガー状態を更新する関数
 * @param {string} status - トリガーステータス
 */
function updateTriggerStatus(status) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const configSheet = ss.getSheetByName(CONFIG.CONFIG_SHEET_NAME);
  
  if (configSheet) {
    const dataRange = configSheet.getDataRange();
    const values = dataRange.getValues();
    
    for (let i = 0; i < values.length; i++) {
      if (values[i][0] === '自動実行ステータス') {
        configSheet.getRange(i + 1, 2).setValue(status);
        break;
      }
    }
  }
}

/**
 * ログシートに実行履歴を記録する関数
 * @param {Object} logData - ログデータ
 * @param {Date} logData.date - 実行日時
 * @param {string} logData.function - 実行関数名
 * @param {string} logData.targetDate - 対象日
 * @param {string} logData.status - ステータス (成功/失敗)
 * @param {string} logData.message - メッセージ
 * @param {string} [logData.details] - 詳細情報 (エラー時のスタックトレースなど)
 */
function logExecution(logData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let logSheet = ss.getSheetByName(CONFIG.LOG_SHEET_NAME);
  
  if (!logSheet) {
    logSheet = ss.insertSheet(CONFIG.LOG_SHEET_NAME);
    logSheet.appendRow(['実行日時', '実行関数', '対象日', 'ステータス', 'メッセージ', '詳細']);
    logSheet.getRange('A1:F1').setFontWeight('bold');
    logSheet.getRange('A1:F1').setBackground('#f3f3f3');
  }
  
  logSheet.appendRow([
    logData.date instanceof Date ? Utilities.formatDate(logData.date, CONFIG.TIMEZONE, 'yyyy-MM-dd HH:mm:ss') : logData.date,
    logData.function,
    logData.targetDate,
    logData.status,
    logData.message,
    logData.details || ''
  ]);
  
  const maxLogRows = 100;
  const currentRows = logSheet.getLastRow();
  
  if (currentRows > maxLogRows + 1) {
    logSheet.deleteRows(2, currentRows - maxLogRows - 1);
  }
  
  if (logSheet.getLastColumn() > 0) {
      logSheet.autoResizeColumns(1, logSheet.getLastColumn());
  }
}

/**
 * 結果をメールで通知する関数
 * @param {Object} result - 処理結果
 * @param {string} targetDate - 対象日
 */
function sendNotificationEmail(result, targetDate) {
  if (!CONFIG.EMAIL_NOTIFICATION || !CONFIG.NOTIFICATION_EMAIL) {
    return;
  }
  
  try {
    const spreadsheetName = SpreadsheetApp.getActiveSpreadsheet().getName();
    const subject = result.success ? 
      `✅ トレード履歴取得成功 (${targetDate})` : 
      `❌ トレード履歴取得失敗 (${targetDate})`;
    
    let body = `トレード履歴自動取得の実行結果をお知らせします。\n\n`;
    body += `スプレッドシート: ${spreadsheetName}\n`;
    body += `対象日: ${targetDate}\n`;
    body += `実行日時: ${new Date().toLocaleString()}\n`;
    body += `ステータス: ${result.success ? '成功' : '失敗'}\n`;
    body += `メッセージ: ${result.message}\n\n`;
    
    if (result.success && result.details) {
      body += `取引件数: ${result.details.tradeCount}件\n`;
      body += `合計損益: ${result.details.totalProfit.toFixed(2)}\n\n`;
    }
    
    body += `スプレッドシートURL: ${SpreadsheetApp.getActiveSpreadsheet().getUrl()}\n\n`;
    body += `このメールは自動送信されています。`;
    
    MailApp.sendEmail({
      to: CONFIG.NOTIFICATION_EMAIL,
      subject: subject,
      body: body
    });
  } catch (error) {
    Logger.log(`メール送信中にエラーが発生しました: ${error.message}`);
    logExecution({
        date: new Date(),
        function: 'sendNotificationEmail',
        targetDate: targetDate,
        status: '失敗',
        message: `メール送信中にエラーが発生しました: ${error.message}`,
        details: error.stack || ''
    });
  }
}

/**
 * エラーをメールで通知する関数
 * @param {string} errorMessage - エラーメッセージ
 */
function sendErrorEmail(errorMessage) {
  if (!CONFIG.EMAIL_NOTIFICATION || !CONFIG.NOTIFICATION_EMAIL) {
    return;
  }
  
  try {
    const spreadsheetName = SpreadsheetApp.getActiveSpreadsheet().getName();
    const subject = `❌ トレード履歴自動取得でエラーが発生しました`;
    
    let body = `トレード履歴自動取得の実行中にエラーが発生しました。\n\n`;
    body += `スプレッドシート: ${spreadsheetName}\n`;
    body += `実行日時: ${new Date().toLocaleString()}\n`;
    body += `エラー: ${errorMessage}\n\n`;
    body += `スプレッドシートURL: ${SpreadsheetApp.getActiveSpreadsheet().getUrl()}\n\n`;
    body += `このエラーを解決するには、スクリプトエディタでログやコードを確認してください。\n\n`;
    body += `このメールは自動送信されています。`;
    
    MailApp.sendEmail({
      to: CONFIG.NOTIFICATION_EMAIL,
      subject: subject,
      body: body
    });
  } catch (error) {
    Logger.log(`エラーメール送信中にエラーが発生しました: ${error.message}`);
     logExecution({
        date: new Date(),
        function: 'sendErrorEmail',
        targetDate: '-',
        status: '失敗',
        message: `エラーメール送信中にエラーが発生しました: ${error.message}`,
        details: error.stack || ''
    });
  }
}

// 以下、API通信関連の関数

/**
 * メイン実行関数
 * 指定日の取引履歴を取得します
 * @param {string} targetDate - 対象日（YYYY-MM-DD形式）
 * @return {Object} 取引履歴結果
 */
function getTradeHistory(targetDate) {
  try {
    const token = authenticate(CONFIG.USERNAME, CONFIG.API_KEY);
    if (!token) {
      throw new Error('認証に失敗しました。トークンが取得できませんでした。');
    }
    
    // アカウント情報の取得
    const allAccounts = searchAccounts(token); // まずAPIから全てのアクティブアカウントを取得
    if (!allAccounts || allAccounts.length === 0) {
      return { success: false, message: 'アクティブなアカウントが見つかりませんでした' };
    }
    Logger.log(`APIから取得したアカウント数: ${allAccounts.length}件`);
    allAccounts.forEach(acc => Logger.log(` - ${acc.name} (ID: ${acc.id})`));

    // アカウント名が "PRACTICE" で始まるものを除外するフィルタリング処理
    const filteredAccounts = allAccounts.filter(account => {
      if (account && typeof account.name === 'string') {
        return !account.name.toUpperCase().startsWith('PRACTICE'); // 大文字・小文字を区別せずに "PRACTICE"で始まるかチェック
      }
      return false; // account.name がない、または文字列でない場合は除外 (安全のため)
    });

    Logger.log(`"PRACTICE"アカウントを除外した後のアカウント数: ${filteredAccounts.length}件`);
    if (filteredAccounts.length > 0) {
        filteredAccounts.forEach(acc => Logger.log(` -- 対象アカウント: ${acc.name} (ID: ${acc.id})`));
    }


    if (filteredAccounts.length === 0) {
      return { success: false, message: 'PRACTICEアカウントを除外した結果、対象となる取引アカウントが見つかりませんでした。' };
    }
    
    const { startTimestamp, endTimestamp } = getDateTimestamps(targetDate);
    
    const results = [];
    
    // フィルタリングされたアカウントリストに対して処理を実行
    filteredAccounts.forEach(account => {
      Logger.log(`アカウント ${account.name} (ID: ${account.id}) の取引履歴を取得します。`);
      const trades = searchTrades(token, account.id, startTimestamp, endTimestamp);
      results.push({
        accountId: account.id,
        // accountName: account.name, // スプレッドシートには出力しないが、ログや内部処理で利用可能
        // balance: account.balance,  // スプレッドシートには出力しない
        tradeCount: trades.length,
        trades: trades
      });
    });
    
    return {
      success: true,
      date: targetDate,
      results: results
    };
  } catch (error) {
    Logger.log('取引履歴取得処理(getTradeHistory)でエラーが発生しました: ' + error.message);
    Logger.log(error.stack);
    return {
      success: false,
      message: '取引履歴取得処理エラー: ' + error.message,
      details: error.stack
    };
  }
}

/**
 * API認証を行い、トークンを取得します
 * @param {string} userName - ユーザー名
 * @param {string} apiKey - APIキー
 * @return {string | null} 認証トークン。失敗時はErrorをthrow
 */
function authenticate(userName, apiKey) {
  const url = CONFIG.BASE_URL + CONFIG.AUTH_ENDPOINT;
  const payload = {
    userName: userName,
    apiKey: apiKey
  };
  
  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };
  
  try {
    Logger.log(`認証リクエスト開始: ${url}`);
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    const responseBody = response.getContentText();
    Logger.log(`認証レスポンス (${responseCode}): ${responseBody}`);
    
    const responseData = JSON.parse(responseBody);
    
    if (responseCode === 200 && responseData.success && responseData.errorCode === 0 && responseData.token) {
      Logger.log('認証成功');
      return responseData.token;
    } else {
      const errorMessage = `認証エラー (${responseCode}): ${responseData.errorMessage || responseBody || '不明なエラー'}`;
      Logger.log(errorMessage);
      throw new Error(errorMessage);
    }
  } catch (error) {
    Logger.log(`認証中に予期せぬエラー: ${error.message}`);
    Logger.log(error.stack);
    if (error instanceof SyntaxError) {
        throw new Error(`認証レスポンスの解析に失敗しました。レスポンス内容を確認してください。 詳細: ${error.message}`);
    }
    throw error;
  }
}

/**
 * アカウント情報を検索します
 * @param {string} token - 認証トークン
 * @return {Array | null} アカウント情報の配列。失敗時はErrorをthrow
 */
function searchAccounts(token) {
  const url = CONFIG.BASE_URL + CONFIG.ACCOUNT_SEARCH_ENDPOINT;
  const payload = {
    onlyActiveAccounts: true
  };
  
  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    headers: {
      'Authorization': 'Bearer ' + token
    },
    muteHttpExceptions: true
  };
  
  try {
    Logger.log(`アカウント検索リクエスト開始: ${url}`);
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    const responseBody = response.getContentText();
    Logger.log(`アカウント検索レスポンス (${responseCode}): ${responseBody}`);

    const responseData = JSON.parse(responseBody);
    
    if (responseCode === 200 && responseData.success && responseData.errorCode === 0 && responseData.accounts) {
      Logger.log(`アカウント検索成功: ${responseData.accounts.length}件のアカウントが見つかりました。`);
      return responseData.accounts; // アカウントID、アカウント名、残高などを含む配列が返る想定
    } else {
      const errorMessage = `アカウント検索エラー (${responseCode}): ${responseData.errorMessage || responseBody || '不明なエラー'}`;
      Logger.log(errorMessage);
      throw new Error(errorMessage);
    }
  } catch (error) {
    Logger.log(`アカウント検索中に予期せぬエラー: ${error.message}`);
    Logger.log(error.stack);
    if (error instanceof SyntaxError) {
        throw new Error(`アカウント検索レスポンスの解析に失敗しました。レスポンス内容を確認してください。 詳細: ${error.message}`);
    }
    throw error;
  }
}

/**
 * 取引履歴を検索します
 * @param {string} token - 認証トークン
 * @param {number} accountId - アカウントID
 * @param {string} startTimestamp - 開始タイムスタンプ (ISO 8601形式)
 * @param {string} endTimestamp - 終了タイムスタンプ (ISO 8601形式)
 * @return {Array | null} 取引履歴の配列。失敗時はErrorをthrow
 */
function searchTrades(token, accountId, startTimestamp, endTimestamp) {
  const url = CONFIG.BASE_URL + CONFIG.TRADE_SEARCH_ENDPOINT;
  const payload = {
    accountId: accountId,
    startTimestamp: startTimestamp,
    endTimestamp: endTimestamp
  };
  
  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    headers: {
      'Authorization': 'Bearer ' + token
    },
    muteHttpExceptions: true
  };
  
  try {
    Logger.log(`取引検索リクエスト開始 (AccountID: ${accountId}): ${url}`);
    const response = UrlFetchApp.fetch(url, options);
    const responseCode = response.getResponseCode();
    const responseBody = response.getContentText();
    Logger.log(`取引検索レスポンス (${responseCode}) (AccountID: ${accountId}): ${responseBody.substring(0,500)}...`);

    const responseData = JSON.parse(responseBody);
    
    if (responseCode === 200 && responseData.success && responseData.errorCode === 0) {
      Logger.log(`取引検索成功 (AccountID: ${accountId}): ${responseData.trades ? responseData.trades.length : 0}件の取引が見つかりました。`);
      return responseData.trades || [];
    } else {
      const errorMessage = `取引検索エラー (${responseCode}) (AccountID: ${accountId}): ${responseData.errorMessage || responseBody || '不明なエラー'}`;
      Logger.log(errorMessage);
      throw new Error(errorMessage);
    }
  } catch (error) {
    Logger.log(`取引検索中に予期せぬエラー (AccountID: ${accountId}): ${error.message}`);
    Logger.log(error.stack);
    if (error instanceof SyntaxError) {
        throw new Error(`取引検索レスポンスの解析に失敗しました (AccountID: ${accountId})。レスポンス内容を確認してください。 詳細: ${error.message}`);
    }
    throw error;
  }
}

/**
 * 指定日の開始・終了タイムスタンプを生成します (UTC)
 * @param {string} dateString - 日付文字列（YYYY-MM-DD形式）
 * @return {{startTimestamp: string, endTimestamp: string}} 開始・終了タイムスタンプ (ISO 8601形式 UTC) を含むオブジェクト
 */
function getDateTimestamps(dateString) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    throw new Error('無効な日付形式です。YYYY-MM-DD形式で指定してください。');
  }
  
  const startDate = new Date(dateString + 'T00:00:00.000Z');
  const startTimestamp = startDate.toISOString();
  
  const endDate = new Date(dateString + 'T23:59:59.999Z');
  const endTimestamp = endDate.toISOString();
  
  Logger.log(`対象日 ${dateString} のタイムスタンプ: ${startTimestamp} - ${endTimestamp}`);
  
  return {
    startTimestamp: startTimestamp,
    endTimestamp: endTimestamp
  };
}