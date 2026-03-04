import '../../../../features/engagement/data/datasources/engagement_remote_datasource.dart';

class MasteryRepository {
  final EngagementRemoteDataSource _dataSource;

  MasteryRepository(this._dataSource);

  Future<List<dynamic>> getTopics() async {
    return _dataSource.getMasteryTopics();
  }

  // Other mastery related methods
}
