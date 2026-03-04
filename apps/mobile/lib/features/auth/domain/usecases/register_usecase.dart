import '../repositories/auth_repository.dart';
import '../../../../core/auth/domain/entities/user.dart';

class RegisterUseCase {
  final AuthRepository _repository;

  RegisterUseCase(this._repository);

  Future<User> execute(String email, String password, String name) {
    return _repository.register(email, password, name);
  }
}
