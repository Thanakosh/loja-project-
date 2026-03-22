import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
}

const PageHeader = ({ title, description, actions }: PageHeaderProps) => (
  <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
    <div>
      <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">{title}</h1>
      {description ? (
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>
      ) : null}
    </div>
    {actions ? <div className="shrink-0">{actions}</div> : null}
  </div>
)

export default PageHeader
