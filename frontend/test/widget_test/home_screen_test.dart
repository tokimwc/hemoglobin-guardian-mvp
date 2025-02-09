import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:hemoglobin_guardian/screens/home_screen.dart';
import 'package:hemoglobin_guardian/providers/auth_provider.dart';
import 'package:hemoglobin_guardian/providers/analysis_provider.dart';
import 'package:mockito/mockito.dart';

class MockAuthNotifier extends Mock implements AuthNotifier {}

class MockAnalysisNotifier extends Mock implements AnalysisNotifier {}

void main() {
  late MockAuthNotifier mockAuthNotifier;
  late MockAnalysisNotifier mockAnalysisNotifier;

  setUp(() {
    mockAuthNotifier = MockAuthNotifier();
    mockAnalysisNotifier = MockAnalysisNotifier();
  });

  testWidgets('ホーム画面の初期表示テスト', (WidgetTester tester) async {
    // 認証済みユーザーの状態をモック
    when(mockAuthNotifier.isAuthenticated).thenReturn(true);
    when(mockAuthNotifier.currentUser)
        .thenReturn(User(id: 'test-user', email: 'test@example.com'));

    // 最新の解析結果をモック
    when(mockAnalysisNotifier.latestResult).thenReturn(AnalysisResult(
      riskLevel: RiskLevel.LOW,
      confidence: 0.95,
      advice: '鉄分を含む食事を継続的に摂取することをお勧めします。',
      timestamp: DateTime.now(),
    ));

    // ウィジェットをビルド
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWithValue(mockAuthNotifier),
          analysisProvider.overrideWithValue(mockAnalysisNotifier),
        ],
        child: MaterialApp(
          home: HomeScreen(),
        ),
      ),
    );

    // 要素の存在を検証
    expect(find.text('ヘモグロビンガーディアン'), findsOneWidget);
    expect(find.byIcon(Icons.camera_alt), findsOneWidget);
    expect(find.byType(ElevatedButton), findsOneWidget);

    // リスクレベルの表示を検証
    expect(find.text('リスクレベル: 低'), findsOneWidget);
    expect(find.text('信頼度: 95%'), findsOneWidget);

    // アドバイスの表示を検証
    expect(find.text('鉄分を含む食事を継続的に摂取することをお勧めします。'), findsOneWidget);
  });

  testWidgets('カメラボタンタップ時の動作テスト', (WidgetTester tester) async {
    // 認証済みユーザーの状態をモック
    when(mockAuthNotifier.isAuthenticated).thenReturn(true);
    when(mockAuthNotifier.currentUser)
        .thenReturn(User(id: 'test-user', email: 'test@example.com'));

    // ウィジェットをビルド
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWithValue(mockAuthNotifier),
          analysisProvider.overrideWithValue(mockAnalysisNotifier),
        ],
        child: MaterialApp(
          home: HomeScreen(),
        ),
      ),
    );

    // カメラボタンをタップ
    await tester.tap(find.byIcon(Icons.camera_alt));
    await tester.pumpAndSettle();

    // カメラ画面への遷移を検証
    verify(mockAnalysisNotifier.startCamera()).called(1);
  });

  testWidgets('未認証時のログイン画面リダイレクトテスト', (WidgetTester tester) async {
    // 未認証状態をモック
    when(mockAuthNotifier.isAuthenticated).thenReturn(false);

    // ウィジェットをビルド
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          authProvider.overrideWithValue(mockAuthNotifier),
          analysisProvider.overrideWithValue(mockAnalysisNotifier),
        ],
        child: MaterialApp(
          home: HomeScreen(),
        ),
      ),
    );

    // ログイン画面への遷移を検証
    expect(find.byType(LoginScreen), findsOneWidget);
  });
}
