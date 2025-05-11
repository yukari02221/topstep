function importTradesFromJson() {
  // --- 設定項目 ---
  const JSON_FILE_ID = '';
  const TARGET_SHEET_NAME = '取引履歴';
  const CREATE_HEADER_ROW = false;
  // --- 設定項目ここまで ---

  const ui = SpreadsheetApp.getUi();

  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(TARGET_SHEET_NAME);
    if (!sheet) {
      sheet = ss.insertSheet(TARGET_SHEET_NAME);
      ui.alert(`シート「${TARGET_SHEET_NAME}」を新規作成しました。`);
    }

    const jsonFile = DriveApp.getFileById(JSON_FILE_ID);
    const jsonString = jsonFile.getBlob().getDataAsString();
    const jsonData = JSON.parse(jsonString);
    const trades = jsonData.trades;

    if (!trades || trades.length === 0) {
      ui.alert('JSONファイル内に取引データが見つかりませんでした。');
      return;
    }

    const dataToWrite = [];
    // カラムのインデックスを定義しておくと後で使いやすい
    const COL_INDEX_PROFIT_LOSS = 5; // 損益 (profitAndLoss) は0から数えて5番目の要素 (F列に対応)
    // 他のカラムインデックスも必要に応じて定義可能

    for (const trade of trades) {
      let formattedTimestamp = "";
      if (trade.creationTimestamp) {
        try {
          const dateObj = new Date(trade.creationTimestamp);
          if (!isNaN(dateObj.getTime())) {
            formattedTimestamp = Utilities.formatDate(dateObj, "Asia/Tokyo", "yyyy/MM/dd HH:mm:ss");
          } else {
            Logger.log(`Invalid date for creationTimestamp: ${trade.creationTimestamp}`);
            formattedTimestamp = trade.creationTimestamp;
          }
        } catch (e) {
          Logger.log(`Error formatting date for creationTimestamp: ${trade.creationTimestamp}. Error: ${e}`);
          formattedTimestamp = trade.creationTimestamp;
        }
      }

      let sideInJapanese = "";
      if (trade.side === 1) {
        sideInJapanese = "買い";
      } else if (trade.side === 0) {
        sideInJapanese = "売り";
      } else {
        sideInJapanese = String(trade.side);
        if (trade.side !== null && typeof trade.side !== 'undefined') {
             Logger.log(`Unknown side value: ${trade.side} for trade ID: ${trade.id}`);
        }
      }

      const rowData = [
        trade.id,
        trade.accountId,
        trade.contractId,
        formattedTimestamp,
        trade.price,
        trade.profitAndLoss, // この値に基づいて色を塗る
        trade.fees,
        sideInJapanese,
        trade.size,
        trade.voided,
        trade.orderId
      ];
      dataToWrite.push(rowData);
    }

    if (dataToWrite.length > 0) {
      const startRow = sheet.getLastRow() + 1;
      const numRows = dataToWrite.length;
      const numCols = dataToWrite[0].length;

      // データを一括書き込み
      sheet.getRange(startRow, 1, numRows, numCols).setValues(dataToWrite);

      // ★★★ 変更点: 損益に基づいて背景色を設定 ★★★
      const profitLossColumn = COL_INDEX_PROFIT_LOSS + 1; // スプレッドシートの列番号 (1-based)
      const backgroundColors = []; // 背景色を格納する2次元配列

      for (let i = 0; i < numRows; i++) {
        const profit = dataToWrite[i][COL_INDEX_PROFIT_LOSS]; // 書き込んだデータから損益を取得
        let bgColor = null; // デフォルトは色なし (透明)

        if (typeof profit === 'number' && !isNaN(profit)) { // 数値であり、NaNでないことを確認
          if (profit < 0) {
            bgColor = "#f4cccc"; // 明るい赤3
          } else if (profit > 0) {
            bgColor = "#d9ead3"; // 明るい緑3
          }
          // profit === 0 の場合は bgColor = null (色なし) のまま
        }
        // backgroundColors配列には、対象列のみの背景色情報を格納
        // 他の列の色は変更したくないので、ここでは損益列専用の配列を作る
        // もし行全体の背景色を変えたい場合は、numCols分の配列にする
        backgroundColors.push([bgColor]);
      }

      // 損益列の範囲を取得して背景色を一括設定
      if (backgroundColors.length > 0) {
        sheet.getRange(startRow, profitLossColumn, numRows, 1) // (開始行, 損益列番号, 行数, 1列分)
             .setBackgrounds(backgroundColors);
      }

      ui.alert(`${numRows} 件の取引データをシート「${TARGET_SHEET_NAME}」に追加し、損益に応じて色付けしました。`);
    } else {
       ui.alert('追加する新しい取引データはありませんでした。');
    }

  } catch (e) {
    Logger.log(e);
    ui.alert(`エラーが発生しました: ${e.message}\n詳細はログを確認してください。`);
  }
}

// スプレッドシートを開いた時にカスタムメニューを追加する（任意）
function onOpen() {
  SpreadsheetApp.getUi()
      .createMenu('カスタムツール')
      .addItem('JSON取引履歴をインポート', 'importTradesFromJson')
      .addToUi();
}