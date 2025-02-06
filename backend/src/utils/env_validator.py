from typing import Dict, List, Optional
import os
from pathlib import Path
import json
from dotenv import load_dotenv

class EnvironmentValidator:
    """環境変数のバリデーションと管理を行うクラス"""

    REQUIRED_VARS = {
        "FIREBASE_CREDENTIALS_PATH": {
            "description": "Firebaseの認証情報ファイルパス",
            "validation": lambda x: Path(x).exists() and x.endswith('.json'),
            "cloud_run": True  # Cloud Runではシークレットとして管理
        },
        "GOOGLE_APPLICATION_CREDENTIALS": {
            "description": "Google Cloudの認証情報ファイルパス",
            "validation": lambda x: Path(x).exists() and x.endswith('.json'),
            "cloud_run": True  # Cloud Runではシークレットとして管理
        },
        "GOOGLE_CLOUD_PROJECT": {
            "description": "Google CloudプロジェクトID",
            "validation": lambda x: bool(x.strip()),
            "cloud_run": False
        },
        "VISION_AI_LOCATION": {
            "description": "Vision AIのロケーション",
            "validation": lambda x: x in ["asia-northeast1", "us-central1", "europe-west1"],
            "cloud_run": False
        },
        "VERTEX_AI_LOCATION": {
            "description": "Vertex AIのロケーション",
            "validation": lambda x: x in ["asia-northeast1", "us-central1", "europe-west1"],
            "cloud_run": False
        },
        "GEMINI_MODEL_ID": {
            "description": "Gemini APIのモデルID",
            "validation": lambda x: x.startswith("gemini-"),
            "cloud_run": False
        }
    }

    OPTIONAL_VARS = {
        "FRONTEND_URL": {
            "description": "フロントエンドのURL",
            "default": "http://localhost:3000",
            "cloud_run": False
        },
        "PORT": {
            "description": "サーバーのポート番号",
            "default": "8080",
            "cloud_run": False
        },
        "HOST": {
            "description": "サーバーのホスト",
            "default": "0.0.0.0",
            "cloud_run": False
        },
        "WORKERS": {
            "description": "ワーカープロセス数",
            "default": "1",
            "cloud_run": False
        },
        "LOG_LEVEL": {
            "description": "ログレベル",
            "default": "INFO",
            "cloud_run": False
        },
        "LOG_FORMAT": {
            "description": "ログフォーマット",
            "default": "json",
            "cloud_run": False
        }
    }

    def __init__(self, env_file: Optional[str] = None):
        """
        環境変数のバリデーターを初期化
        Args:
            env_file: .envファイルのパス（オプション）
        """
        self.is_cloud_run = self._is_running_on_cloud_run()
        
        if not self.is_cloud_run and env_file and Path(env_file).exists():
            load_dotenv(env_file)
        
        self.missing_vars: List[str] = []
        self.invalid_vars: Dict[str, str] = {}
        self.warnings: List[str] = []

    def _is_running_on_cloud_run(self) -> bool:
        """Cloud Run環境で実行されているかどうかを判定"""
        return bool(os.getenv("K_SERVICE"))

    def validate(self) -> bool:
        """
        環境変数をバリデーション
        Returns:
            bool: すべての必須環境変数が正しく設定されているかどうか
        """
        # 必須環境変数のチェック
        for var_name, config in self.REQUIRED_VARS.items():
            # Cloud Run環境でのシークレット管理をスキップ
            if self.is_cloud_run and config.get("cloud_run"):
                continue

            value = os.getenv(var_name)
            if not value:
                self.missing_vars.append(var_name)
                continue
            
            try:
                if not config["validation"](value):
                    self.invalid_vars[var_name] = f"無効な値: {value}"
            except Exception as e:
                self.invalid_vars[var_name] = f"バリデーションエラー: {str(e)}"

        # オプショナル環境変数のチェック
        for var_name, config in self.OPTIONAL_VARS.items():
            if not os.getenv(var_name):
                os.environ[var_name] = config["default"]
                self.warnings.append(f"{var_name}のデフォルト値を使用: {config['default']}")

        # 認証情報ファイルの内容チェック（Cloud Run環境以外）
        if not self.is_cloud_run:
            self._validate_credentials()

        return not (self.missing_vars or self.invalid_vars)

    def _validate_credentials(self):
        """認証情報ファイルの内容をバリデーション（ローカル環境用）"""
        # Firebase認証情報のチェック
        firebase_creds = os.getenv("FIREBASE_CREDENTIALS_PATH")
        if firebase_creds and Path(firebase_creds).exists():
            try:
                with open(firebase_creds) as f:
                    creds_data = json.load(f)
                required_fields = ["type", "project_id", "private_key", "client_email"]
                missing_fields = [field for field in required_fields if field not in creds_data]
                if missing_fields:
                    self.invalid_vars["FIREBASE_CREDENTIALS_PATH"] = f"必須フィールドが不足: {', '.join(missing_fields)}"
            except json.JSONDecodeError:
                self.invalid_vars["FIREBASE_CREDENTIALS_PATH"] = "JSONの解析に失敗"
            except Exception as e:
                self.invalid_vars["FIREBASE_CREDENTIALS_PATH"] = f"ファイルの読み込みに失敗: {str(e)}"

        # Google Cloud認証情報のチェック
        gcp_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if gcp_creds and Path(gcp_creds).exists():
            try:
                with open(gcp_creds) as f:
                    creds_data = json.load(f)
                required_fields = ["type", "project_id", "private_key", "client_email"]
                missing_fields = [field for field in required_fields if field not in creds_data]
                if missing_fields:
                    self.invalid_vars["GOOGLE_APPLICATION_CREDENTIALS"] = f"必須フィールドが不足: {', '.join(missing_fields)}"
            except json.JSONDecodeError:
                self.invalid_vars["GOOGLE_APPLICATION_CREDENTIALS"] = "JSONの解析に失敗"
            except Exception as e:
                self.invalid_vars["GOOGLE_APPLICATION_CREDENTIALS"] = f"ファイルの読み込みに失敗: {str(e)}"

    def get_validation_report(self) -> Dict:
        """
        バリデーション結果のレポートを生成
        Returns:
            Dict: バリデーション結果のレポート
        """
        return {
            "status": "valid" if not (self.missing_vars or self.invalid_vars) else "invalid",
            "environment": "cloud_run" if self.is_cloud_run else "local",
            "missing_variables": self.missing_vars,
            "invalid_variables": self.invalid_vars,
            "warnings": self.warnings
        }

    def print_validation_report(self):
        """バリデーション結果を標準出力に出力"""
        report = self.get_validation_report()
        
        print("\n=== 環境変数バリデーションレポート ===")
        print(f"ステータス: {report['status']}")
        print(f"実行環境: {report['environment']}")
        
        if report['missing_variables']:
            print("\n未設定の必須環境変数:")
            for var in report['missing_variables']:
                print(f"- {var}: {self.REQUIRED_VARS[var]['description']}")
        
        if report['invalid_variables']:
            print("\n無効な環境変数:")
            for var, error in report['invalid_variables'].items():
                print(f"- {var}: {error}")
        
        if report['warnings']:
            print("\n警告:")
            for warning in report['warnings']:
                print(f"- {warning}")
        
        print("\n推奨される対応:")
        if report['status'] == "invalid":
            if report['environment'] == "cloud_run":
                print("1. Cloud Runの環境変数設定を確認してください")
                print("2. シークレットマネージャーの設定を確認してください")
            else:
                print("1. .envファイルを確認し、必須環境変数を設定してください")
                print("2. 認証情報ファイルのパスと内容を確認してください")
            print("3. 環境変数の値が正しい形式であることを確認してください")
        else:
            print("- すべての環境変数が正しく設定されています") 