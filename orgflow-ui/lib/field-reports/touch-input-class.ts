/** Shared classes for touch-friendly controls in field reports (3E.1). */
export const FR_TOUCH_INPUT =
  "of-input w-full min-h-12 text-base touch-manipulation lg:min-h-0 lg:text-sm";

export const FR_TOUCH_SELECT = `${FR_TOUCH_INPUT}`;

export const FR_TOUCH_TEXTAREA = `${FR_TOUCH_INPUT} min-h-32 lg:min-h-28`;

export const FR_TOUCH_NOTES = `${FR_TOUCH_INPUT} min-h-28 lg:min-h-24`;

export const FR_TOUCH_BUTTON =
  "min-h-12 touch-manipulation lg:min-h-0";

export const FR_TOUCH_LIST_BUTTON =
  "w-full min-h-12 touch-manipulation rounded-xl border px-4 py-3 text-right text-base transition-colors lg:min-h-0 lg:rounded-lg lg:px-3 lg:py-2 lg:text-sm";
