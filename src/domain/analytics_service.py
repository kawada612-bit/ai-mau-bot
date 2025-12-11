import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from src.core import config
from src.core.logger import setup_logger
from supabase import create_client

logger = setup_logger(__name__)

class AnalyticsService:
    def __init__(self):
        self.supabase = None
        if config.SUPABASE_URL and config.SUPABASE_KEY:
            self.supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        self._cache_df = None
        self._cache_expires_at = datetime.min

    def get_schema_info(self) -> str:
        """AIに提示するテーブル定義"""
        return """
Table: schedules
Columns:
  - title (text): イベント名
  - start_at (text): 開始日時 (ISO 8601 format: YYYY-MM-DDTHH:MM:SS)
  - description (text): 詳細メモ
"""

    def _get_fresh_connection(self):
        """Supabaseからデータを取得し、SQLiteコネクションを返す（キャッシュ有効5分）"""
        if not self.supabase:
            logger.warning("Supabase not configured, returning empty DB")
            conn = sqlite3.connect(':memory:')
            return conn

        now = datetime.now()
        
        # キャッシュが有効ならそれを使う
        if self._cache_df is not None and now < self._cache_expires_at:
            df = self._cache_df
        else:
            logger.info("🔄 Analytics: Supabaseから全件データを取得中...")
            try:
                res = self.supabase.table("schedules").select("*").execute()
                df = pd.DataFrame(res.data)
                
                # 日付型変換 (SQLite用に文字列化しておくが、Pandas上ではdatetimeの方が扱いやすい場合もある。
                # ここではSQLiteに入れるのでISO文字列であればOKだが、
                # 念のためPandasでdatetime変換してからまた文字列にするなどの整合性を取る)
                if 'start_at' in df.columns:
                    # Supabaseから返ってくるのはISO文字列なのでそのままでOKだが、
                    # 解析のために一度datetimeにする手もある。
                    # 今回はSQLiteの date() 関数などを使うため、標準的なISOフォーマット文字列で格納されていれば良い。
                    pass
                
                self._cache_df = df
                self._cache_expires_at = now + timedelta(minutes=5)
            except Exception as e:
                logger.error(f"Analytics Data Fetch Error: {e}")
                # エラー時は空のDFを返すかキャッシュを使う
                if self._cache_df is None:
                    df = pd.DataFrame(columns=["title", "start_at", "description"])
                else:
                    df = self._cache_df

        # インメモリDB作成
        conn = sqlite3.connect(':memory:')
        # SQLiteの日付関数で扱いやすいように文字列(ISO)で保存
        if self._cache_df is not None:
             self._cache_df.to_sql('schedules', conn, index=False, if_exists='replace')
        return conn

    def execute_query(self, sql_query: str) -> str:
        """AIが生成したSQLを実行する"""
        conn = self._get_fresh_connection()
        try:
            # 安全対策: SQLのクリーニング
            # Markdownのコードブロック記号を削除
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

            # 簡易セキュリティ: SELECT以外は禁止
            if not sql_query.upper().startswith("SELECT"):
                logger.warning(f"Blocked non-SELECT query: {sql_query}")
                return "エラー: 安全のため、SELECTクエリ以外は実行できません。"

            logger.info(f"🔍 Executing SQL: {sql_query}")
            result_df = pd.read_sql_query(sql_query, conn)
            
            if result_df.empty:
                return "（条件に一致する予定はありませんでした）"
            
            # AIが読みやすいMarkdown形式で返す
            return result_df.to_markdown(index=False)

        except Exception as e:
            logger.error(f"SQL Execution Error: {e} | Query: {sql_query}")
            return f"データ検索中にエラーが発生しました: {e}"
        finally:
            conn.close()
