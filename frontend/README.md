# Hemoglobin Guardian

貧血リスクを簡易チェック＆AIアドバイスを行うモバイルアプリケーション

## 開発環境要件

### 必須ソフトウェア
- Flutter SDK 3.27.2以上
- Dart SDK 3.6.1以上
- Java Development Kit (JDK) 17
  - 推奨: Eclipse Temurin JDK 17.0.13+11
- Android Studio Hedgehog | 2023.1.1
- Android SDK Platform 34
- Kotlin 1.9.22

### 環境変数設定
```bash
# Windows
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-17.0.13.11-hotspot
ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk
PATH=%PATH%;%ANDROID_HOME%\platform-tools

# macOS/Linux
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

## プロジェクトのセットアップ

1. リポジトリのクローン
```bash
git clone https://github.com/your-username/hemoglobin-guardian-mvp.git
cd hemoglobin-guardian-mvp
```

2. 依存関係のインストール
```bash
cd frontend
flutter pub get
```

3. Firebaseの設定
- `google-services.json`を`frontend/android/app/`に配置

4. ビルドと実行
```bash
# デバッグビルド
flutter clean
flutter pub get
flutter build apk --debug

# リリースビルド
flutter build apk --release
```

## 開発時の注意事項

### 互換性
- Android minSdkVersion: 21
- Android targetSdkVersion: 34
- Flutter環境: 3.27.2以上
- Dart SDK: 3.6.1以上

### パッケージバージョン
主要な依存パッケージのバージョン：
- firebase_core: ^2.32.0
- cloud_firestore: ^4.17.5
- firebase_auth: ^4.16.0
- google_mlkit_commons: ^0.9.0
- camera: ^0.10.6

### ビルド設定
- Gradle: 8.2.0
- Kotlin: 1.9.22
- Firebase BoM: 32.7.0

## トラブルシューティング

### よくある問題と解決方法
1. Gradle ビルドエラー
   - `flutter clean`を実行
   - Gradleキャッシュをクリア
   - JDK 17が正しく設定されているか確認

2. パッケージの互換性エラー
   - `flutter pub outdated`で更新可能なパッケージを確認
   - `pubspec.yaml`のバージョン制約を確認

3. Firebase設定エラー
   - `google-services.json`の配置を確認
   - アプリケーションIDが一致しているか確認

## 参考リンク
- [Flutter公式ドキュメント](https://docs.flutter.dev/)
- [Firebase Flutter セットアップ](https://firebase.google.com/docs/flutter/setup)
- [ML Kit for Flutter](https://developers.google.com/ml-kit/guides)
