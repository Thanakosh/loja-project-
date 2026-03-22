import type { ReactNode } from 'react'

interface StatusBadgeProps {
  children: ReactNode
  tone?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  className?: string
}

const toneClasses: Record<NonNullable<StatusBadgeProps['tone']>, string> = {
  default: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  success: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  danger: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
  info: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
}

const StatusBadge = ({ children, tone = 'default', className = '' }: StatusBadgeProps) => (
  <span
    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${toneClasses[tone]} ${className}`.trim()}
  >
    {children}
  </span>
)

export default StatusBadge
