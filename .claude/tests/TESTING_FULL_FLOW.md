# TESTING_FULL_FLOW.md — ICFES Leveling

> Suite completa de pruebas automatizadas cubriendo el 100% del flujo de usuario.
> Desde onboarding hasta reevaluación mensual.

---

## MAPA DE FLUJO vs TESTS

```
FLUJO DEL USUARIO                    TIPO DE TEST                  ARCHIVO
═══════════════════════════════════════════════════════════════════════════════

1. REGISTRO/LOGIN                    
   ├─ Registro email/password        Unit + Integration (Backend)  test_auth_service.py
   ├─ Login → JWT tokens             Unit + Integration (Backend)  test_auth_service.py
   ├─ Social login (Google/Apple)    Integration (Backend)         test_auth_social.py
   ├─ Refresh token                  Unit (Backend)                test_auth_service.py
   ├─ UI Login Page                  Widget (Flutter)              login_page_test.dart
   └─ UI Register Page               Widget (Flutter)              register_page_test.dart

2. ONBOARDING (5 pasos)
   ├─ Welcome screen                 Widget (Flutter)              onboarding_flow_test.dart
   ├─ Seleccionar meta ICFES         Widget + Unit (Flutter)       onboarding_flow_test.dart
   ├─ Nivel actual                   Widget (Flutter)              onboarding_flow_test.dart
   ├─ Materias de enfoque            Widget (Flutter)              onboarding_flow_test.dart
   ├─ Tiempo disponible              Widget (Flutter)              onboarding_flow_test.dart
   └─ Guardar preferencias           Integration (Backend)         test_onboarding.py

3. DIAGNÓSTICO RÁPIDO
   ├─ Selección 15 preguntas         Unit (Backend)                test_diagnostic_service.py
   ├─ Distribución 3/materia         Unit (Backend)                test_diagnostic_service.py
   ├─ Sin feedback inmediato         Widget (Flutter)              quick_diagnostic_test.dart
   ├─ Cálculo IRT theta              Unit (Backend)                test_irt_engine.py
   ├─ Estimación rango               Unit (Backend)                test_irt_engine.py
   ├─ Detección áreas débiles        Unit (Backend)                test_diagnostic_service.py
   └─ Submit completo                Integration (Backend)         test_diagnostic_flow.py

4. REVELACIÓN DE RESULTADOS
   ├─ Secuencia animada              Widget (Flutter)              results_reveal_test.dart
   ├─ Radar chart 5 materias         Widget (Flutter)              results_reveal_test.dart
   ├─ Rango animado                  Widget (Flutter)              results_reveal_test.dart
   └─ Áreas débiles priorizadas      Widget (Flutter)              results_reveal_test.dart

5. GENERACIÓN PLAN DE ESTUDIO
   ├─ Plan básico por materia        Unit (Backend)                test_study_plan_service.py
   ├─ Plan adaptativo                Integration (Backend)         test_study_plan_service.py
   ├─ Plan AI (GPT/Claude)           Integration (Backend)         test_ai_study_plan.py
   └─ UI Plan de estudio             Widget (Flutter)              study_plan_page_test.dart

6. LOOP DIARIO — PRACTICE MODE
   ├─ Inicio sesión 15 preguntas     Integration (Backend)         test_practice_flow.py
   ├─ Selección inteligente 60/40    Unit (Backend)                test_practice_service.py
   ├─ Anti-gaming: tipo de intento   Unit (Backend)                test_anti_gaming.py
   ├─ Anti-gaming: tiempo mínimo     Unit (Backend)                test_anti_gaming.py
   ├─ Anti-gaming: XP cap/hora       Unit (Backend)                test_anti_gaming.py
   ├─ Anti-gaming: duplicados        Unit (Backend)                test_anti_gaming.py
   ├─ Cálculo XP + speed bonus       Unit (Backend)                test_game_engine.py
   ├─ Cálculo gold                   Unit (Backend)                test_game_engine.py
   ├─ Streak multiplier              Unit (Backend)                test_game_engine.py
   ├─ Corazones: pérdida             Unit (Backend)                test_hearts_service.py
   ├─ Corazones: grace mode          Unit (Backend)                test_hearts_service.py
   ├─ Corazones: regeneración        Unit (Backend)                test_hearts_service.py
   ├─ Mastery update                 Unit (Backend)                test_mastery_service.py
   ├─ Combo system                   Unit (Backend)                test_game_engine.py
   ├─ Lifelines (50/50, AI, Skip)    Unit (Backend)                test_practice_service.py
   ├─ UI pregunta + feedback         Widget (Flutter)              practice_session_test.dart
   ├─ UI combo overlay               Widget (Flutter)              practice_session_test.dart
   ├─ UI anti-gaming badge           Widget (Flutter)              practice_session_test.dart
   └─ UI resultados sesión           Widget (Flutter)              practice_results_test.dart

7. RECOMENDACIÓN VIDEO
   ├─ Análisis patrón error          Unit (Backend)                test_video_recommendation.py
   ├─ Ajuste dificultad              Unit (Backend)                test_video_recommendation.py
   ├─ UI reproductor YouTube         Widget (Flutter)              video_player_test.dart
   └─ Auto-completado 80%            Integration (Flutter)         video_tracking_test.dart

8. MILLIONAIRE MODE
   ├─ Máximo 3 partidas/día          Unit (Backend)                test_millionaire_service.py
   ├─ Dificultad progresiva          Unit (Backend)                test_millionaire_service.py
   ├─ Checkpoints 5/10/15            Unit (Backend)                test_millionaire_service.py
   ├─ Walk away conserva rewards     Unit (Backend)                test_millionaire_service.py
   ├─ Lifelines con costo            Unit (Backend)                test_millionaire_service.py
   └─ UI escalera de premios         Widget (Flutter)              millionaire_page_test.dart

9. BOSS RAID
   ├─ Disponibilidad domingos        Unit (Backend)                test_boss_raid_service.py
   ├─ Costo entrada 100 gold         Unit (Backend)                test_boss_raid_service.py
   ├─ 70/30 distribución preguntas   Unit (Backend)                test_boss_raid_service.py
   ├─ Cálculo daño + combo           Unit (Backend)                test_game_engine.py
   ├─ XP × 3 multiplier              Unit (Backend)                test_boss_raid_service.py
   ├─ Rangos S/A/B/C                 Unit (Backend)                test_boss_raid_service.py
   ├─ Leaderboard top 50             Integration (Backend)         test_boss_raid_flow.py
   └─ UI boss visual + HP bar        Widget (Flutter)              boss_raid_page_test.dart

10. MASTERY + REPETICIÓN ESPACIADA
    ├─ Learning rate correcto/incorr  Unit (Backend)               test_mastery_service.py
    ├─ Decay system                   Unit (Backend)               test_mastery_service.py
    ├─ Prerequisitos 60%              Unit (Backend)               test_mastery_service.py
    ├─ SM-2 intervalos                Unit (Backend)               test_spaced_repetition.py
    ├─ Easiness factor                Unit (Backend)               test_spaced_repetition.py
    ├─ Daily reviews endpoint         Integration (Backend)        test_spaced_repetition.py
    └─ UI mastery tracking            Widget (Flutter)             mastery_page_test.dart

11. LIGAS SEMANALES
    ├─ Creación grupos ~30            Unit (Backend)               test_league_service.py
    ├─ Ranking por XP semanal         Unit (Backend)               test_league_service.py
    ├─ Ascenso/descenso               Unit (Backend)               test_league_service.py
    └─ UI leaderboard                 Widget (Flutter)             leagues_page_test.dart

12. ECONOMÍA VIRTUAL
    ├─ Gold transactions              Unit (Backend)               test_economy_service.py
    ├─ Orbs en batallas               Unit (Backend)               test_economy_service.py
    ├─ Tienda compra/venta            Integration (Backend)        test_store_flow.py
    └─ UI tienda                      Widget (Flutter)             shop_page_test.dart

13. SISTEMA OFFLINE
    ├─ Cache preguntas en Hive        Unit (Flutter)               question_cache_test.dart
    ├─ ActionQueue FIFO               Unit (Flutter)               action_queue_test.dart
    ├─ SyncManager reconexión         Integration (Flutter)        sync_manager_test.dart
    ├─ PendingAnswerSync              Unit (Flutter)               pending_sync_test.dart
    └─ Delta sync                     Integration (Flutter)        sync_manager_test.dart

14. REEVALUACIÓN MENSUAL
    ├─ Nuevo diagnóstico              Integration (Backend)        test_reassessment_flow.py
    ├─ Comparación con baseline       Unit (Backend)               test_reassessment.py
    ├─ Regeneración plan              Integration (Backend)        test_reassessment_flow.py
    └─ Actualización puntaje          Unit (Backend)               test_reassessment.py

15. E2E COMPLETO
    ├─ Registro → Onboarding → Dx     E2E (Flutter)               e2e_full_user_journey_test.dart
    ├─ Practice → Results → Video      E2E (Flutter)               e2e_practice_loop_test.dart
    ├─ Millionaire completo            E2E (Flutter)               e2e_millionaire_test.dart
    ├─ Boss Raid completo              E2E (Flutter)               e2e_boss_raid_test.dart
    └─ Offline → Sync → Verify         E2E (Flutter)               e2e_offline_sync_test.dart

═══════════════════════════════════════════════════════════════════════════════
TOTAL: ~180 test cases | ~45 test files | 5 capas de testing
```

---

## PIRÁMIDE DE TESTING

```
                    ╱╲
                   ╱  ╲
                  ╱ E2E╲           ~15 tests   (flujos completos)
                 ╱______╲
                ╱        ╲
               ╱Integration╲       ~45 tests   (endpoints + DB + cache)
              ╱____________╲
             ╱              ╲
            ╱  Widget Tests  ╲     ~40 tests   (UI components Flutter)
           ╱__________________╲
          ╱                    ╲
         ╱    Unit Tests        ╲  ~80 tests   (lógica pura, fórmulas)
        ╱________________________╲
```
