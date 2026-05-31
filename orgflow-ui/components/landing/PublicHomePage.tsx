import Link from "next/link";
import {
  ArrowLeft,
  Bot,
  Building2,
  FileSearch,
  Layers,
  Shield,
  Sparkles,
  Zap,
} from "lucide-react";

import HeroDashboardPreview from "@/components/landing/HeroDashboardPreview";
import LandingHashScroll from "@/components/landing/LandingHashScroll";
import PublicNavBar from "@/components/landing/PublicNavBar";
import BrandLogo from "@/components/ui/BrandLogo";

const FEATURES = [
  {
    icon: Bot,
    title: "ביקורות AI אוטומטיות",
    description:
      "ניתוח דוחות הנדסיים, זיהוי חריגות וסיכונים — בזמן אמת ובדיוק גבוה.",
    accent: "from-blue-500 to-cyan-500",
  },
  {
    icon: FileSearch,
    title: "ניתוח חריגות חכם",
    description:
      "מיפוי, סיווג ומעקב אחר חריגות בפרויקט — עם המלצות פעולה מיידיות.",
    accent: "from-violet-500 to-purple-500",
  },
  {
    icon: Shield,
    title: "פיקוח הנדסי רציף",
    description:
      "שקיפות מלאה על מצב הפרויקט, נקודות סיכון וסטטוס ביצוע לכל שלב.",
    accent: "from-emerald-500 to-teal-500",
  },
  {
    icon: Building2,
    title: "התחדשות עירונית",
    description:
      "מותאם לפרויקטי בנייה, פינוי-בינוי ותמ\"א — עם תהליכי עבודה מוכרים.",
    accent: "from-amber-500 to-orange-500",
  },
  {
    icon: Zap,
    title: "אוטומציה תפעולית",
    description:
      "הפקת פעולות, התראות ודוחות — ללא עבודה ידנית חוזרת.",
    accent: "from-rose-500 to-pink-500",
  },
  {
    icon: Layers,
    title: "ניהול רב-פרויקטים",
    description:
      "תצוגת פורטפolio מרכזית לכל החברות והפרויקטים — במקום אחד.",
    accent: "from-indigo-500 to-blue-500",
  },
] as const;

const STEPS = [
  {
    step: "01",
    title: "העלאת דוחות",
    description:
      "מעלים דוחות הנדסיים, ביקורות ומסמכי תפעול — המערכת מעבדת אוטומטית.",
  },
  {
    step: "02",
    title: "ניתוח AI",
    description:
      "המנוע מזהה חריגות, סיכונים ונקודות תשומת לב — ומסווג לפי חומרה.",
  },
  {
    step: "03",
    title: "פעולה והמשך",
    description:
      "מקבלים המלצות, פעולות ומעקב — עד לסגירה מלאה של כל נושא.",
  },
] as const;

const STATS = [
  { value: "148+", label: "ביקורות AI" },
  { value: "24/7", label: "ניטור רציף" },
  { value: "94%", label: "שיעור סגירה" },
  { value: "∞", label: "פרויקטים במקביל" },
] as const;

export default function PublicHomePage() {
  return (
    <div className="of-landing-page min-h-screen">
      <LandingHashScroll />
      <PublicNavBar />

      {/* Hero */}
      <section
        className="
          relative
          overflow-hidden
          px-4
          pb-20
          pt-16
          md:px-8
          md:pb-28
          md:pt-24
        "
      >
        <div
          className="
            of-landing-orb
            of-landing-orb-1
          "
        />
        <div
          className="
            of-landing-orb
            of-landing-orb-2
          "
        />

        <div
          className="
            of-container
            relative
            grid
            items-center
            gap-12
            lg:grid-cols-2
            lg:gap-16
          "
        >
          <div className="of-animate-fade-up">
            <div
              className="
                mb-6
                inline-flex
                items-center
                gap-2
                rounded-full
                border
                border-blue-200/60
                bg-blue-50/80
                px-4
                py-2
                text-sm
                font-medium
                text-blue-700
                backdrop-blur-sm
                dark:border-blue-800/40
                dark:bg-blue-950/40
                dark:text-blue-300
              "
            >
              <Sparkles className="h-4 w-4" />
              מערכת תפעול הנדסי מבוססת AI
            </div>

            <h1
              className="
                text-4xl
                font-black
                leading-[1.1]
                tracking-tight
                sm:text-5xl
                md:text-6xl
                lg:text-7xl
              "
            >
              פיקוח הנדסי
              <span
                className="
                  of-landing-gradient-text
                  block
                "
              >
                ברמת Enterprise
              </span>
            </h1>

            <p
              className="
                mt-6
                max-w-xl
                text-lg
                leading-relaxed
                text-zinc-600
                dark:text-zinc-400
                md:text-xl
              "
            >
              פלטפורמת AI לניהול תפעולי, בקרת פרויקטים,
              ניתוח חריגות ונקודות סיכון
              בפרויקטי התחדשות עירונית ובנייה.
            </p>

            <div
              className="
                mt-10
                flex
                flex-wrap
                items-center
                gap-4
              "
            >
              <Link
                href="/auth/login"
                className="
                  of-focus-ring
                  inline-flex
                  items-center
                  gap-2
                  rounded-2xl
                  bg-gradient-to-l
                  from-blue-600
                  to-violet-600
                  px-8
                  py-4
                  text-base
                  font-semibold
                  text-white
                  shadow-lg
                  shadow-blue-600/25
                  transition-all
                  hover:shadow-xl
                  hover:shadow-blue-600/30
                  hover:brightness-110
                "
              >
                התחברות למערכת
                <ArrowLeft className="h-5 w-5" />
              </Link>

              <a
                href="#features"
                className="
                  of-focus-ring
                  inline-flex
                  items-center
                  rounded-2xl
                  border
                  border-zinc-200
                  bg-white/80
                  px-8
                  py-4
                  text-base
                  font-semibold
                  text-zinc-900
                  backdrop-blur-sm
                  transition-colors
                  hover:bg-zinc-50
                  dark:border-zinc-700
                  dark:bg-zinc-900/80
                  dark:text-zinc-100
                  dark:hover:bg-zinc-800
                "
              >
                גלה את היכולות
              </a>
            </div>
          </div>

          <div className="of-animate-fade-up of-animate-delay-200">
            <HeroDashboardPreview />
          </div>
        </div>
      </section>

      {/* Stats strip */}
      <section
        className="
          border-y
          border-zinc-200/60
          bg-white/50
          backdrop-blur-sm
          dark:border-zinc-800/60
          dark:bg-zinc-900/30
        "
      >
        <div
          className="
            of-container
            grid
            grid-cols-2
            gap-8
            py-12
            md:grid-cols-4
          "
        >
          {STATS.map((stat) => (
            <div
              key={stat.label}
              className="text-center md:text-start"
            >
              <p
                className="
                  text-3xl
                  font-black
                  tracking-tight
                  md:text-4xl
                "
              >
                {stat.value}
              </p>
              <p
                className="
                  mt-1
                  text-sm
                  font-medium
                  text-zinc-500
                  dark:text-zinc-400
                "
              >
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section
        id="features"
        className="
          px-4
          py-24
          md:px-8
        "
      >
        <div className="of-container">
          <div
            className="
              mx-auto
              mb-16
              max-w-2xl
              text-center
            "
          >
            <p
              className="
                mb-3
                text-sm
                font-semibold
                uppercase
                tracking-wider
                text-blue-600
                dark:text-blue-400
              "
            >
              יכולות המערכת
            </p>
            <h2
              className="
                text-3xl
                font-black
                tracking-tight
                md:text-5xl
              "
            >
              הכל במקום אחד
            </h2>
            <p
              className="
                mt-4
                text-lg
                text-zinc-600
                dark:text-zinc-400
              "
            >
              מנוע AI תפעולי שמחבר בין דוחות, חריגות,
              פעולות ומעקב — לפרויקטים מורכבים.
            </p>
          </div>

          <div
            className="
              grid
              gap-6
              md:grid-cols-2
              lg:grid-cols-3
            "
          >
            {FEATURES.map((feature) => (
              <article
                key={feature.title}
                className="
                  group
                  rounded-[1.75rem]
                  border
                  border-zinc-200/80
                  bg-white
                  p-8
                  transition-all
                  hover:-translate-y-1
                  hover:border-zinc-300
                  hover:shadow-xl
                  hover:shadow-zinc-900/5
                  dark:border-zinc-800
                  dark:bg-zinc-900/60
                  dark:hover:border-zinc-700
                  dark:hover:shadow-black/20
                "
              >
                <div
                  className={`
                    mb-5
                    inline-flex
                    rounded-2xl
                    bg-gradient-to-br
                    ${feature.accent}
                    p-3
                    text-white
                    shadow-lg
                    transition-transform
                    group-hover:scale-110
                  `}
                >
                  <feature.icon className="h-6 w-6" />
                </div>

                <h3 className="text-xl font-bold">
                  {feature.title}
                </h3>

                <p
                  className="
                    mt-3
                    leading-relaxed
                    text-zinc-600
                    dark:text-zinc-400
                  "
                >
                  {feature.description}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section
        id="how-it-works"
        className="
          px-4
          py-24
          md:px-8
        "
      >
        <div
          className="
            of-container
            rounded-[2.5rem]
            border
            border-zinc-200/80
            bg-gradient-to-br
            from-zinc-50
            to-zinc-100/80
            p-10
            md:p-16
            dark:border-zinc-800
            dark:from-zinc-900/80
            dark:to-zinc-950
          "
        >
          <div
            className="
              mb-14
              max-w-xl
            "
          >
            <p
              className="
                mb-3
                text-sm
                font-semibold
                uppercase
                tracking-wider
                text-violet-600
                dark:text-violet-400
              "
            >
              תהליך העבודה
            </p>
            <h2
              className="
                text-3xl
                font-black
                tracking-tight
                md:text-4xl
              "
            >
              שלושה שלבים. תוצאות מיידיות.
            </h2>
          </div>

          <div
            className="
              grid
              gap-8
              md:grid-cols-3
            "
          >
            {STEPS.map((item) => (
              <div
                key={item.step}
                className="relative"
              >
                <span
                  className="
                    of-landing-gradient-text
                    text-5xl
                    font-black
                    opacity-30
                  "
                >
                  {item.step}
                </span>

                <h3
                  className="
                    -mt-4
                    text-xl
                    font-bold
                  "
                >
                  {item.title}
                </h3>

                <p
                  className="
                    mt-3
                    leading-relaxed
                    text-zinc-600
                    dark:text-zinc-400
                  "
                >
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Platform highlight */}
      <section
        id="platform"
        className="
          px-4
          py-24
          md:px-8
        "
      >
        <div
          className="
            of-container
            grid
            items-center
            gap-12
            lg:grid-cols-2
          "
        >
          <div>
            <p
              className="
                mb-3
                text-sm
                font-semibold
                uppercase
                tracking-wider
                text-emerald-600
                dark:text-emerald-400
              "
            >
              הפלטפורמה
            </p>
            <h2
              className="
                text-3xl
                font-black
                tracking-tight
                md:text-4xl
              "
            >
              Supervisor AI —
              מערכת ההפעלה
              לפרויקטים שלך
            </h2>
            <p
              className="
                mt-5
                text-lg
                leading-relaxed
                text-zinc-600
                dark:text-zinc-400
              "
            >
              ממשק אחיד לניהול ביקורות, חריגות,
              פעולות תפעוליות והתראות — עם ניטור
              בזמן אמת ודוחות מנהלים.
            </p>

            <ul
              className="
                mt-8
                space-y-4
              "
            >
              {[
                "דשבורד KPI לכל פרויקט",
                "מעקב חריגות ואскלציות",
                "התראות ועדכונים בזמן אמת",
                "אוטומציה ותורים חכמים",
              ].map((item) => (
                <li
                  key={item}
                  className="
                    flex
                    items-center
                    gap-3
                    text-zinc-700
                    dark:text-zinc-300
                  "
                >
                  <span
                    className="
                      flex
                      h-6
                      w-6
                      shrink-0
                      items-center
                      justify-center
                      rounded-full
                      bg-emerald-100
                      text-emerald-600
                      dark:bg-emerald-900/40
                      dark:text-emerald-400
                    "
                  >
                    ✓
                  </span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div
            className="
              relative
              overflow-hidden
              rounded-[2rem]
              border
              border-zinc-200/80
              bg-gradient-to-br
              from-blue-600
              to-violet-700
              p-10
              text-white
              shadow-2xl
              shadow-blue-600/20
              dark:border-zinc-700
            "
          >
            <div
              className="
                absolute
                -right-10
                -top-10
                h-40
                w-40
                rounded-full
                bg-white/10
                blur-2xl
              "
            />
            <div
              className="
                absolute
                -bottom-10
                -left-10
                h-32
                w-32
                rounded-full
                bg-white/10
                blur-2xl
              "
            />

            <p className="relative text-sm font-medium text-blue-100">
              Operational AI Engine
            </p>
            <p
              className="
                relative
                mt-2
                text-3xl
                font-black
              "
            >
              מוכן לעבודה
            </p>
            <p
              className="
                relative
                mt-4
                leading-relaxed
                text-blue-100
              "
            >
              המערכת פעילה, מאובטחת ומחוברת
              לכל שכבות התפעול — מהדוח ועד הפעולה.
            </p>

            <div
              className="
                relative
                mt-8
                flex
                items-center
                gap-3
              "
            >
              <span
                className="
                  relative
                  flex
                  h-3
                  w-3
                "
              >
                <span
                  className="
                    absolute
                    inline-flex
                    h-full
                    w-full
                    animate-ping
                    rounded-full
                    bg-emerald-400
                    opacity-75
                  "
                />
                <span
                  className="
                    relative
                    inline-flex
                    h-3
                    w-3
                    rounded-full
                    bg-emerald-400
                  "
                />
              </span>
              <span className="text-sm font-semibold">
                System Online
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section
        className="
          px-4
          pb-24
          md:px-8
        "
      >
        <div
          className="
            of-container
            overflow-hidden
            rounded-[2.5rem]
            border
            border-zinc-200/80
            bg-zinc-900
            px-8
            py-16
            text-center
            dark:border-zinc-800
            dark:bg-zinc-900/80
          "
        >
          <h2
            className="
              text-3xl
              font-black
              tracking-tight
              text-white
              md:text-4xl
            "
          >
            מוכנים לשלוט בפרויקט?
          </h2>
          <p
            className="
              mx-auto
              mt-4
              max-w-lg
              text-lg
              text-zinc-400
            "
          >
            התחברו למערכת וקבלו גישה מיידית
            לסביבת העבודה התפעולית.
          </p>

          <Link
            href="/auth/login"
            className="
              of-focus-ring
              mt-8
              inline-flex
              items-center
              gap-2
              rounded-2xl
              bg-white
              px-8
              py-4
              text-base
              font-semibold
              text-zinc-900
              transition-all
              hover:bg-zinc-100
            "
          >
            התחברות למערכת
            <ArrowLeft className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer
        className="
          border-t
          border-zinc-200/60
          px-4
          py-10
          dark:border-zinc-800/60
        "
      >
        <div
          className="
            of-container
            flex
            flex-col
            items-center
            justify-between
            gap-4
            md:flex-row
          "
        >
          <div className="flex items-center gap-3">
            <BrandLogo size="sm" showTagline={false} />
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              © {new Date().getFullYear()} Supervisor AI
            </p>
          </div>

          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            פלטפורמת AI לניהול תפעול הנדסי
          </p>
        </div>
      </footer>
    </div>
  );
}
