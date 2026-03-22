import type { ReactNode } from 'react'

export interface DataTableColumn<T> {
  key: string
  header: ReactNode
  render: (item: T) => ReactNode
  className?: string
  headerClassName?: string
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  data: T[]
  getRowKey: (item: T) => string | number
  emptyMessage: string
  loading?: boolean
  loadingMessage?: string
  className?: string
  rowClassName?: (item: T) => string
  page?: number
  totalPages?: number
  onPreviousPage?: () => void
  onNextPage?: () => void
  previousDisabled?: boolean
  nextDisabled?: boolean
}

const DataTable = <T,>({
  columns,
  data,
  getRowKey,
  emptyMessage,
  loading = false,
  loadingMessage = 'Carregando...',
  className = '',
  rowClassName,
  page,
  totalPages,
  onPreviousPage,
  onNextPage,
  previousDisabled,
  nextDisabled,
}: DataTableProps<T>) => (
  <div className={`overflow-hidden rounded-lg border border-gray-200 bg-white shadow dark:border-gray-700 dark:bg-gray-800 ${className}`.trim()}>
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-700">
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={`px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400 ${column.headerClassName ?? ''}`.trim()}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
          {loading ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                {loadingMessage}
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr key={getRowKey(item)} className={rowClassName?.(item)}>
                {columns.map((column) => (
                  <td key={column.key} className={`px-4 py-3 text-sm ${column.className ?? ''}`.trim()}>
                    {column.render(item)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>

    {page && totalPages ? (
      <div className="flex items-center justify-end gap-2 border-t border-gray-200 px-4 py-3 text-sm dark:border-gray-700">
        <button
          type="button"
          onClick={onPreviousPage}
          disabled={previousDisabled}
          className="rounded border border-gray-300 px-3 py-1.5 text-gray-700 transition hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          Anterior
        </button>
        <span className="text-gray-500 dark:text-gray-400">
          Pagina {page} de {totalPages}
        </span>
        <button
          type="button"
          onClick={onNextPage}
          disabled={nextDisabled}
          className="rounded border border-gray-300 px-3 py-1.5 text-gray-700 transition hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          Proxima
        </button>
      </div>
    ) : null}
  </div>
)

export default DataTable
