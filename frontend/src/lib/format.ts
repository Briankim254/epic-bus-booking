// All times are shown in Africa/Lagos regardless of the browser's zone (assumption A3).
const LAGOS = "Africa/Lagos"

const lagosDateTime = new Intl.DateTimeFormat("en-GB", {
  timeZone: LAGOS,
  weekday: "short",
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
})

const lagosTime = new Intl.DateTimeFormat("en-GB", {
  timeZone: LAGOS,
  hour: "2-digit",
  minute: "2-digit",
})

const lagosLongDate = new Intl.DateTimeFormat("en-GB", {
  timeZone: LAGOS,
  weekday: "long",
  day: "numeric",
  month: "long",
})

// en-CA formats dates as YYYY-MM-DD, the API's date format.
const lagosIsoDate = new Intl.DateTimeFormat("en-CA", {
  timeZone: LAGOS,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
})

const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
})

export function formatLagosTime(isoUtc: string): string {
  return lagosDateTime.format(new Date(isoUtc))
}

export function formatLagosClock(isoUtc: string): string {
  return lagosTime.format(new Date(isoUtc))
}

/** "Thursday 19 November" for a YYYY-MM-DD calendar day. */
export function formatLagosDate(day: string): string {
  // Noon UTC is the same calendar day in Lagos (UTC+1).
  return lagosLongDate.format(new Date(`${day}T12:00:00Z`))
}

/** Today's date in Lagos as YYYY-MM-DD. */
export function lagosToday(now: Date = new Date()): string {
  return lagosIsoDate.format(now)
}

export function formatUsd(cents: number): string {
  return usd.format(cents / 100)
}
