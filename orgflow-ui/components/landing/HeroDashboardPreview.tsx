import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  TrendingUp,
} from "lucide-react";

export default function HeroDashboardPreview() {
  return (
    <div
      className="
        relative
        mx-auto
        w-full
        max-w-xl
        lg:max-w-none
      "
      aria-hidden
    >
      <div
        className="
          of-landing-glow
          absolute
          -inset-8
          rounded-[2.5rem]
          opacity-60
        "
      />

      <div
        className="
          of-animate-float
          relative
          overflow-hidden
          rounded-[2rem]
          border
          border-zinc-200/80
          bg-white/90
          p-6
          shadow-2xl
          shadow-zinc-900/10
          backdrop-blur-sm
          dark:border-zinc-700/80
          dark:bg-zinc-900/90
          dark:shadow-black/40
        "
      >
        <div
          className="
            mb-6
            flex
            items-center
            justify-between
            gap-4
          "
        >
          <div>
            <p
              className="
                text-xs
                font-medium
                uppercase
                tracking-wider
                text-zinc-500
              "
            >
              פרויקט פעיל
            </p>
            <p className="mt-1 text-lg font-bold">
              האורנים 7 הוד השרון
            </p>
          </div>

          <div
            className="
              rounded-full
              bg-emerald-100
              px-3
              py-1
              text-xs
              font-semibold
              text-emerald-700
              dark:bg-emerald-900/40
              dark:text-emerald-300
            "
          >
            Online
          </div>
        </div>

        <div
          className="
            grid
            grid-cols-3
            gap-3
            mb-6
          "
        >
          {[
            { label: "דוחות שטח", value: "24", icon: BarChart3 },
            { label: "ליקויים פתוחים", value: "12", icon: AlertTriangle },
            { label: "% סגירה", value: "87%", icon: CheckCircle2 },
          ].map((stat) => (
            <div
              key={stat.label}
              className="
                rounded-2xl
                border
                border-zinc-100
                bg-zinc-50
                p-3
                dark:border-zinc-800
                dark:bg-zinc-800/50
              "
            >
              <stat.icon
                className="
                  mb-2
                  h-4
                  w-4
                  text-brand
                  dark:text-brand-light
                "
              />
              <p
                className="
                  text-xl
                  font-black
                  leading-none
                "
              >
                {stat.value}
              </p>
              <p
                className="
                  mt-1
                  text-[10px]
                  font-medium
                  text-zinc-500
                "
              >
                {stat.label}
              </p>
            </div>
          ))}
        </div>

        <div
          className="
            rounded-2xl
            border
            border-zinc-100
            bg-zinc-50
            p-4
            dark:border-zinc-800
            dark:bg-zinc-800/50
          "
        >
          <div
            className="
              mb-3
              flex
              items-center
              justify-between
            "
          >
            <p className="text-sm font-semibold">
              מגמת סגירת ליקויים
            </p>
            <TrendingUp
              className="
                h-4
                w-4
                text-emerald-600
                dark:text-emerald-400
              "
            />
          </div>

          <div
            className="
              flex
              h-20
              items-end
              gap-1.5
            "
          >
            {[40, 55, 45, 70, 62, 85, 78, 92].map((height, index) => (
              <div
                key={index}
                className="
                  flex-1
                  rounded-t-md
                  bg-gradient-to-t
                  from-brand
                  to-brand-gold
                  opacity-80
                "
                style={{ height: `${height}%` }}
              />
            ))}
          </div>
        </div>

        <div
          className="
            of-animate-float-delayed
            absolute
            -left-4
            top-1/3
            rounded-2xl
            border
            border-zinc-200/80
            bg-white
            px-4
            py-3
            shadow-lg
            dark:border-zinc-700
            dark:bg-zinc-800
          "
        >
          <p className="text-xs text-zinc-500">
            ליקוי חדש
          </p>
          <p className="text-sm font-bold text-amber-600 dark:text-amber-400">
            אינסטלציה
          </p>
        </div>

        <div
          className="
            of-animate-float
            absolute
            -right-2
            bottom-8
            rounded-2xl
            border
            border-zinc-200/80
            bg-white
            px-4
            py-3
            shadow-lg
            dark:border-zinc-700
            dark:bg-zinc-800
          "
        >
          <p className="text-xs text-zinc-500">
            נסגר בביקור
          </p>
          <p className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
            תמונת תיקון
          </p>
        </div>
      </div>
    </div>
  );
}
