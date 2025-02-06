import pytest
import asyncio
import os
import sys
import logging
from pathlib import Path

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_test_environment():
    """テスト環境のセットアップ"""
    # テストデータディレクトリの確認
    test_data_dir = Path("tests/test_data")
    if not test_data_dir.exists():
        logger.info("テストデータディレクトリを作成します")
        test_data_dir.mkdir(parents=True)

    # テスト用の.env.testファイルの作成
    env_test = Path(".env.test")
    if not env_test.exists():
        logger.info("テスト用の環境変数ファイルを作成します")
        with open(env_test, "w") as f:
            f.write("""
DEBUG=True
HOST=0.0.0.0
PORT=8080
CORS_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]
MAX_REQUESTS_PER_MINUTE=100
BURST_LIMIT=20
RATE_LIMIT_EXPIRE_TIME=60
""".strip())

def run_tests():
    """統合テストの実行"""
    logger.info("統合テストを開始します")
    
    # テスト環境のセットアップ
    setup_test_environment()
    
    # テストの実行
    test_files = [
        "tests/integration/test_cors_integration.py",
        "tests/integration/test_performance.py"
    ]
    
    # pytestの引数を設定
    pytest_args = [
        "-v",  # 詳細な出力
        "--asyncio-mode=auto",  # 非同期テストモード
        "-s",  # 標準出力をキャプチャしない
        "--tb=short",  # トレースバックを短く
        "--maxfail=1",  # 最初の失敗で停止
    ] + test_files
    
    try:
        # テストの実行
        exit_code = pytest.main(pytest_args)
        
        if exit_code == 0:
            logger.info("すべてのテストが成功しました")
        else:
            logger.error("テストが失敗しました")
            sys.exit(exit_code)
            
    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests() 