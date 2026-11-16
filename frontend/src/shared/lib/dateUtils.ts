const SHORT_MONTHS: Record<number, string> = {
  1: 'jan', 2: 'fev', 3: 'mar', 4: 'abr', 5: 'mai', 6: 'jun',
  7: 'jul', 8: 'ago', 9: 'set', 10: 'out', 11: 'nov', 12: 'dez',
}

const LONG_MONTHS: Record<number, string> = {
  1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho',
  7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
}

function parseParts(isoDate: string): { day: number; month: number; year: number } {
  const [y, m, d] = isoDate.split('-').map(Number)
  return { day: d, month: m, year: y }
}

export function formatShortDate(isoDate: string): string {
  const { day, month } = parseParts(isoDate)
  return `${day} ${SHORT_MONTHS[month]}`
}

export function formatMonthYear(isoDate: string): string {
  const { month, year } = parseParts(isoDate)
  return `${LONG_MONTHS[month]} ${year}`
}

export function formatWindowRange(startDate: string, endDate: string): string {
  const s = parseParts(startDate)
  const e = parseParts(endDate)
  if (s.month === e.month) {
    return `${s.day}–${e.day} ${LONG_MONTHS[s.month]} ${s.year}`
  }
  return `${s.day} ${SHORT_MONTHS[s.month]} – ${e.day} ${SHORT_MONTHS[e.month]} ${s.year}`
}

export function getPlantingYear(): number {
  const now = new Date()
  return now.getMonth() > 4 ? now.getFullYear() + 1 : now.getFullYear()
}
