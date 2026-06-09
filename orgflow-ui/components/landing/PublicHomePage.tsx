import Link from "next/link";
import {
  Bot,
  Building2,
  FileSearch,
  Layers,
  Shield,
  Sparkles,
  Zap,
} from "lucide-react";

import HeroDashboardPreview from "@/components/landing/HeroDashboardPreview";
import LandingSystemCtaLink from "@/components/landing/LandingSystemCtaLink";
import PublicNavBar from "@/components/landing/PublicNavBar";
import BrandLogo from "@/components/ui/BrandLogo";

const FEATURES = [
  {
    icon: Bot,
    title: "ביקורות AI אוטומטיות",
    description:
      "ניתוח דוחות הנדסיים, זיהוי חריגות וסיכונים — בזמן אמת ובדיוק גבוה.",
    accent: "from-brand to-brand-light",
  },
  {
    icon: FileSearch,
    title: "ניתוח חריגות חכם",
    description:
      "מיפוי, סיווג ומעקב אחר חריגות בפרויקט — עם המלצות פעולה מיידיות.",
    accent: "from-brand-gold to-amber-500",
  },
  {
    icon: Shield,
    title: "פיקוח הנדסי רציף",
    description:
      "שקיפות מלאה על מצב הפרויקט, נקודות סיכון וסטטוס ביצוע לכל שלב.",
    accent: "from-teal-500 to-brand-light",
  },
  {
    icon: Building2,
    title: "התחדשות עירונית",
    description:
      "מותאם לפרויקטי בנייה, פינוי-בינוי ותמ\"א — עם תהליכי עבודה מוכרים.",
    accent: "from-brand to-brand-gold",
  },
  {
    icon: Zap,
    title: "אוטומציה תפעולית",
    description:
      "הפקת פעולות, התראות ודוחות — ללא עבודה ידנית חוזרת.",
    accent: "from-brand-gold to-brand-gold-dark",
  },
  {
    icon: Layers,
    title: "ניהול רב-פרויקטים",
    description:
      "תצוגת פורטפolio מרכזית לכל החברות והפרויקטים — במקום אחד.",
    accent: "from-brand-dark to-brand",
  },
] as const;

const WORKFLOW_STEPS = [
  {
    step: "01",
    title: "הקשר פרויקט וקליטת חומר",
    description:
      "בוחרים ארגון ופרויקט, מעלים דוח הנדסי או מסמך תפעולי — "
      + "המערכת מקשרת את הקלט לפרויקט הנכון ומפעילה עיבוד.",
  },
  {
    step: "02",
    title: "ממצאים וביקורת AI",
    description:
      "ה-AI מחלץ ממצאים, בונה פרשנות עם השפעה עסקית, "
      + "רמת סיכון ופעולה מומלצת — הביקורות ממתינות לאישור "
      + "בלוח ביקורות AI.",
  },
  {
    step: "03",
    title: "אישור ויצירת פעולות",
    description:
      "מנהל מאשר או דוחה את הביקורת; באישור נוצרות "
      + "פעולות תפעוליות (מעקב, ביקורת באתר, הסלמה ועוד) "
      + "המקושרות לפרשנות.",
  },
  {
    step: "04",
    title: "מעקב, הסלמה וסגירה",
    description:
      "עוקבים אחר פעולות פתוחות ונקודות סיכון ב-workspace "
      + "הפרויקט, ברמת הארגון ובתיק הפרויקטים — כולל הסלמה "
      + "אוטומטית בפיגור יעד, עד סגירה מלאה.",
  },
] as const;

const WORKFLOW_PILLARS = [
  { value: "ביקורות AI", label: "פרשנות, אישור ודחייה מנהלתית" },
  { value: "פעולות תפעוליות", label: "מעקב סטטוס, השלמה וחסימה" },
  { value: "נקודות סיכון", label: "הסלמה ידנית ואוטומטית לפי SLA" },
  { value: "אוטומציה", label: "תורים, ניטור בריאות ו-Dead Letters" },
] as const;

export default function PublicHomePage() {
  return (
    <div className="of-landing-page min-h-screen">
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
                border-brand/20/60
                bg-brand-muted/80
                px-4
                py-2
                text-sm
                font-medium
                text-brand
                backdrop-blur-sm
                dark:border-brand/40
                dark:bg-brand/40
                dark:text-brand-light
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
              פלטפורמת AI לתפעול פיקוח הנדסי — מדוחות וחריגות
              ועד פעולות, מעקב והסלמות
              בפרויקטי בנייה והתחדשות עירונית.
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
              <LandingSystemCtaLink variant="hero" />

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
          {WORKFLOW_PILLARS.map((pillar) => (
            <div
              key={pillar.label}
              className="text-center md:text-start"
            >
              <p
                className="
                  text-lg
                  font-black
                  tracking-tight
                  text-brand
                  dark:text-brand-light
                  md:text-xl
                "
              >
                {pillar.value}
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
                {pillar.label}
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
          pb-20
          pt-24
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
                text-brand
                dark:text-brand-light
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
          pb-20
          pt-8
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
            p-8
            md:p-12
            dark:border-zinc-800
            dark:from-zinc-900/80
            dark:to-zinc-950
          "
        >
          <div
            className="
              mb-10
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
                text-brand-gold
                dark:text-brand-gold
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
              מקליטת דוח ועד סגירת פעולה
            </h2>
            <p
              className="
                mt-4
                text-lg
                leading-relaxed
                text-zinc-600
                dark:text-zinc-400
              "
            >
              אותו מסלול שעוברים בו במערכת: פרויקט → ביקורת AI →
              פעולות תפעוליות → מעקב והסלמה.
            </p>
          </div>

          <div
            className="
              grid
              gap-5
              md:grid-cols-2
              xl:grid-cols-4
            "
          >
            {WORKFLOW_STEPS.map((item) => (
              <article
                key={item.step}
                className="
                  rounded-[1.75rem]
                  border
                  border-zinc-200/80
                  bg-white
                  p-8
                  shadow-sm
                  transition-all
                  hover:-translate-y-0.5
                  hover:shadow-lg
                  hover:shadow-zinc-900/5
                  dark:border-zinc-800
                  dark:bg-zinc-950/70
                  dark:hover:shadow-black/20
                "
              >
                <div
                  className="
                    mb-6
                    inline-flex
                    h-12
                    w-12
                    items-center
                    justify-center
                    rounded-2xl
                    bg-gradient-to-br
                    from-brand-gold
                    to-brand-gold-dark
                    text-sm
                    font-black
                    text-white
                    shadow-lg
                    shadow-brand-gold/20
                  "
                >
                  {item.step}
                </div>

                <h3 className="text-xl font-bold">
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
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Platform highlight */}
      <section
        id="platform"
        className="
          px-4
          pb-24
          pt-8
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
              ElayoAI —
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
              from-brand
              to-brand-gold-dark
              p-10
              text-white
              shadow-2xl
              shadow-brand/20
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

            <p className="relative text-sm font-medium text-white/80">
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
                text-white/80
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
            relative
            overflow-hidden
            rounded-[2.5rem]
            border
            border-zinc-200/80
            bg-gradient-to-br
            from-brand
            to-brand-gold-dark
            px-8
            py-16
            text-center
            shadow-2xl
            shadow-brand/20
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

          <h2
            className="
              relative
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
              relative
              mx-auto
              mt-4
              max-w-lg
              text-lg
              text-white/80
            "
          >
            התחברו למערכת וקבלו גישה מיידית
            לסביבת העבודה התפעולית.
          </p>

          <LandingSystemCtaLink
            variant="footer"
            className="relative"
          />
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
              © {new Date().getFullYear()} ElayoAI
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
