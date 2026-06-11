import { CAPACITOR_LAST_ROUTE_STORAGE_KEY } from "@/lib/capacitor/route-persistence";

/**
 * רץ לפני React - מחזיר לדוח אחרי מצלמה/קובץ שטענו מחדש את ה-WebView ל-/ .
 * ניווט יחיד בלבד (בלי רעידות).
 */
export const CAPACITOR_ROUTE_RESTORE_SCRIPT = `(function(){try{var k=${JSON.stringify(CAPACITOR_LAST_ROUTE_STORAGE_KEY)};var t=localStorage.getItem(k);if(!t||t==="/")return;var p=location.pathname.replace(/\\/index\\.html$/i,"")||"/";if(p!=="/"&&p!=="")return;var loc=location.pathname+location.search;if(loc===t)return;if(t.indexOf("/field-reports")!==0)return;location.replace(t);}catch(e){}})();`;
