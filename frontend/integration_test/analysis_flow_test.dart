import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:hemoglobin_guardian/main.dart';
import 'package:hemoglobin_guardian/src/services/api_service.dart';
import '../test/test_config.dart';
import '../test/services/api_service_test.mocks.dart';

// プロバイダーの定義
final apiServiceProvider = Provider<ApiService>((ref) => throw UnimplementedError());
final imagePickerProvider = Provider<ImagePicker>((ref) => throw UnimplementedError());

@GenerateMocks([ApiService, ImagePicker])
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  late MockApiService mockApiService;
  late ImagePicker mockImagePicker;
  late File testImage;

  setUpAll(() async {
    // テストアセットの準備
    await TestConfig.ensureTestAssets();
    if (!await TestConfig.validateTestImage()) {
      fail('テスト用画像が見つかりません: ${TestConfig.testImagePath}');
    }
  });

  setUp(() async {
    mockApiService = MockApiService();
    mockImagePicker = ImagePicker();
    testImage = File(TestConfig.testImagePath);

    // モックの応答を設定
    when(mockApiService.analyzeImage(any)).thenAnswer((_) async => {
      'risk_score': 0.6,
      'risk_level': 'MEDIUM',
      'confidence': 0.85,
      'warnings': ['テスト用の警告メッセージ'],
      'quality_metrics': {
        'is_blurry': false,
        'brightness_score': 0.8,
        'has_proper_lighting': true,
        'has_detected_nail': true,
      },
      'advice': {
        'summary': 'テスト用の栄養アドバイス',
        'iron_rich_foods': ['食材1', '食材2'],
        'meal_suggestions': ['メニュー1', 'メニュー2'],
        'lifestyle_tips': ['アドバイス1', 'アドバイス2'],
      },
    });
  });

  group('統合テスト', () {
    testWidgets('画像解析フローのテスト', (tester) async {
      await tester.runAsync(() async {
        await tester.pumpWidget(
          ProviderScope(
            overrides: [
              apiServiceProvider.overrideWithValue(mockApiService),
              imagePickerProvider.overrideWithValue(mockImagePicker),
            ],
            child: const HemoglobinGuardianApp(),
          ),
        );
        await tester.pumpAndSettle();

        // ギャラリーボタンをタップ
        final galleryButton = find.text('ギャラリーから選択');
        expect(galleryButton, findsOneWidget, reason: 'ギャラリーボタンが見つかりません');
        await tester.tap(galleryButton);
        await tester.pump();

        // 画像選択後の画面遷移を待つ
        await tester.pumpAndSettle();

        // ローディング状態を確認
        expect(find.byType(CircularProgressIndicator), findsOneWidget);
        expect(find.text('画像を解析中...'), findsOneWidget);

        // 解析完了を待つ（タイムアウトを設定）
        await tester.pumpAndSettle(const Duration(seconds: 5));

        // 解析結果が表示されることを確認
        expect(find.text('解析結果'), findsOneWidget, reason: '解析結果が表示されていません');
        expect(find.text('アドバイス'), findsOneWidget, reason: 'アドバイスが表示されていません');
      });
    });
  });
} 