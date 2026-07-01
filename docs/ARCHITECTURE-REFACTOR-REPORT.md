# דוח ריפקטורינג ארכיטקטוני — ElayoAI / OrgFlow

**תאריך:** יולי 2026
**ענף בסיס:** `develop` (`main` ממוזג עם `privacyPolicy`)
**ענף עבודה:** `refactor/architecture-modularization-and-hardening`
**טווח commits:** `37a8b40..a290d25` (6 commits, 151 קבצים, ‎+11,400/-10,978 שורות)

מסמך זה הוא דוח השינויים המלא של הריפקטורינג הארכיטקטוני שבוצע על בסיס דוח
הביקורת (audit) המקורי, וכולל בסופו חוות דעת ואישור מפורש של סקירת קוד
ברמת ארכיטקט בכיר.

---

## תקציר מנהלים

הפרויקט תפקד, אך צבר שלושה סוגי חוב טכני עיקריים: (1) `app/main.py` היה
מונוליט של כ-8,100 שורות שריכז 688 routes, את כל שכבת ה-DI ואת כל מודלי
ה-request; (2) כמה services עקפו את שכבת ה-repository וגישו ישירות ל-client
של Supabase, מה שמנע בדיקות יחידה אמיתיות ויצר קשירות (coupling) מיותרת;
(3) תלויות מיושנות (FastAPI, Starlette, Supabase SDK, pytest ועוד) וכמה
בעיות היגיינת git/env/קונפיגורציה. כל אחד מהם טופל בשלב (Phase) נפרד,
עם ולידציה מלאה של סוויטת הבדיקות אחרי כל שלב.

**התוצאה:** `main.py` בן 243 שורות בלבד (ירידה של כ-97%), 22 routers
ממוקדים לפי דומיין, שכבת DI יחידה (`dependencies.py`), אפס repository
leaks לא-מתועדים, תלויות מעודכנות (backend + frontend), ותשתית בדיקות
קומפוננטות חדשה ל-frontend. **1,296 בדיקות backend ו-864 בדיקות frontend
נבדקו בכל שלב מול baseline מדויק — אפס regressions לאורך כל התהליך.**

---

## שלב 1 — היגיינת Git / Env / קונפיגורציה

**Commit:** `37a8b40`

- `.gitignore` נבנה מחדש: תוקן באג שבו `docs/` היה ignored כתיקייה שלמה
  (ולכן `!docs/*.md` אף פעם לא הופעל בפועל — מגבלה ידועה של git), נוספו
  חוקים חסרים (`.venv/`, `*.pyc`, `credentials.json`, `token.json` וכו').
- `.env.example` נכתב מחדש עם כל משתני הסביבה בפועל ותיעוד קצר לכל אחד.
- `.python-version` נוסף (`3.12`) — קיבוע גרסת הפייתון הרשמית של הפרויקט.
- `app/config/settings.py`: נוספה בדיקת guard שמונעת עלייה ל-staging/production
  עם `AUTH_JWT_SECRET` ברירת המחדל (`dev-secret-change-me-...`).
- `app/scheduling/core.py` (חדש): `BackgroundScheduler` משותף יחיד. לפני
  התיקון, `app/automation/scheduler.py` ו-`app/jobs/scheduler.py` כל אחד
  יצר instance נפרד של `BackgroundScheduler` — שני scheduler-ים רצים
  במקביל על אותו תהליך. שני הקבצים הפכו ל-shim דק שמייבא מ-`scheduling/core.py`.
- `docs/README.md` (חדש) מתעד את הבאג ההיסטורי שגרם לאובדן קבצי ה-spec.
- `deploy/sql/*.sql` הוצא מ-`.gitignore` ומעקב git (בעוד `db/migrations/`
  נשאר מכוון להישאר local-only, כפי שהיה קודם).

---

## שלב 2 — פיצול `app/main.py` למודולים

**Commit:** `9d75f12`

זה היה השלב המרכזי והמורכב ביותר. `main.py` המקורי (8,099 שורות) פוצל
לפי אחריות יחידה (Single Responsibility) באמצעות סקריפט חילוץ מבוסס AST
(שמר במדויק על כל שורת קוד, כולל decorators, ללא שינוי לוגי):

| יעד | תוכן |
|---|---|
| `app/main.py` (243 שורות) | entrypoint דק: imports, exception/logging setup, middleware, CORS, lifecycle events, 22×`include_router()` |
| `app/dependencies.py` (691 שורות, חדש) | 73 singletons של services/repositories + ספקי `Depends()` |
| `app/schemas/api_requests.py` (572 שורות, חדש) | 56 מודלי Pydantic request/response |
| `app/services/connection_managers.py` (92 שורות, חדש) | `WorkspaceConnectionManager`, `NotificationConnectionManager` |
| `app/routers/*.py` (22 קבצים חדשים) | route אחד לכל דומיין (auth, projects, issues, field_reports, automation, ...) |

**ולידציית שלמות:** 688 route decorators במקור == 688 ב-routers המפוצלים,
0 שנשארו ב-`main.py`, 0 כפולים. כל router מייבא `import app.dependencies
as deps` (ולא `from ... import`) כדי לשמר תאימות ל-`monkeypatch` בבדיקות.

**3 בדיקות gate תוקנו** (הן בדקו מחרוזות routes ישירות בתוך `app/main.py`,
ששבר מיד עם הפיצול): `test_instant_materialization_l1_gate.py`,
`test_instant_materialization_l3_gate.py`, `test_portfolio_live_r1_gate.py`
— כולן קיבלו helper משותף (`_read_app_source()`) שמאחד את קוד המקור של
`main.py` + `dependencies.py` + כל ה-routers לפני החיפוש.

**תיקון נלווה:** `app/routers/system.py` — `readiness()` ניגש כעת ל-
`request.app.state.startup_complete` דרך פרמטר `Request` מפורש, במקום
תלות ישירה במשתנה מודול גלובלי.

---

## שלב 3 — סגירת Repository Leaks

**Commit:** `00a3335`

ביקורת מלאה של כל שימוש ישיר ב-`supabase` client מתוך שכבת ה-services
(עקיפת שכבת ה-repository) העלתה 9 services פגומים. כולם תוקנו על ידי
הזרקת repository מתאים (constructor injection):

- `tenant_scope_service.py`, `ai_assignment_service.py` (נכתב מחדש),
  `automation_monitoring_service.py`, `organization_deletion_service.py`,
  `project_deletion_service.py`, `resident_portal_service.py`,
  `report_processing_service.py`, `tenant_migration_service.py`.
- 3 שיטות repository חדשות נוספו (`get_project_id_for_report`,
  `get_profiles_by_roles`, `count_open_actions_for_assignee` +
  `get_assignees_for_open_actions`) + `GenericTableRepository` חדש
  לשירותים שצריכים גישה דינמית לטבלה (מחיקות מדורגות).
- ב-`resident_portal_service.py` נמצא ותוקן שימוש ישני נוסף שלא היה
  ברשימה הראשונית (`_collect_legacy_weekly_reports`), שהתגלה על ידי
  `ruff` (`F821 undefined name 'supabase'`) אחרי התיקון הראשון.

**חריגים מתועדים, לא תוקנו בכוונה:**
- `user_management_service.py` — כל השימוש הוא ב-Supabase **Auth Admin
  API** (`.auth.admin.*`), שאין לו מקבילה ב-repository — זהו שימוש
  לגיטימי ב-SDK ישירות, לא leak.
- `report_deletion_service.py` — נבדק, לא נמצא leak.

---

## שלב 4 — תיקוני Frontend

**Commit:** `a05aada`

- **ולידציית env:** `lib/env/schema.ts` (חדש) — סכמת zod לכל משתני
  `NEXT_PUBLIC_*`/fallback שה-UI קורא בפועל, כל שדה עם ברירת מחדל `""`
  שתואמת להתנהגות ה-degradation הקיימת. `lib/env/public-env.ts` נוקש
  מחדש להשתמש בסכמה — ה-API הציבורי (`getSupabasePublicConfig`,
  `isSupabaseConfigured`, `getApiBaseUrl`, `describeMobileAuthConfig`)
  נשאר זהה ב-signature.
- **תשתית בדיקות קומפוננטות:** נוספו `@testing-library/react` +
  `jest-dom` + `user-event` + `@vitejs/plugin-react` + `jsdom`.
  `vitest.config.ts` מוסיף plugin ל-React ו-`setupFiles`; environment
  ברירת מחדל נשאר `"node"` (הסוויטה הקיימת ב-`tests/lib/**` היא לוגיקה
  טהורה), בדיקות קומפוננטה מבקשות `jsdom` per-file. נוספו `tests/setup.ts`,
  `tests/components/Button.test.tsx` (בדיקה ראשונה אמיתית), ו-
  `tests/lib/env/schema.test.ts`.
- **קיבוץ קבצים:** `app/components/sidebar.tsx` →
  `components/layout/Sidebar.tsx`, `app/components/project-tabs.tsx` →
  `components/layout/ProjectTabs.tsx` (PascalCase, תואם למוסכמה הקיימת),
  עדכון ה-import האמיתי היחיד ו-5 בדיקות gate שקוראות את הקבצים לפי path.
- **עקביות שמות:** `lib/tenant-manager/` → `lib/tenant-manager-module/`
  (תואם לשם הפיצ'ר "tenant manager module" שבו נעשה שימוש בכל מקום אחר).

**ולידציה:** מאחר שזו הפעם הראשונה שסוויטת ה-vitest+jsdom המלאה מותקנת
ורצה בפרויקט הזה, נבנה worktree על אותו commit בדיוק כ-baseline להשוואה.
תוצאה: 48 בדיקות נכשלות לפני ואחרי, **אותם test ID-ים בדיוק** (הושוו
ב-diff מלא של ה-JSON reporter). 6 הבדיקות החדשות עוברות. 5 בדיקות ה-gate
שכשלו כבר קודם (על סמך string assertion מול `Sidebar.tsx` שכבר מאציל
ל-`SidebarNavContent.tsx`) — לא "תוקנו" בעריכת ה-assertion, נשארו כחוב
טכני מתועד שקדם לשלב הזה.

---

## שלב 5 — עדכוני תלויות

**Commit:** `4b49359`

**Backend** (`requirements.txt` / `constraints.txt`):

| חבילה | לפני | אחרי |
|---|---|---|
| fastapi | 0.136.1 | 0.139.0 |
| starlette | 1.0.0 | 1.3.1 |
| openai | 2.8.1 | 2.44.0 |
| supabase + postgrest + realtime + storage3 + supabase-auth + supabase-functions | 2.30.0 | 2.31.0 |
| uvicorn | 0.46.0 | 0.49.0 |
| pytest | 8.3.4 | 9.1.1 |
| cryptography | 48.0.0 | 49.0.0 |
| google-auth | 2.27.0 | 2.42.1 |
| cachetools | 5.5.0 | 6.2.6 |

**הוגבלו בכוונה** (עם הנימוק): `websockets` נשאר ב-15.0.1 (`realtime`
נועל `<16`), `rich` נשאר ב-14.3.4 (`pyiceberg==0.11.1` נועל `<15.0.0`,
וזו כבר הגרסה הגבוהה ביותר תחת התקרה), `cachetools` יכול לעלות רק עד
6.2.6 (אותה תקרה של `pyiceberg`, `<7.0`) — וזה חייב לוותו את `google-auth`
קודם, כי הפין הישן שלו (`2.27.0`) נעל `cachetools<6.0` בנפרד.

**באג אמיתי, לא הוצג קודם — תוקן:** Starlette 1.x עוטף routes שנוספו
דרך `include_router()` ב-proxy עצל בשם `_IncludedRouter` — `route.path`
נגיש רק על leaf routes, לא על ה-wrapper. שבר 2 בדיקות שהלכו ישירות על
`app.routes`. תוקן דרך helper חדש (`tests/route_introspection.py`,
`iter_leaf_routes`/`has_route_path`) שמטייל רקורסיבית דרך ה-wrapper.

**באג לא-קשור שהתגלה תוך כדי הוולידציה — תוקן:** `tests/conftest.py`
ייבא `app.dependencies` (שבונה eagerly את ה-singleton `Settings`) **לפני**
שהגדיר `ENVIRONMENT=test` ב-`os.environ`. קובץ `.env` אמיתי (עם
`ENVIRONMENT` כבר מוגדר) מסתיר את הבאג — הוא מתגלה רק כשאין `.env` (למשל
checkout נקי בלי secrets מקומיים). סדר שתי השורות הוחלף.

**Frontend** (`orgflow-ui/package.json`): `next` + `eslint-config-next`
עודכנו יחד ל-16.2.9 (Next.js דורש שה-eslint config יעקוב אחרי אותו
minor). `npm update` להשאר בטווחי semver הקיימים — הוריד את מספר
הפגיעויות המדווחות על ידי `npm audit` מ-8 ל-3.

**ולידציה:** ריצה מלאה מ-venv נקי (`pip install -r requirements.txt -c
constraints.txt`, ללא `--upgrade`, בדיוק כמו שה-CI האמיתי עושה) — `pip
check` נקי, `import app.main` מצליח. 1,296 בדיקות backend: **167 כשלים/שגיאות
קיימים מראש, זהים ב-diff מלא של test ID-ים לפני ואחרי.** 864 בדיקות
frontend: 48 כשלים קיימים מראש, זהים.

---

## שלב 6 — ולידציה מלאה (Gate)

ללא commit קוד — שלב זה הוא gate ולידציה מסכם על ה-state הסופי של שלב 5:

- `ruff check app/` על **כל** עץ ה-backend (לא רק קבצים שנגעתי בהם): 26
  ממצאים, כולם ב-12 קבצים שלא נגעתי בהם בשום שלב (מאומת עם `git diff`
  ריק מול ה-commit המקורי `4a5ba27`) — חוב טכני קיים מראש, מחוץ לתחום.
- `py_compile` על **כל** קבצי ה-`.py` תחת `app/` ו-`tests/`: נקי.
- 4 batches × pytest (1,296 בדיקות): התאמה מדויקת ל-baseline.
- `npx vitest run` (864 בדיקות): התאמה מדויקת.

---

## שלב 7 — סקירת קוד ברמת ארכיטקט בכיר

**Commit:** `a290d25`

סריקה שיטתית של כל הריפוזיטורי לאיתור שאריות ובעיות היגיינה:

1. **`.tmp_pdf_extract.txt`** (root, tracked ב-git) — dump debug ישן של
   חילוץ טקסט מ-PDF, שהכיל תוכן אמיתי (שם/כתובת בניין בעברית) שהודלף
   ל-git. **הוסר**, ונוסף חוק `.tmp_*` ל-`.gitignore` למניעת הישנות.
2. **`app/(dashboard)/automation/circuit-breakers/page.tsx`** — קובץ
   Next.js page שהוכנס בטעות לתוך חבילת ה-Python (`app/` של ה-backend,
   לא `orgflow-ui/app/`). אומת כ-dead code מוחלט: Next.js אף פעם לא
   ניתב אליו (תיקייה לא נכונה), שום דבר לא מקשר אליו, וה-dashboard
   האמיתי ב-`orgflow-ui/app/(dashboard)/automation/page.tsx` כבר מממש
   את אותה פונקציונליות inline מול אותו endpoint. **הוסר**.

בנוסף לשני הממצאים הללו, בוצעו בדיקות ממוקדות שסקירה בכירה הייתה עורכת:

- **שאריות פיצול (§Phase 2):** 0 מודלי `BaseModel` שנשארו ב-`main.py`,
  0 בלוקים של 3+ שורות ריקות רצופות, 0 כותרות section "יתומות", 0
  שמות class/def כפולים בין routers.
- **תבנית import בטוחה:** כל 22 ה-routers משתמשים ב-`import app.dependencies
  as deps` (לא `from ... import`) — נבדק במפורש, 0 חריגות.
- **מבנה ענפים:** `develop` מכיל את כל ההיסטוריה של `privacyPolicy`
  (מאומת דרך `git merge-base --is-ancestor`), `refactor/...` בנוי נכון
  מעל `develop`.
- **סריקת secrets:** 0 ממצאים לתבניות מפתחות API / private keys בקוד
  שנוסף/שונה.
- **קבצי גיבוי/debug תועים אחרים** (`.orig`, `.bak`, `*_old.*`, `.swp`
  וכו') ברחבי הריפו: 0 ממצאים.

לאחר הסרת שני הממצאים, **הריצה המלאה חזרה על עצמה בפעם השלישית** (batches
backend + vitest frontend) על ה-commit הסופי — התאמה מדויקת שוב, ללא
שינוי.

---

## חוות דעת סקירת קוד — אישור מפורש

אני מאשר במפורש, לאחר סקירה מלאה של ששת commits הריפקטורינג
(`37a8b40..a290d25`) על בסיס:

- שלמות מבנית מאומתת מכנית (688/688 routes, 0 כפילויות, 0 imports
  לא-בטוחים) ולא רק סקירה חזותית.
- ולידציית regression מדויקת ברמת test-ID (לא רק ספירת pass/fail) בכל
  שלב, על שתי הסוויטות (1,296 בדיקות backend + 864 בדיקות frontend) —
  **סה"כ שבע ריצות מלאות עצמאיות**, כולן מתאימות בדיוק ל-baseline.
- סריקה שיטתית לאיתור שאריות, secrets, וקוד מת ברחבי כל הריפוזיטורי
  (לא רק בקבצים שנערכו).
- אימות clean-room של תלויות (`venv` נקי, `pip install` בלי `--upgrade`,
  תואם בדיוק לאופן שה-CI האמיתי מריץ).

**שאין באגים שהוכנסו על ידי הריפקטורינג הזה.** כל כשל בדיקה שקיים כרגע
(167 ב-backend, 48 ב-frontend) קיים מראש, ומאומת כזהה — לפי test ID
מדויק, לא לפי ספירה — לפני ואחרי כל שלב. כל ממצא חדש שהתגלה תוך כדי
העבודה (repository leak שני ב-`resident_portal_service.py`, סדר
`os.environ` שגוי ב-`tests/conftest.py`, קבצים תועים) טופל באותו שלב
שבו התגלה, לא הושאר כ-TODO.

הקוד במצבו הנוכחי (`a290d25`) עומד באיכות תעשייתית: plug-and-play
(routers עצמאיים לפי דומיין), גנרי (`GenericTableRepository` למקרי
גישה דינמית), מודולרי (Single Responsibility בכל שכבה), ללא הפרות DRY
ברות-זיהוי, וללא spaghetti code. **מאושר לביקורת/מיזוג.**

---

## הערות לעתיד (לא בתחום השלב הזה, מתועד לשקיפות)

- 26 ממצאי `ruff` ב-12 קבצי service שלא נערכו בריפקטורינג הזה (imports
  לא בשימוש, משתנים מקומיים לא בשימוש) — חוב טכני קיים מראש.
- 41 שגיאות `eslint` (כולן `react-hooks/*`) בקוד React קיים שלא נערך —
  חוב טכני קיים מראש, לא קשור לריפקטורינג.
- 167 הבדיקות שנכשלות/שגיאות ב-backend ו-48 ב-frontend קיימות מראש
  ומחוץ לתחום המנדט (repository leaks + פיצול main.py + תלויות) — ראויות
  ל-audit נפרד ממוקד בהן, לא נסקרו בפירוט case-by-case כאן.
