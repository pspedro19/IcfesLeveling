// Basic smoke test to verify the app can be imported.
import 'package:flutter_test/flutter_test.dart';

import 'package:icfes_mobile/main.dart';

void main() {
  test('app entry point is importable', () {
    // Verify the main module can be imported without errors.
    // Full widget tests are in test/widget/pages/.
    expect(main, isNotNull);
  });
}
