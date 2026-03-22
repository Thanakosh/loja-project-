import Modal from '../ui/Modal'

interface AlertaPrecoMinimo {
  produto_id: number
  produto_nome: string
  preco_praticado: number
  preco_minimo: number
  prejuizo_estimado: number
}

interface PDVPriceAlertModalProps {
  open: boolean
  alertas: AlertaPrecoMinimo[]
  moneyFormatter: Intl.NumberFormat
  onClose: () => void
  onConfirm: () => void
}

const PDVPriceAlertModal = ({
  open,
  alertas,
  moneyFormatter,
  onClose,
  onConfirm,
}: PDVPriceAlertModalProps) => (
  <Modal
    open={open}
    onClose={onClose}
    size="lg"
    title="Alerta de preço minimo"
    description={
      alertas.length === 1
        ? '1 produto está com preço abaixo do custo minimo calculado.'
        : `${alertas.length} produtos estão com preço abaixo do custo minimo calculado.`
    }
    footer={
      <div className="flex flex-col justify-end gap-3 sm:flex-row">
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg border border-gray-300 bg-white px-5 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
        >
          Corrigir preços
        </button>
        <button
          type="button"
          onClick={onConfirm}
          className="rounded-lg bg-amber-600 px-5 py-2 text-sm font-semibold text-white transition hover:bg-amber-700"
        >
          Vender mesmo assim
        </button>
      </div>
    }
  >
    <div className="space-y-2 px-6 py-4">
      {alertas.map((alerta) => (
        <div key={alerta.produto_id} className="rounded-xl border border-red-200 bg-red-50 p-3 dark:border-red-700 dark:bg-red-900/20">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 text-lg">🔴</span>
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-gray-800 dark:text-gray-100">{alerta.produto_nome}</p>
              <div className="mt-1.5 grid grid-cols-3 gap-2 text-sm">
                <div>
                  <p className="text-xs text-gray-400 dark:text-gray-500">Praticado</p>
                  <p className="font-semibold text-red-600 dark:text-red-400">
                    {moneyFormatter.format(alerta.preco_praticado)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 dark:text-gray-500">Minimo</p>
                  <p className="font-semibold text-gray-700 dark:text-gray-300">
                    {moneyFormatter.format(alerta.preco_minimo)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-400 dark:text-gray-500">Prejuizo</p>
                  <p className="font-semibold text-red-600 dark:text-red-400">
                    -{moneyFormatter.format(alerta.prejuizo_estimado)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  </Modal>
)

export default PDVPriceAlertModal
