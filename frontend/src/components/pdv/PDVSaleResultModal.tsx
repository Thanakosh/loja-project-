import Modal from '../ui/Modal'

interface VendaPDVRead {
  id: number
  numero_legado?: string | number | null
  total: number
  forma_pagamento?: number | null
  forma_pagamento_label?: string | null
  troco?: number
  pagamentos?: {
    forma_pagamento: number
    forma_pagamento_label?: string | null
    valor: number
  }[]
}

interface PDVSaleResultModalProps {
  open: boolean
  saleResult: VendaPDVRead | null
  totalVenda: number
  formaPagamento?: number | null
  moneyFormatter: Intl.NumberFormat
  formatPayment: (value?: number | null) => string
  onPrint: () => void
  onReset: () => void
}

const PDVSaleResultModal = ({
  open,
  saleResult,
  totalVenda,
  formaPagamento,
  moneyFormatter,
  formatPayment,
  onPrint,
  onReset,
}: PDVSaleResultModalProps) => (
  <Modal
    open={open}
    onClose={onReset}
    size="sm"
    title="Venda concluída"
    footer={
      <button
        type="button"
        onClick={onReset}
        className="w-full rounded-lg bg-emerald-600 px-4 py-2 font-semibold text-white transition hover:bg-emerald-700"
      >
        Nova Venda
      </button>
    }
  >
    <div className="space-y-4 px-6 py-5">
      <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
        <p>
          Número da venda: <strong>{saleResult?.numero_legado ?? saleResult?.id}</strong>
        </p>
        <p>
          Total: <strong>{moneyFormatter.format(Number(saleResult?.total ?? totalVenda))}</strong>
        </p>
        <p>
          Forma de pagamento: <strong>{saleResult?.forma_pagamento_label ?? formatPayment(saleResult?.forma_pagamento ?? formaPagamento)}</strong>
        </p>
        {saleResult?.pagamentos?.map((pagamento, index) => (
          <p key={`${pagamento.forma_pagamento}-${index}`}>
            {pagamento.forma_pagamento_label ?? formatPayment(pagamento.forma_pagamento)}: <strong>{moneyFormatter.format(pagamento.valor)}</strong>
          </p>
        ))}
        {(saleResult?.troco ?? 0) > 0 ? (
          <p>
            Troco: <strong>{moneyFormatter.format(saleResult?.troco ?? 0)}</strong>
          </p>
        ) : null}
      </div>

      <button
        type="button"
        onClick={onPrint}
        className="w-full rounded-lg border border-indigo-300 bg-indigo-50 px-4 py-2 font-semibold text-indigo-700 transition hover:bg-indigo-100 dark:border-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300 dark:hover:bg-indigo-900/50"
      >
        Gerar comprovante (PDF)
      </button>
    </div>
  </Modal>
)

export default PDVSaleResultModal
