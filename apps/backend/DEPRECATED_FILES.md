# Deprecated Files - ICFES Leveling Backend

This document lists files that are deprecated and should not be used for new development.
These files are kept for backward compatibility but will be removed in a future release.

## Deprecated Routes (apps/backend/app/routes/)

| File | Reason | Replacement |
|------|--------|-------------|
| `simple_recommendations.py` | Redundant | Use `recommendations.py` |
| `study_plans_simple.py` | Redundant | Use `study_plans.py` |
| `simple_study_plan_generator.py` | Redundant | Use `claude_study_plan_generator.py` |
| `analytics.py` | Outdated | Use `analytics_advanced.py` |
| `diagnostic_images_test.py` | Test file | Remove after testing |

## Deprecated Services (apps/backend/app/services/)

### Diagnostic Services (Keep only diagnostic_service.py and diagnostic_two_phase_service.py)
| File | Reason | Replacement |
|------|--------|-------------|
| `diagnostic_service_simple.py` | Redundant | Use `diagnostic_service.py` |
| `enhanced_diagnostic_service.py` | Merged | Use `diagnostic_service.py` |
| `diagnostic_deep_service.py` | Merged | Use `diagnostic_two_phase_service.py` |

### Recommendation Services (Keep only recommendation_service.py and master_recommendation_service.py)
| File | Reason | Replacement |
|------|--------|-------------|
| `intelligent_recommendation_engine.py` | Redundant | Use `master_recommendation_service.py` |
| `smart_recommendation_engine.py` | Redundant | Use `master_recommendation_service.py` |
| `recommendation_scoring_service.py` | Merged | Use `recommendation_service.py` |

### Video Services (Keep only video_service.py and video_recommendation_service.py)
| File | Reason | Replacement |
|------|--------|-------------|
| `intelligent_video_recommendation_service.py` | Redundant | Use `video_recommendation_service.py` |
| `optimized_video_recommendation_engine.py` | Redundant | Use `video_recommendation_service.py` |
| `video_learning_planner.py` | Merged | Use `video_service.py` |
| `master_video_matching_orchestrator.py` | Redundant | Use `video_matching_service.py` |
| `enhanced_video_matcher.py` | Stub only | Use `video_matching_service.py` |
| `enhanced_video_progress_service.py` | Stub only | Use `video_progress_service.py` |

## Migration Notes

1. All deprecated services maintain backward-compatible interfaces
2. New code should use the replacement services
3. Deprecated files will be archived in `/archive/deprecated/` in next major version

## Last Updated
2025-12-28 - Initial deprecation list created
