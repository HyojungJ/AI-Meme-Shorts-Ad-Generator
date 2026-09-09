const isDev = process.env.NODE_ENV !== 'production'

type LogLevel = 'debug' | 'info' | 'warn' | 'error'

function formatPrefix(level: LogLevel, tag?: string) {
  const ts = new Date().toISOString().slice(11, 23)
  const label = tag ? `[${tag}]` : ''
  return `${ts} ${level.toUpperCase()} ${label}`.trimEnd()
}

function log(level: LogLevel, tag: string | undefined, args: unknown[]) {
  const prefix = formatPrefix(level, tag)
  const fn = level === 'error' ? console.error
    : level === 'warn' ? console.warn
    : console.log
  fn(prefix, ...args)
}

export const logger = {
  debug(tag: string, ...args: unknown[]) {
    if (isDev) log('debug', tag, args)
  },
  info(tag: string, ...args: unknown[]) {
    log('info', tag, args)
  },
  warn(tag: string, ...args: unknown[]) {
    log('warn', tag, args)
  },
  error(tag: string, ...args: unknown[]) {
    log('error', tag, args)
  },
}
