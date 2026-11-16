export interface PhaseConfig {
  id: string
  name: string
  start_day: number
  end_day: number
}

export interface CropConfig {
  cycle_days: number
  phases: PhaseConfig[]
  check_windows: PhaseConfig[]
  progressColors: string[]
}

export const CROP_CONFIGS: Record<number, CropConfig> = {
  1: {
    cycle_days: 120,
    phases: [
      { id: 'germinacao', name: 'Germinação', start_day: 0, end_day: 14 },
      { id: 'floracao', name: 'Floração', start_day: 15, end_day: 64 },
      { id: 'enchimento', name: 'Enchimento do grão', start_day: 65, end_day: 99 },
      { id: 'maturacao', name: 'Maturação e colheita', start_day: 100, end_day: 119 },
    ],
    check_windows: [
      { id: 'flowering', name: 'Florescimento', start_day: 15, end_day: 64 },
      { id: 'pollination', name: 'Polinização', start_day: 40, end_day: 55 },
    ],
    progressColors: ['#22c55e', '#f59e0b', '#22c55e', '#f59e0b'],
  },
  2: {
    cycle_days: 90,
    phases: [
      { id: 'germinacao', name: 'Germinação', start_day: 0, end_day: 14 },
      { id: 'floracao', name: 'Floração', start_day: 15, end_day: 44 },
      { id: 'enchimento', name: 'Enchimento do grão', start_day: 45, end_day: 74 },
      { id: 'maturacao', name: 'Maturação e colheita', start_day: 75, end_day: 89 },
    ],
    check_windows: [
      { id: 'flowering', name: 'Florescimento', start_day: 15, end_day: 44 },
    ],
    progressColors: ['#22c55e', '#f59e0b', '#22c55e', '#f59e0b'],
  },
  3: {
    cycle_days: 110,
    phases: [
      { id: 'germinacao', name: 'Germinação', start_day: 0, end_day: 14 },
      { id: 'floracao', name: 'Floração', start_day: 15, end_day: 64 },
      { id: 'enchimento', name: 'Enchimento do grão', start_day: 65, end_day: 94 },
      { id: 'maturacao', name: 'Maturação e colheita', start_day: 95, end_day: 109 },
    ],
    check_windows: [
      { id: 'flowering', name: 'Florescimento', start_day: 15, end_day: 64 },
    ],
    progressColors: ['#22c55e', '#f59e0b', '#22c55e', '#f59e0b'],
  },
}
