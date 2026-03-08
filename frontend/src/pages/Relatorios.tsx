import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import toast from 'react-hot-toast'

import api from '../services/api'
import { getToken } from '../utils/auth'

const apiV2 = axios.create({ baseURL: api.defaults.baseURL?.replace('/api/v1', '/api/v2') || 'http://localhost:8000/api/v2' })
apiV2.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

interface VendaItem {
  nome_produto?: string | null
  quantidade: number
}

interface Venda {
  id: number
  numero_legado: string | null
  data: string
  total: number
  desconto: number
  forma_pagamento: number
  cancelada: boolean
  itens: VendaItem[]
}

interface VendasPaginadas {
  items: Venda[]
  total: number
  page: number
  page_size: number
  pages: number
}

interface VendaResumo {
  total_bruto: number
  total_descontos: number
  total_liquido: number
  quantidade_vendas: number
  ticket_medio: number
}

interface EstoqueAtual {
  produto_id: number
  nome_produto: string
  quantidade_atual: number
  estoque_minimo: number
  estoque_baixo: boolean
  ultima_movimentacao: string | null
}

type Tab = 'vendas' | 'estoque' | 'resumo' | 'itens-mais-vendidos'

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value)

const downloadPdf = async (endpoint: string, filename: string, params?: Record<string, string>) => {
  const response = await api.get(endpoint, {
    params,
    responseType: 'blob'
  })

  const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return isNaN(d.getTime()) ? '-' : d.toLocaleDateString('pt-BR')
}

const formatDateTime = (dateStr: string | null) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return isNaN(d.getTime()) ? '-' : d.toLocaleString('pt-BR')
}

const FORMAS_PAGAMENTO: Record<number, string> = {
  1: 'Dinheiro',
  2: 'Débito',
  3: 'Crédito',
  4: 'PIX',
  5: 'Boleto',
  6: 'A Prazo'
}

const getTodayDate = () => new Date().toISOString().split('T')[0]
const getFirstDayOfMonth = () => {
  const d = new Date()
  d.setDate(1)
  return d.toISOString().split('T')[0]
}

const AbaVendas = () => {
  const [dataInicio, setDataInicio] = useState(getFirstDayOfMonth())
  const [dataFim, setDataFim] = useState(getTodayDate())
  const [page, setPage] = useState(1)
  const [downloadingPdf, setDownloadingPdf] = useState(false)
  const [filterQuery, setFilterQuery] = useState({ start: getFirstDayOfMonth(), end: getTodayDate() })

  const { data, isLoading } = useQuery({
    queryKey: ['vendas', filterQuery.start, filterQuery.end, page],
    queryFn: async () => {
      const response = await api.get('/vendas/', {
        params: { start_date: filterQuery.start, end_date: filterQuery.end, page, page_size: 100 }
      })
      return (response.data || { items: [], total: 0, page: 1, page_size: 100, pages: 0 }) as VendasPaginadas
    }
  })

  const vendas = data?.items || []

  const resumo = useMemo(() => {
    const items = data?.items || []
    const validas = items.filter(v => !v.cancelada)
    const total = validas.reduce((acc, v) => acc + (v.total || 0), 0)
    const descontos = validas.reduce((acc, v) => acc + (v.desconto || 0), 0)
    const qtd = validas.length
    const ticket = qtd > 0 ? total / qtd : 0
    return { total, descontos, qtd, ticket }
  }, [data?.items])

  const handleGerar = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    setFilterQuery({ start: dataInicio, end: dataFim })
  }

  const totalPages = data?.pages || 0
  const totalRegistros = data?.total || 0

  const handleExportarPdf = async () => {
    setDownloadingPdf(true)
    try {
      await downloadPdf(
        '/relatorios/vendas/pdf',
        `relatorio-vendas-${filterQuery.start}-a-${filterQuery.end}.pdf`,
        { start_date: filterQuery.start, end_date: filterQuery.end }
      )
    } catch {
      toast.error('Erro ao gerar PDF de vendas. Tente novamente.')
    } finally {
      setDownloadingPdf(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleGerar} className="flex flex-wrap items-end gap-4 bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data Início</label>
          <input type="date" value={dataInicio} onChange={e => setDataInicio(e.target.value)}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:ring-blue-500 focus:border-blue-500" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data Fim</label>
          <input type="date" value={dataFim} onChange={e => setDataFim(e.target.value)}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:ring-blue-500 focus:border-blue-500" required />
        </div>
        <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition border border-transparent">
          Gerar
        </button>
        <button
          type="button"
          onClick={handleExportarPdf}
          disabled={downloadingPdf}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-md transition border border-transparent disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {downloadingPdf ? 'Gerando PDF...' : 'Exportar PDF'}
        </button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total de Vendas', value: formatCurrency(resumo.total), color: 'text-emerald-600 dark:text-emerald-400' },
          { label: 'Quantidade', value: resumo.qtd, color: 'text-gray-900 dark:text-gray-100' },
          { label: 'Ticket Médio', value: formatCurrency(resumo.ticket), color: 'text-blue-600 dark:text-blue-400' },
          { label: 'Total Descontos', value: formatCurrency(resumo.descontos), color: 'text-red-500 dark:text-red-400' },
        ].map((card, idx) => (
          <div key={idx} className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">{card.label}</p>
            <p className={`text-2xl font-bold mt-1 ${card.color}`}>{card.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-200 dark:border-gray-700">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Data</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Número</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Itens</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Pagamento</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Desconto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Total</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Carregando...</td></tr>
              ) : vendas.length === 0 ? (
                <tr><td colSpan={6} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Nenhuma venda no período.</td></tr>
              ) : (
                vendas.map(v => (
                  <tr key={v.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition">
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap">{formatDateTime(v.data)}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap">
                      {v.numero_legado || `#${v.id}`}
                      {v.cancelada && <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">Cancelada</span>}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                      {v.itens?.reduce((acc, i) => acc + (i.quantidade || 0), 0) || 0}
                    </td>
                    <td className="px-6 py-4 text-sm whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                        {FORMAS_PAGAMENTO[v.forma_pagamento] || 'Outro'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">{formatCurrency(v.desconto || 0)}</td>
                    <td className={`px-6 py-4 text-sm font-medium ${v.cancelada ? 'text-gray-400 dark:text-gray-500 line-through' : 'text-emerald-600 dark:text-emerald-400'}`}>
                      {formatCurrency(v.total || 0)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <span className="text-sm text-gray-500 dark:text-gray-400">Página {data?.page || 1} de {totalPages || 1} — {totalRegistros} registros</span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage(current => Math.max(current - 1, 1))}
              disabled={isLoading || page <= 1}
              className="px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            <button
              type="button"
              onClick={() => setPage(current => (totalPages > 0 ? Math.min(current + 1, totalPages) : current + 1))}
              disabled={isLoading || (totalPages > 0 && page >= totalPages)}
              className="px-3 py-1.5 rounded-md border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Próxima
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

const AbaEstoque = () => {
  const [downloadingPdf, setDownloadingPdf] = useState(false)
  const { data, isLoading, isError } = useQuery({
    queryKey: ['estoque-baixo'],
    queryFn: async () => {
      const resp = await apiV2.get('/estoque/', {
        params: { apenas_baixo: true, apenas_ativos: true, page_size: 200 }
      })
      return {
        items: (resp.data?.items || []) as EstoqueAtual[],
        total: (resp.data?.total || 0) as number
      }
    }
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          type="button"
          onClick={async () => {
            setDownloadingPdf(true)
            try {
              await downloadPdf('/relatorios/estoque-baixo/pdf', 'relatorio-estoque-baixo.pdf')
            } catch {
              toast.error('Erro ao gerar PDF de estoque baixo. Tente novamente.')
            } finally {
              setDownloadingPdf(false)
            }
          }}
          disabled={downloadingPdf}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-md transition border border-transparent disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {downloadingPdf ? 'Gerando PDF...' : 'Exportar PDF'}
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow w-full md:w-1/3 border border-gray-200 dark:border-gray-700">
        <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Produtos Abaixo do Mínimo</p>
        <p className="text-3xl font-bold mt-1 text-red-600 dark:text-red-400">{isError ? '-' : (data?.total || 0)}</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-200 dark:border-gray-700">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Produto</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Estoque Atual</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Mínimo</th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Déficit</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Última Movimentação</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Carregando...</td></tr>
              ) : isError ? (
                <tr><td colSpan={5} className="px-6 py-4 text-center text-red-500 dark:text-red-400">Erro ao carregar os itens de estoque.</td></tr>
              ) : data?.items.length === 0 ? (
                <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Nenhum produto com estoque crítico.</td></tr>
              ) : (
                data?.items.map(item => {
                  const deficit = item.estoque_minimo - item.quantidade_atual
                  const rowClass = item.quantidade_atual <= 0
                    ? 'bg-red-50 dark:bg-red-900/20'
                    : 'bg-yellow-50 dark:bg-yellow-900/10'
                  const qtyClass = item.quantidade_atual <= 0
                    ? 'text-red-700 dark:text-red-400 font-bold'
                    : 'text-yellow-700 dark:text-yellow-400 font-bold'
                  return (
                    <tr key={item.produto_id} className={rowClass}>
                      <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-gray-100">{item.nome_produto}</td>
                      <td className={`px-6 py-4 text-sm text-center ${qtyClass}`}>{item.quantidade_atual}</td>
                      <td className="px-6 py-4 text-sm text-center text-gray-500 dark:text-gray-400">{item.estoque_minimo}</td>
                      <td className="px-6 py-4 text-sm text-center text-gray-900 dark:text-gray-100 font-medium">{deficit > 0 ? deficit : 0}</td>
                      <td className="px-6 py-4 text-sm text-right text-gray-500 dark:text-gray-400 whitespace-nowrap">{formatDateTime(item.ultima_movimentacao)}</td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

const AbaResumoMes = () => {
  const [downloadingPdf, setDownloadingPdf] = useState(false)
  const dataHoje = getTodayDate()
  const dataInicioMes = getFirstDayOfMonth()

  const dataInicioGrafico = useMemo(() => {
    const inicioMes = new Date(`${dataInicioMes}T00:00:00`)
    const maxRange = new Date(`${dataHoje}T00:00:00`)
    maxRange.setDate(maxRange.getDate() - 89)

    return inicioMes < maxRange ? maxRange.toISOString().split('T')[0] : dataInicioMes
  }, [dataInicioMes, dataHoje])

  const { data: resumo, isLoading: isLoadingResumo } = useQuery({
    queryKey: ['vendas-resumo', dataInicioMes, dataHoje],
    queryFn: async () => {
      const response = await api.get('/vendas/resumo', {
        params: { start_date: dataInicioMes, end_date: dataHoje }
      })
      return (response.data || {
        total_bruto: 0,
        total_descontos: 0,
        total_liquido: 0,
        quantidade_vendas: 0,
        ticket_medio: 0
      }) as VendaResumo
    }
  })

  const { data: vendas = [], isLoading: isLoadingGrafico } = useQuery({
    queryKey: ['vendas-mes-grafico', dataInicioGrafico, dataHoje],
    queryFn: async () => {
      const response = await api.get('/vendas/', {
        params: { start_date: dataInicioGrafico, end_date: dataHoje, page: 1, page_size: 200 }
      })
      return ((response.data?.items || []) as Venda[])
    }
  })

  const vendasPorDia = useMemo(() => {
    const validas = vendas.filter(v => !v.cancelada)

    const diaMap: Record<string, number> = {}
    validas.forEach(v => {
      if (!v.data) return
      const day = v.data.split('T')[0]
      if (!diaMap[day]) diaMap[day] = 0
      diaMap[day] += (v.total || 0)
    })

    const startDate = new Date(dataInicioGrafico + 'T00:00:00')
    const endDate = new Date(dataHoje + 'T00:00:00')
    const chartData = []
    let maxVal = 0

    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
      const dayStr = d.toISOString().split('T')[0]
      const val = diaMap[dayStr] || 0
      if (val > maxVal) maxVal = val
      chartData.push({ dayStr, val, dayNum: d.getDate() })
    }

    return { data: chartData, maxVal }
  }, [vendas, dataInicioGrafico, dataHoje])

  const isLoading = isLoadingResumo || isLoadingGrafico

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          type="button"
          onClick={async () => {
            setDownloadingPdf(true)
            try {
              await downloadPdf(
                '/relatorios/resumo-mes/pdf',
                `relatorio-resumo-${dataInicioMes}-a-${dataHoje}.pdf`,
                { start_date: dataInicioMes, end_date: dataHoje }
              )
            } catch {
              toast.error('Erro ao gerar PDF do resumo do mês. Tente novamente.')
            } finally {
              setDownloadingPdf(false)
            }
          }}
          disabled={downloadingPdf}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 px-4 rounded-md transition border border-transparent disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {downloadingPdf ? 'Gerando PDF...' : 'Exportar PDF'}
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: 'Faturamento Bruto', value: formatCurrency(resumo?.total_bruto || 0), color: 'text-gray-900 dark:text-gray-100' },
          { label: 'Descontos', value: formatCurrency(resumo?.total_descontos || 0), color: 'text-red-500 dark:text-red-400' },
          { label: 'Faturamento Líquido', value: formatCurrency(resumo?.total_liquido || 0), color: 'text-emerald-600 dark:text-emerald-400' },
          { label: 'Nº Vendas', value: resumo?.quantidade_vendas || 0, color: 'text-gray-900 dark:text-gray-100' },
          { label: 'Ticket Médio', value: formatCurrency(resumo?.ticket_medio || 0), color: 'text-blue-600 dark:text-blue-400' },
        ].map((c, i) => (
          <div key={i} className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
            <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider">{c.label}</p>
            <p className={`text-xl md:text-2xl font-bold mt-2 ${c.color}`}>{isLoadingResumo ? '...' : c.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-100 mb-6">Faturamento Diário - {new Date(dataInicioMes + 'T12:00:00').toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}</h3>
        <div className="h-64 flex items-end justify-between gap-1 w-full">
          {isLoading ? (
            <div className="w-full text-center text-gray-500 pt-20">Processando gráfico...</div>
          ) : vendasPorDia.data.length === 0 ? (
            <div className="w-full text-center text-gray-500 pt-20">Nenhum dado para exibir.</div>
          ) : (
            vendasPorDia.data.map(item => {
              const heightPct = vendasPorDia.maxVal > 0 ? (item.val / vendasPorDia.maxVal) * 100 : 0
              return (
                <div key={item.dayStr} className="flex-1 flex flex-col items-center group relative h-full justify-end">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute bottom-full mb-2 bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap z-10 pointer-events-none shadow-lg">
                    {formatDate(item.dayStr)}: {formatCurrency(item.val)}
                  </div>
                  <div
                    className="w-full bg-blue-500 hover:bg-blue-400 dark:bg-blue-600 dark:hover:bg-blue-500 rounded-t-sm transition-all duration-300 border border-blue-600 dark:border-blue-500"
                    style={{ height: `${Math.max(heightPct, 1)}%`, minHeight: item.val > 0 ? '4px' : '0' }}
                  ></div>
                  <div className="text-[10px] md:text-xs text-gray-500 dark:text-gray-400 mt-2 font-medium">
                    {item.dayNum}
                  </div>
                </div>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}

const AbaItensMaisVendidos = () => {
  const [dataInicio, setDataInicio] = useState(getFirstDayOfMonth())
  const [dataFim, setDataFim] = useState(getTodayDate())
  const [filterQuery, setFilterQuery] = useState({ start: getFirstDayOfMonth(), end: getTodayDate() })

  const { data: vendas = [], isLoading, isError } = useQuery({
    queryKey: ['itens-mais-vendidos', filterQuery.start, filterQuery.end],
    queryFn: async () => {
      const paramsBase = {
        start_date: filterQuery.start,
        end_date: filterQuery.end,
        page_size: 200
      }

      const firstResponse = await api.get('/vendas/', {
        params: {
          ...paramsBase,
          page: 1
        }
      })

      const firstPage = (firstResponse.data || {
        items: [],
        total: 0,
        page: 1,
        page_size: 200,
        pages: 0
      }) as VendasPaginadas

      const allVendas = [...(firstPage.items || [])]
      const pages = firstPage.pages || 0

      for (let currentPage = 2; currentPage <= pages; currentPage += 1) {
        const pageResponse = await api.get('/vendas/', {
          params: {
            ...paramsBase,
            page: currentPage
          }
        })

        const pageData = pageResponse.data as VendasPaginadas
        allVendas.push(...(pageData.items || []))
      }

      return allVendas
    }
  })

  const ranking = useMemo(() => {
    const itensMap = new Map<string, { nome: string; quantidade: number; vendas: number }>()

    vendas
      .filter((venda) => !venda.cancelada)
      .forEach((venda) => {
        const itensMarcadosNaVenda = new Set<string>()

        venda.itens?.forEach((item) => {
          const nome = (item.nome_produto || 'Produto sem nome').trim() || 'Produto sem nome'
          const quantidade = Number(item.quantidade) || 0

          if (quantidade <= 0) {
            return
          }

          const atual = itensMap.get(nome) || { nome, quantidade: 0, vendas: 0 }
          atual.quantidade += quantidade

          if (!itensMarcadosNaVenda.has(nome)) {
            atual.vendas += 1
            itensMarcadosNaVenda.add(nome)
          }

          itensMap.set(nome, atual)
        })
      })

    return Array.from(itensMap.values()).sort((a, b) => b.quantidade - a.quantidade)
  }, [vendas])

  const top10 = ranking.slice(0, 10)
  const totalUnidades = ranking.reduce((acc, item) => acc + item.quantidade, 0)

  const handleGerar = (e: React.FormEvent) => {
    e.preventDefault()
    setFilterQuery({ start: dataInicio, end: dataFim })
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleGerar} className="flex flex-wrap items-end gap-4 bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data Início</label>
          <input
            type="date"
            value={dataInicio}
            onChange={(e) => setDataInicio(e.target.value)}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Data Fim</label>
          <input
            type="date"
            value={dataFim}
            onChange={(e) => setDataFim(e.target.value)}
            className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>
        <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition border border-transparent">
          Gerar
        </button>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Itens Distintos Vendidos</p>
          <p className="text-2xl font-bold mt-1 text-gray-900 dark:text-gray-100">{ranking.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Unidades Vendidas</p>
          <p className="text-2xl font-bold mt-1 text-emerald-600 dark:text-emerald-400">{totalUnidades.toLocaleString('pt-BR')}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Top Exibido</p>
          <p className="text-2xl font-bold mt-1 text-blue-600 dark:text-blue-400">{Math.min(10, ranking.length)}</p>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden border border-gray-200 dark:border-gray-700">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Posição</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Produto</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Unidades Vendidas</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Nº de Vendas</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Carregando...</td></tr>
              ) : isError ? (
                <tr><td colSpan={4} className="px-6 py-4 text-center text-red-500 dark:text-red-400">Erro ao carregar itens mais vendidos.</td></tr>
              ) : top10.length === 0 ? (
                <tr><td colSpan={4} className="px-6 py-4 text-center text-gray-500 dark:text-gray-400">Nenhum item vendido no período.</td></tr>
              ) : (
                top10.map((item, index) => (
                  <tr key={`${item.nome}-${index}`} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition">
                    <td className="px-6 py-4 text-sm font-semibold text-gray-900 dark:text-gray-100">#{index + 1}</td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{item.nome}</td>
                    <td className="px-6 py-4 text-sm text-right font-medium text-emerald-600 dark:text-emerald-400">{item.quantidade.toLocaleString('pt-BR')}</td>
                    <td className="px-6 py-4 text-sm text-right text-gray-600 dark:text-gray-300">{item.vendas.toLocaleString('pt-BR')}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

const Relatorios = () => {
  const [activeTab, setActiveTab] = useState<Tab>('vendas')

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Relatórios</h1>
      </div>

      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-6 overflow-x-auto">
          <button
            onClick={() => setActiveTab('vendas')}
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'vendas'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:border-gray-600'
              }`}
          >
            Vendas por Período
          </button>
          <button
            onClick={() => setActiveTab('estoque')}
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'estoque'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:border-gray-600'
              }`}
          >
            Estoque Baixo
          </button>
          <button
            onClick={() => setActiveTab('resumo')}
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'resumo'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:border-gray-600'
              }`}
          >
            Resumo do Mês
          </button>
          <button
            onClick={() => setActiveTab('itens-mais-vendidos')}
            className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors ${activeTab === 'itens-mais-vendidos'
              ? 'border-blue-500 text-blue-600 dark:text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:border-gray-600'
              }`}
          >
            Itens Mais Vendidos
          </button>
        </nav>
      </div>

      <div className="mt-4">
        {activeTab === 'vendas' && <AbaVendas />}
        {activeTab === 'estoque' && <AbaEstoque />}
        {activeTab === 'resumo' && <AbaResumoMes />}
        {activeTab === 'itens-mais-vendidos' && <AbaItensMaisVendidos />}
      </div>
    </div>
  )
}

export default Relatorios
