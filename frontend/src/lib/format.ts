// All times are shown in Africa/Lagos regardless of the browser's zone (assumption A3).
const lagosDateTime = new Intl.DateTimeFormat("en-GB", {
  timeZone: "Africa/Lagos",
  weekday: "short",
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
})

const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
})

export function formatLagosTime(isoUtc: string): string {
  return lagosDateTime.format(new Date(isoUtc))
}

export function formatUsd(cents: number): string {
  return usd.format(cents / 100)
}
