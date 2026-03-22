import type { ReactNode } from 'react'

import Modal from './Modal'

interface ConfirmDialogProps {
  open: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  description?: string
  confirmLabel?: string
  cancelLabel?: string
  tone?: 'danger' | 'warning' | 'primary'
  isPending?: boolean
  children?: ReactNode
}

const buttonToneClasses: Record<NonNullable<ConfirmDialogProps['tone']>, string> = {
  danger: 'bg-rose-600 hover:bg-rose-700',
  warning: 'bg-amber-600 hover:bg-amber-700',
  primary: 'bg-blue-600 hover:bg-blue-700',
}

const ConfirmDialog = ({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  tone = 'primary',
  isPending = false,
  children,
}: ConfirmDialogProps) => (
  <Modal
    open={open}
    onClose={onClose}
    title={title}
    description={description}
    size="sm"
    footer={
      <div className="flex justify-end gap-3">
        <button
          type="button"
          onClick={onClose}
          disabled={isPending}
          className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-60 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
        >
          {cancelLabel}
        </button>
        <button
          type="button"
          onClick={onConfirm}
          disabled={isPending}
          className={`rounded-lg px-4 py-2 text-sm font-semibold text-white transition disabled:opacity-60 ${buttonToneClasses[tone]}`.trim()}
        >
          {confirmLabel}
        </button>
      </div>
    }
  >
    <div className="space-y-4 px-6 py-5 text-sm text-gray-700 dark:text-gray-200">{children}</div>
  </Modal>
)

export default ConfirmDialog
