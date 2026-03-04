import '../repositories/auth_repository.dart';
import '../../../../core/auth/domain/entities/user.dart';

class LoginUseCase {
  final AuthRepository _repository;

  LoginUseCase(this._repository);

  Future<User> execute(String email, String password) {
    return _repository.login(email, password);
  }
}
