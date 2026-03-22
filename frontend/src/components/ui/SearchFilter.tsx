import type { ChangeEventHandler, FormEventHandler, ReactNode } from 'react'

interface SearchFilterProps {
  value: string
  onChange: ChangeEventHandler<HTMLInputElement>
  onSubmit?: FormEventHandler<HTMLFormElement>
  placeholder?: string
  label?: string
  actionLabel?: string
  actions?: ReactNode
  className?: string
  id?: string
}

const SearchFilter = ({
  value,
  onChange,
  onSubmit,
  placeholder = 'Buscar...',
  label,
  actionLabel = 'Buscar',
  actions,
  className = '',
  id,
}: SearchFilterProps) => (
  <form onSubmit={onSubmit} className={`flex flex-col gap-2 sm:flex-row sm:items-end ${className}`.trim()}>
    <div className="min-w-0 flex-1">
      {label ? (
        <label htmlFor={id} className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
      ) : null}
      <input
        id={id}
        type="text"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100"
      />
    </div>
    <div className="flex items-center gap-2">
      {onSubmit ? (
        <button
          type="submit"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          {actionLabel}
        </button>
      ) : null}
      {actions}
    </div>
  </form>
)

export default SearchFilter
