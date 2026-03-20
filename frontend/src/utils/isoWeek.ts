/** ISO week label `YYYY-WW` to match backend `bounds_for_iso_week_string`. */

export function isoWeekLabel(d: Date): string {
  const t = new Date(d.valueOf())
  t.setHours(0, 0, 0, 0)
  t.setDate(t.getDate() + 3 - ((t.getDay() + 6) % 7))
  const isoYear = t.getFullYear()
  const week1 = new Date(isoYear, 0, 4)
  const week =
    1 +
    Math.round(
      ((t.getTime() - week1.getTime()) / 86_400_000 - 3 + ((week1.getDay() + 6) % 7)) / 7,
    )
  return `${isoYear}-${String(week).padStart(2, '0')}`
}

const LABEL_RE = /^(\d{4})-(\d{2})$/

function addDays(d: Date, n: number): Date {
  const x = new Date(d.valueOf())
  x.setDate(x.getDate() + n)
  return x
}

/** Monday (local midnight) of the ISO week described by `YYYY-WW`. */
export function mondayOfIsoWeekLabel(label: string): Date {
  const m = LABEL_RE.exec(label.trim())
  if (!m) throw new Error('week must be YYYY-WW')
  const year = Number(m[1])
  const week = Number(m[2])
  const jan4 = new Date(year, 0, 4)
  const dayOfWeek = jan4.getDay() || 7
  const week1Monday = new Date(jan4)
  week1Monday.setDate(jan4.getDate() - dayOfWeek + 1)
  const monday = addDays(week1Monday, (week - 1) * 7)
  monday.setHours(0, 0, 0, 0)
  return monday
}

export function formatLocalDate(d: Date): string {
  const y = d.getFullYear()
  const mo = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${mo}-${day}`
}

/** Move ISO week label by `deltaWeeks` (negative = previous). */
export function shiftIsoWeek(label: string, deltaWeeks: number): string {
  const mon = mondayOfIsoWeekLabel(label)
  const next = addDays(mon, deltaWeeks * 7)
  return isoWeekLabel(next)
}
