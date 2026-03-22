import { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import type { AxiosError } from 'axios'

import { useAtualizarConfiguracaoLoja, useConfiguracaoLoja } from '../hooks/useConfiguracoes'
import type { ConfiguracaoLojaPayload } from '../types/configuracoes'

const formInicial: ConfiguracaoLojaPayload = {
  cnpj: null,
  razao_social: null,
  nome_fantasia: null,
  logradouro: null,
  numero: null,
  bairro: null,
  municipio: null,
  porte: null,
  inscricao_estadual: null,
  inscricao_municipal: null,
  regime_tributario: 'simples_nacional',
  uf: 'SP',
  cep: null,
  pais: 'Brasil',
  fone: null,
  email: null,
  cnae: null,
}

const formatarDocumento = (valor: string | null) => valor ?? ''

const ConfiguracoesLoja = () => {
  const { data, isLoading, isError } = useConfiguracaoLoja()
  const atualizarMutation = useAtualizarConfiguracaoLoja()
  const [form, setForm] = useState<ConfiguracaoLojaPayload>(formInicial)
  const [cepLoading, setCepLoading] = useState(false)

  useEffect(() => {
    if (!data) return

    setForm({
      cnpj: data.cnpj,
      razao_social: data.razao_social,
      nome_fantasia: data.nome_fantasia,
      logradouro: data.logradouro,
      numero: data.numero,
      bairro: data.bairro,
      municipio: data.municipio,
      porte: data.porte,
      inscricao_estadual: data.inscricao_estadual,
      inscricao_municipal: data.inscricao_municipal,
      regime_tributario: data.regime_tributario,
      uf: data.uf,
      cep: data.cep,
      pais: data.pais,
      fone: data.fone,
      email: data.email,
      cnae: data.cnae,
    })
  }, [data])

  const preencherEnderecoPorCep = async () => {
    const cepNormalizado = (form.cep ?? '').replace(/\D/g, '')
    if (cepNormalizado.length !== 8) return

    try {
      setCepLoading(true)
      const response = await fetch(`https://viacep.com.br/ws/${cepNormalizado}/json/`)
      if (!response.ok) {
        throw new Error('Falha ao consultar CEP')
      }

      const dataCep = (await response.json()) as {
        erro?: boolean
        logradouro?: string
        bairro?: string
        localidade?: string
        uf?: string
      }

      if (dataCep.erro) {
        toast.error('CEP nao encontrado.')
        return
      }

      setForm((estadoAtual) => ({
        ...estadoAtual,
        logradouro: dataCep.logradouro || estadoAtual.logradouro,
        bairro: dataCep.bairro || estadoAtual.bairro,
        municipio: dataCep.localidade || estadoAtual.municipio,
        uf: (dataCep.uf || estadoAtual.uf).toUpperCase(),
        pais: estadoAtual.pais || 'Brasil',
      }))
    } catch {
      toast.error('Nao foi possivel buscar o endereco pelo CEP.')
    } finally {
      setCepLoading(false)
    }
  }

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    const payload: ConfiguracaoLojaPayload = {
      ...form,
      uf: form.uf.trim().toUpperCase(),
    }

    atualizarMutation.mutate(payload, {
      onSuccess: () => {
        toast.success('Configuracoes da loja atualizadas.')
      },
      onError: (error: AxiosError<{ detail?: string }>) => {
        toast.error(error.response?.data?.detail ?? 'Nao foi possivel salvar as configuracoes da loja.')
      },
    })
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Configuracoes da Loja</h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Esses parametros alimentam a engine fiscal e regras de precificacao do sistema.
        </p>
      </div>

      <section className="rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm text-blue-900 dark:border-blue-900/60 dark:bg-blue-950/30 dark:text-blue-100">
        <p className="font-semibold">Impacto atual na engine</p>
        <p className="mt-2">
          Regime tributario, porte, inscricoes fiscais e UF ajudam a dar contexto para a leitura de notas de entrada e saida.
        </p>
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <section className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          {isLoading ? (
            <div className="py-10 text-center text-gray-500 dark:text-gray-400">Carregando configuracoes...</div>
          ) : isError ? (
            <div className="py-10 text-center text-red-600 dark:text-red-400">Erro ao carregar configuracoes da loja.</div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <label htmlFor="cnpj-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    CNPJ
                  </label>
                  <input
                    id="cnpj-loja"
                    type="text"
                    value={formatarDocumento(form.cnpj)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, cnpj: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="00.000.000/0000-00"
                  />
                </div>

                <div>
                  <label htmlFor="razao-social" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Razao social
                  </label>
                  <input
                    id="razao-social"
                    type="text"
                    value={formatarDocumento(form.razao_social)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, razao_social: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="nome-fantasia" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Nome fantasia
                  </label>
                  <input
                    id="nome-fantasia"
                    type="text"
                    value={formatarDocumento(form.nome_fantasia)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, nome_fantasia: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="regime-tributario" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Regime tributario
                  </label>
                  <select
                    id="regime-tributario"
                    value={form.regime_tributario}
                    onChange={(event) =>
                      setForm((estadoAtual) => ({
                        ...estadoAtual,
                        regime_tributario: event.target.value as ConfiguracaoLojaPayload['regime_tributario'],
                      }))
                    }
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="simples_nacional">Simples Nacional</option>
                    <option value="regime_normal">Regime Normal</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="cnae-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    CNAE
                  </label>
                  <input
                    id="cnae-loja"
                    type="text"
                    value={formatarDocumento(form.cnae)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, cnae: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="0000000"
                  />
                </div>

                <div>
                  <label htmlFor="porte-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Porte
                  </label>
                  <select
                    id="porte-loja"
                    value={form.porte ?? ''}
                    onChange={(event) =>
                      setForm((estadoAtual) => ({
                        ...estadoAtual,
                        porte: event.target.value === '' ? null : (event.target.value as ConfiguracaoLojaPayload['porte']),
                      }))
                    }
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="">Selecione</option>
                    <option value="ME">ME</option>
                    <option value="EPP">EPP</option>
                    <option value="MEI">MEI</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="inscricao-estadual" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Inscricao estadual
                  </label>
                  <input
                    id="inscricao-estadual"
                    type="text"
                    value={formatarDocumento(form.inscricao_estadual)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, inscricao_estadual: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="inscricao-municipal" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Inscricao municipal
                  </label>
                  <input
                    id="inscricao-municipal"
                    type="text"
                    value={formatarDocumento(form.inscricao_municipal)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, inscricao_municipal: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="email-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    E-mail
                  </label>
                  <input
                    id="email-loja"
                    type="email"
                    value={formatarDocumento(form.email)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, email: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="fone-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Fone
                  </label>
                  <input
                    id="fone-loja"
                    type="text"
                    value={formatarDocumento(form.fone)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, fone: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="(00) 0000-0000"
                  />
                </div>

                <div>
                  <label htmlFor="cep-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    CEP
                  </label>
                  <div className="flex gap-2">
                    <input
                      id="cep-loja"
                      type="text"
                      value={formatarDocumento(form.cep)}
                      onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, cep: event.target.value }))}
                      onBlur={() => void preencherEnderecoPorCep()}
                      className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                      placeholder="00000-000"
                    />
                    <button
                      type="button"
                      onClick={() => void preencherEnderecoPorCep()}
                      className="rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-gray-700"
                    >
                      {cepLoading ? 'Buscando...' : 'Buscar'}
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="logradouro-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Logradouro
                  </label>
                  <input
                    id="logradouro-loja"
                    type="text"
                    value={formatarDocumento(form.logradouro)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, logradouro: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="numero-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Numero
                  </label>
                  <input
                    id="numero-loja"
                    type="text"
                    value={formatarDocumento(form.numero)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, numero: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="bairro-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Bairro
                  </label>
                  <input
                    id="bairro-loja"
                    type="text"
                    value={formatarDocumento(form.bairro)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, bairro: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="municipio-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Municipio
                  </label>
                  <input
                    id="municipio-loja"
                    type="text"
                    value={formatarDocumento(form.municipio)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, municipio: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label htmlFor="uf-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    UF da loja
                  </label>
                  <input
                    id="uf-loja"
                    type="text"
                    inputMode="text"
                    maxLength={2}
                    value={form.uf}
                    onChange={(event) =>
                      setForm((estadoAtual) => ({
                        ...estadoAtual,
                        uf: event.target.value.toUpperCase(),
                      }))
                    }
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm uppercase text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="SP"
                  />
                </div>

                <div>
                  <label htmlFor="pais-loja" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Pais
                  </label>
                  <input
                    id="pais-loja"
                    type="text"
                    value={formatarDocumento(form.pais)}
                    onChange={(event) => setForm((estadoAtual) => ({ ...estadoAtual, pais: event.target.value }))}
                    className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none focus:ring-2 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                    placeholder="Brasil"
                  />
                </div>

              </div>

              <div className="flex items-center justify-between gap-4 border-t border-gray-200 pt-4 dark:border-gray-700">
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {data ? `Ultima atualizacao: ${new Date(data.updated_at).toLocaleString('pt-BR')}` : 'Sem dados carregados.'}
                </div>
                <button
                  type="submit"
                  disabled={atualizarMutation.isPending}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {atualizarMutation.isPending ? 'Salvando...' : 'Salvar configuracoes'}
                </button>
              </div>
            </form>
          )}
        </section>

        <aside className="space-y-4">
          <section className="rounded-xl border border-amber-200 bg-amber-50 p-5 shadow-sm dark:border-amber-900/50 dark:bg-amber-950/30">
            <h2 className="text-base font-semibold text-amber-900 dark:text-amber-100">Dados ainda pendentes</h2>
            <ul className="mt-3 space-y-2 text-sm text-amber-900 dark:text-amber-100">
              <li>CRT e enquadramento fiscal detalhado</li>
              <li>Parametros especificos para regras de entrada e saida</li>
              <li>Dados complementares de emissao e ambiente fiscal</li>
            </ul>
          </section>

          <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">Leitura atual da engine</h2>
            <ul className="mt-3 space-y-2 text-sm text-gray-600 dark:text-gray-300">
              <li>Entrada usa CFOP, regime e outlier de preco por NCM.</li>
              <li>Saida usa contexto da operacao e nao penaliza outlier de compra.</li>
              <li>Quanto melhor o cadastro fiscal da loja, menor a chance de falso positivo.</li>
            </ul>
          </section>
        </aside>
      </div>
    </div>
  )
}

export default ConfiguracoesLoja
