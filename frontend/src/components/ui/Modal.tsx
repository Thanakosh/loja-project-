import { useId } from 'react'
import type { ReactNode, MouseEvent } from 'react'

import { useAccessibleModal } from '../../hooks/useAccessibleModal'

interface ModalProps {
  open: boolean
  onClose: () => void
  title?: string
  description?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  children: ReactNode
  footer?: ReactNode
  className?: string
  panelClassName?: string
  closeLabel?: string
}

const sizeClasses: Record<NonNullable<ModalProps['size']>, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-2xl',
}

const Modal = ({
  open,
  onClose,
  title,
  description,
  size = 'md',
  children,
  footer,
  className = '',
  panelClassName = '',
  closeLabel = 'Fechar modal',
}: ModalProps) => {
  const modalRef = useAccessibleModal(open, onClose)
  const titleId = useId()

  if (!open) {
    return null
  }

  const handleBackdropMouseDown = (event: MouseEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget) {
      onClose()
    }
  }

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 ${className}`.trim()}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? titleId : undefined}
      onMouseDown={handleBackdropMouseDown}
    >
      <div
        ref={modalRef}
        tabIndex={-1}
        onMouseDown={(event) => event.stopPropagation()}
        className={`flex max-h-[90vh] w-full flex-col overflow-hidden rounded-xl border border-gray-200 bg-white shadow-2xl dark:border-gray-700 dark:bg-gray-800 ${sizeClasses[size]} ${panelClassName}`.trim()}
      >
        {title || description ? (
          <div className="flex items-start justify-between gap-3 border-b border-gray-200 px-6 py-4 dark:border-gray-700">
            <div>
              {title ? (
                <h2 id={titleId} className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                  {title}
                </h2>
              ) : null}
              {description ? (
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{description}</p>
              ) : null}
            </div>
            <button
              type="button"
              aria-label={closeLabel}
              onClick={onClose}
              className="rounded-md px-2 py-1 text-xl text-gray-400 transition hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-200"
            >
              ×
            </button>
          </div>
        ) : null}

        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>

        {footer ? (
          <div className="border-t border-gray-200 bg-gray-50 px-6 py-4 dark:border-gray-700 dark:bg-gray-700/50">
            {footer}
          </div>
        ) : null}
      </div>
    </div>
  )
}

export default Modal
