import { LINE_PHOTO_CAPTURE_CONTEXT_KEY } from "@/lib/capacitor/line-photo-capture-context";
import {
  CAPACITOR_LAST_ROUTE_STORAGE_KEY,
} from "@/lib/capacitor/route-persistence";

/**
 * רץ לפני React — מחזיר לדוח שטח אחרי reload של WebView (מצלמה native).
 */
export const CAPACITOR_ROUTE_RESTORE_SCRIPT = `(function(){try{var rk=${JSON.stringify(CAPACITOR_LAST_ROUTE_STORAGE_KEY)};var ck=${JSON.stringify(LINE_PHOTO_CAPTURE_CONTEXT_KEY)};var loc=window.location.pathname+window.location.search;var bootPath=window.location.pathname.replace(/\\/index\\.html$/i,"")||"/";if(bootPath!=="/"&&bootPath!=="")return;var target=localStorage.getItem(rk);if(!target){var raw=localStorage.getItem(ck);if(raw){try{target=JSON.parse(raw).returnPath;}catch(e){}}}if(!target||target==="/"||target.indexOf("/field-reports")!==0)return;if(loc===target)return;window.location.replace(target);}catch(e){}})();`;
