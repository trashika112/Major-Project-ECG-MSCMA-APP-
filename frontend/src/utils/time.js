/**
 * The backend stores and returns timestamps as naive UTC (no timezone marker
 * in the ISO string, e.g. "2026-07-16T06:05:00.123456" instead of
 * "...123456Z"). Passed straight into `new Date(...)`, browsers treat a
 * timezone-less ISO string as LOCAL time, not UTC — so the raw UTC clock
 * value gets displayed as if it already were local time, showing up ~5.5
 * hours behind real IST. These helpers force UTC interpretation before
 * conversion, so times shown in the UI actually match the viewer's clock.
 */

function asUtcDate(isoString) {
  if (!isoString) return null
  // If the string already has a timezone marker (Z or +hh:mm), leave it
  // alone; otherwise append 'Z' so JS parses it as UTC rather than local.
  const hasTz = /Z$|[+-]\d{2}:\d{2}$/.test(isoString)
  return new Date(hasTz ? isoString : `${isoString}Z`)
}

export function formatLocalDateTime(isoString) {
  const d = asUtcDate(isoString)
  return d ? d.toLocaleString() : '—'
}

export function formatLocalDate(isoString) {
  const d = asUtcDate(isoString)
  return d ? d.toLocaleDateString() : '—'
}
