/**
 * Clima Raiz — Design System tokens (JS mirror of globals.css)
 *
 * Use for React Native StyleSheet, inline styles, Storybook
 * decorators, or any runtime that cannot read CSS variables.
 *
 * The source of truth is globals.css. Keep in sync when updating.
 */

// ── Primitive palette ────────────────────────────────────────────

export const palette = {
  // Brand Green — 8 steps: brandDark → green50
  brandDark: '#1b4132',
  green800:  '#166534',
  green700:  '#15803d',
  green600:  '#16a34a',
  green500:  '#22c55e',
  green300:  '#86efac',
  green100:  '#dcfce7',
  green50:   '#f0fdf4',

  // Neutral — 7 steps: gray900 → white
  gray900:   '#111827',
  gray700:   '#374151',
  gray500:   '#6b7280',
  gray400:   '#9ca3af',
  gray300:   '#d1d5db',
  gray100:   '#f3f4f6',
  white:     '#ffffff',

  // Amber — 4 steps: atenção e alertas
  amber800:  '#92400e',
  amber500:  '#f59e0b',
  amber200:  '#fde68a',
  amber50:   '#fffbeb',

  // Blue — 3 steps: precipitação e dados hídricos
  blue700:   '#1d4ed8',
  blue400:   '#60a5fa',
  blue100:   '#dbeafe',

  // Red — 2 steps: erros e severidade alta
  red700:    '#b91c1c',
  red100:    '#fee2e2',

  // Overlays
  overlayWhite10: 'rgba(255,255,255,0.10)',
  overlayWhite85: 'rgba(255,255,255,0.85)',
  overlayBlack30: 'rgba(0,0,0,0.30)',
} as const;

// ── Semantic tokens ──────────────────────────────────────────────

export const semanticLight = {
  background:       palette.green50,
  surface:          palette.white,
  surfaceElevated:  palette.gray100,
  border:           palette.green100,

  textPrimary:      palette.gray900,
  textSecondary:    palette.gray700,
  textMuted:        palette.gray500,

  brand:            palette.green600,
  brandHover:       palette.green700,
  brandSubtle:      palette.green100,

  statusOk:         palette.green700,
  statusWarn:       palette.amber800,
  statusDanger:     palette.red700,
  statusInfo:       palette.blue700,

  statusOkBg:       palette.green100,
  statusWarnBg:     palette.amber50,
  statusDangerBg:   palette.red100,
  statusInfoBg:     palette.blue100,
} as const;

export const semanticDark = {
  background:       palette.gray900,
  surface:          '#1a2e22',
  surfaceElevated:  palette.brandDark,
  border:           'rgba(134,239,172,0.12)',

  textPrimary:      palette.white,
  textSecondary:    palette.gray400,
  textMuted:        palette.gray500,

  brand:            palette.green500,
  brandHover:       palette.green600,
  brandSubtle:      palette.brandDark,

  statusOk:         palette.green500,
  statusWarn:       palette.amber500,
  statusDanger:     palette.red700,
  statusInfo:       palette.blue400,

  statusOkBg:       palette.brandDark,
  statusWarnBg:     palette.amber800,
  statusDangerBg:   'rgba(185,28,28,0.15)',
  statusInfoBg:     'rgba(29,78,216,0.15)',
} as const;

// ── Typography ───────────────────────────────────────────────────

export const typography = {
  fontFamily: 'Inter',

  weights: {
    regular:  400,
    medium:   500,
    semibold: 600,
    bold:     700,
  },

  /**
   * 12 roles — micro(8) → display(28)
   * All sizes are in px. lineHeight is a unitless multiplier.
   * letterSpacing (when present) is in px — only text-label has it.
   */
  roles: {
    micro:       { fontSize:  8, fontWeight: 400, lineHeight: 1.4 },
    label:       { fontSize: 10, fontWeight: 500, lineHeight: 1.4, letterSpacing: 0.8 },
    caption:     { fontSize: 11, fontWeight: 400, lineHeight: 1.5 },
    xs:          { fontSize: 12, fontWeight: 400, lineHeight: 1.5 },
    sm:          { fontSize: 13, fontWeight: 400, lineHeight: 1.5 },
    body:        { fontSize: 14, fontWeight: 400, lineHeight: 1.6 },
    bodyStrong:  { fontSize: 14, fontWeight: 600, lineHeight: 1.6 },
    base:        { fontSize: 16, fontWeight: 400, lineHeight: 1.6 },
    baseStrong:  { fontSize: 16, fontWeight: 600, lineHeight: 1.6 },
    lg:          { fontSize: 18, fontWeight: 600, lineHeight: 1.4 },
    heading:     { fontSize: 22, fontWeight: 700, lineHeight: 1.3 },
    display:     { fontSize: 28, fontWeight: 700, lineHeight: 1.2 },
  },
} as const;

// ── Convenience helpers ──────────────────────────────────────────

/** Returns the right semantic token set for a given theme. */
export function getSemanticTokens(theme: 'light' | 'dark') {
  return theme === 'dark' ? semanticDark : semanticLight;
}

// ── Shared types ─────────────────────────────────────────────────

export type Palette        = typeof palette;
export type SemanticTokens = typeof semanticLight;
export type TypographyRole = keyof typeof typography.roles;
export type Theme          = 'light' | 'dark';
