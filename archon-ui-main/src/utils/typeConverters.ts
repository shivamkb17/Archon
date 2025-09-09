/**
 * Type conversion utilities for safely converting unknown values
 * with fallback support
 */

/**
 * Converts an unknown value to a boolean with fallback
 * @param v - The value to convert
 * @param fallback - The fallback value if conversion fails
 * @returns The boolean value or fallback
 */
export const toBool = (v: unknown, fallback: boolean): boolean => {
  if (typeof v === "boolean") return v;
  if (typeof v === "string") {
    const s = v.trim().toLowerCase();
    if (s === "true") return true;
    if (s === "false") return false;
  }
  return fallback;
};

/**
 * Converts an unknown value to an integer with fallback
 * @param v - The value to convert
 * @param fallback - The fallback value if conversion fails
 * @returns The integer value or fallback
 */
export const toInt = (v: unknown, fallback: number): number => {
  const n =
    typeof v === "number" ? Math.trunc(v) : Number.parseInt(String(v), 10);
  return Number.isFinite(n) ? n : fallback;
};

/**
 * Converts an unknown value to a float with fallback
 * @param v - The value to convert
 * @param fallback - The fallback value if conversion fails
 * @returns The float value or fallback
 */
export const toFloat = (v: unknown, fallback: number): number => {
  const n = typeof v === "number" ? v : Number.parseFloat(String(v));
  return Number.isFinite(n) ? n : fallback;
};
