import { useEffect, useMemo, useState } from 'react'
import type { AxiosError } from 'axios'
import { Building2, MapPinned, MessageCircle, Power, QrCode, ReceiptText, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'

import { useAtualizarConfiguracaoLoja, useConfiguracaoLoja } from '../hooks/useConfiguracoes'
import { useConnectWhatsApp, useDisconnectWhatsApp, useWhatsAppStatus } from '../hooks/useWhatsApp'
import type { ConfiguracaoLojaPayload } from '../types/configuracoes'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

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

const PORTE_NONE = '__none__'

const asFieldValue = (valor: string | null) => valor ?? ''
const whatsappStatusLabel = {
  disconnected: 'Desconectado',
  connecting: 'Aguardando QR',
  connected: 'Conectado',
  error: 'Com erro',
} as const
const whatsappStatusClassName = {
  disconnected: 'border-border text-muted-foreground',
  connecting: 'border-amber-500/40 text-amber-700',
  connected: 'border-primary/30 text-primary',
  error: 'border-destructive/30 text-destructive',
} as const

const ConfiguracoesLoja = () => {
  const { data, isLoading, isError } = useConfiguracaoLoja()
  const atualizarMutation = useAtualizarConfiguracaoLoja()
  const whatsappStatusQuery = useWhatsAppStatus()
  const connectWhatsAppMutation = useConnectWhatsApp()
  const disconnectWhatsAppMutation = useDisconnectWhatsApp()
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

  const updateField = (field: keyof ConfiguracaoLojaPayload, value: string | null) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const preencherEnderecoPorCep = async () => {
    const cepNormalizado = (form.cep ?? '').replace(/\D/g, '')
    if (cepNormalizado.length !== 8) return

    try {
      setCepLoading(true)
      const response = await fetch(`https://viacep.com.br/ws/${cepNormalizado}/json/`)
      if (!response.ok) throw new Error('Falha ao consultar CEP')

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
      onSuccess: () => toast.success('Configuracoes da loja atualizadas.'),
      onError: (error: AxiosError<{ detail?: string }>) => {
        toast.error(error.response?.data?.detail ?? 'Nao foi possivel salvar as configuracoes da loja.')
      },
    })
  }

  const pendingFields = useMemo(
    () => [
      'CRT e enquadramento fiscal detalhado',
      'Parametros especificos para regras de entrada e saida',
      'Dados complementares de emissao e ambiente fiscal',
    ],
    [],
  )

  const engineNotes = useMemo(
    () => [
      'Entrada usa CFOP, regime e outlier de preco por NCM.',
      'Saida usa contexto da operacao e nao penaliza outlier de compra.',
      'Quanto melhor o cadastro fiscal da loja, menor a chance de falso positivo.',
    ],
    [],
  )

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold">Configuracoes da loja</h1>
        <p className="text-sm text-muted-foreground">
          Esses parametros alimentam a engine fiscal e as regras de precificacao do sistema.
        </p>
      </div>

      <Alert>
        <ReceiptText className="size-4" />
        <AlertTitle>Impacto atual na engine</AlertTitle>
        <AlertDescription>
          Regime tributario, porte, inscricoes fiscais e UF ajudam a contextualizar leituras de notas de entrada e saida.
        </AlertDescription>
      </Alert>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,2fr)_minmax(320px,1fr)]">
        <form onSubmit={handleSubmit} className="space-y-5">
          <Card>
            <CardHeader className="gap-3">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="space-y-1">
                  <CardTitle>Cadastro fiscal</CardTitle>
                  <CardDescription>Base juridica, regime tributario e inscricoes da empresa.</CardDescription>
                </div>
                {data && <Badge variant="outline">Atualizado em {new Date(data.updated_at).toLocaleString('pt-BR')}</Badge>}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoading ? (
                <p className="py-8 text-center text-muted-foreground">Carregando configuracoes...</p>
              ) : isError ? (
                <Alert variant="destructive">
                  <AlertTitle>Erro ao carregar configuracoes</AlertTitle>
                  <AlertDescription>Tente novamente em alguns instantes.</AlertDescription>
                </Alert>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="config-cnpj">CNPJ</Label>
                    <Input
                      id="config-cnpj"
                      value={asFieldValue(form.cnpj)}
                      onChange={(event) => updateField('cnpj', event.target.value)}
                      placeholder="00.000.000/0000-00"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-razao-social">Razao social</Label>
                    <Input
                      id="config-razao-social"
                      value={asFieldValue(form.razao_social)}
                      onChange={(event) => updateField('razao_social', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-nome-fantasia">Nome fantasia</Label>
                    <Input
                      id="config-nome-fantasia"
                      value={asFieldValue(form.nome_fantasia)}
                      onChange={(event) => updateField('nome_fantasia', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-regime">Regime tributario</Label>
                    <Select
                      value={form.regime_tributario}
                      onValueChange={(value) =>
                        setForm((current) => ({
                          ...current,
                          regime_tributario: value as ConfiguracaoLojaPayload['regime_tributario'],
                        }))
                      }
                    >
                      <SelectTrigger id="config-regime" className="w-full">
                        <SelectValue placeholder="Selecione o regime" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="simples_nacional">Simples Nacional</SelectItem>
                        <SelectItem value="regime_normal">Regime Normal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-cnae">CNAE</Label>
                    <Input
                      id="config-cnae"
                      value={asFieldValue(form.cnae)}
                      onChange={(event) => updateField('cnae', event.target.value)}
                      placeholder="0000000"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-porte">Porte</Label>
                    <Select
                      value={form.porte ?? PORTE_NONE}
                      onValueChange={(value) =>
                        setForm((current) => ({
                          ...current,
                          porte: value === PORTE_NONE ? null : (value as ConfiguracaoLojaPayload['porte']),
                        }))
                      }
                    >
                      <SelectTrigger id="config-porte" className="w-full">
                        <SelectValue placeholder="Selecione o porte" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value={PORTE_NONE}>Nao informado</SelectItem>
                        <SelectItem value="ME">ME</SelectItem>
                        <SelectItem value="EPP">EPP</SelectItem>
                        <SelectItem value="MEI">MEI</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-ie">Inscricao estadual</Label>
                    <Input
                      id="config-ie"
                      value={asFieldValue(form.inscricao_estadual)}
                      onChange={(event) => updateField('inscricao_estadual', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-im">Inscricao municipal</Label>
                    <Input
                      id="config-im"
                      value={asFieldValue(form.inscricao_municipal)}
                      onChange={(event) => updateField('inscricao_municipal', event.target.value)}
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Contato e endereco</CardTitle>
              <CardDescription>Informacoes comerciais e dados de localizacao utilizados em cadastros e documentos.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoading ? (
                <p className="py-8 text-center text-muted-foreground">Carregando endereco...</p>
              ) : isError ? (
                <Alert variant="destructive">
                  <AlertTitle>Erro ao carregar endereco</AlertTitle>
                  <AlertDescription>Os dados nao puderam ser exibidos.</AlertDescription>
                </Alert>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="config-email">E-mail</Label>
                    <Input
                      id="config-email"
                      type="email"
                      value={asFieldValue(form.email)}
                      onChange={(event) => updateField('email', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-fone">Fone</Label>
                    <Input
                      id="config-fone"
                      value={asFieldValue(form.fone)}
                      onChange={(event) => updateField('fone', event.target.value)}
                      placeholder="(00) 0000-0000"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-cep">CEP</Label>
                    <div className="flex gap-2">
                      <Input
                        id="config-cep"
                        value={asFieldValue(form.cep)}
                        onChange={(event) => updateField('cep', event.target.value)}
                        onBlur={() => void preencherEnderecoPorCep()}
                        placeholder="00000-000"
                      />
                      <Button type="button" variant="outline" onClick={() => void preencherEnderecoPorCep()}>
                        {cepLoading ? 'Buscando...' : 'Buscar'}
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-logradouro">Logradouro</Label>
                    <Input
                      id="config-logradouro"
                      value={asFieldValue(form.logradouro)}
                      onChange={(event) => updateField('logradouro', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-numero">Numero</Label>
                    <Input
                      id="config-numero"
                      value={asFieldValue(form.numero)}
                      onChange={(event) => updateField('numero', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-bairro">Bairro</Label>
                    <Input
                      id="config-bairro"
                      value={asFieldValue(form.bairro)}
                      onChange={(event) => updateField('bairro', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-municipio">Municipio</Label>
                    <Input
                      id="config-municipio"
                      value={asFieldValue(form.municipio)}
                      onChange={(event) => updateField('municipio', event.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-uf">UF</Label>
                    <Input
                      id="config-uf"
                      maxLength={2}
                      value={form.uf}
                      onChange={(event) => setForm((current) => ({ ...current, uf: event.target.value.toUpperCase() }))}
                      placeholder="SP"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="config-pais">Pais</Label>
                    <Input
                      id="config-pais"
                      value={asFieldValue(form.pais)}
                      onChange={(event) => updateField('pais', event.target.value)}
                      placeholder="Brasil"
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button type="submit" disabled={isLoading || isError || atualizarMutation.isPending}>
              {atualizarMutation.isPending ? 'Salvando...' : 'Salvar configuracoes'}
            </Button>
          </div>
        </form>

        <div className="space-y-4">
          <Card size="sm">
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <MessageCircle className="size-4" />
                    Canal WhatsApp
                  </CardTitle>
                  <CardDescription>Gateway separado com sessao QR, no estilo OpenClaw.</CardDescription>
                </div>
                {whatsappStatusQuery.data && (
                  <Badge
                    variant="outline"
                    className={whatsappStatusClassName[whatsappStatusQuery.data.status]}
                  >
                    {whatsappStatusLabel[whatsappStatusQuery.data.status]}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {whatsappStatusQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Carregando status do gateway...</p>
              ) : whatsappStatusQuery.isError ? (
                <Alert variant="destructive">
                  <AlertTitle>Falha ao consultar WhatsApp</AlertTitle>
                  <AlertDescription>Verifique se o backend e o gateway estao ativos.</AlertDescription>
                </Alert>
              ) : whatsappStatusQuery.data ? (
                <>
                  <div className="space-y-1 text-sm">
                    <p className="font-medium">
                      Numero vinculado:{' '}
                      <span className="font-normal text-muted-foreground">
                        {whatsappStatusQuery.data.linked_phone ?? 'Nenhum numero conectado'}
                      </span>
                    </p>
                    <p className="text-muted-foreground">
                      Conta: {whatsappStatusQuery.data.account_key} | Provider: {whatsappStatusQuery.data.provider}
                    </p>
                    {whatsappStatusQuery.data.last_connected_at && (
                      <p className="text-muted-foreground">
                        Ultima conexao: {new Date(whatsappStatusQuery.data.last_connected_at).toLocaleString('pt-BR')}
                      </p>
                    )}
                  </div>

                  {whatsappStatusQuery.data.qr_code_data_url && (
                    <div className="space-y-2 rounded-xl border border-dashed border-border p-3">
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <QrCode className="size-4" />
                        QR disponivel para pareamento
                      </div>
                      <img
                        src={whatsappStatusQuery.data.qr_code_data_url}
                        alt="QR Code do WhatsApp"
                        className="mx-auto size-48 rounded-lg border border-border bg-white p-2"
                      />
                      <p className="text-xs text-muted-foreground">
                        Escaneie com o WhatsApp Business do numero dedicado.
                      </p>
                    </div>
                  )}

                  {whatsappStatusQuery.data.last_error && (
                    <Alert variant="destructive">
                      <AlertTitle>Ultimo erro da sessao</AlertTitle>
                      <AlertDescription>{whatsappStatusQuery.data.last_error}</AlertDescription>
                    </Alert>
                  )}

                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() =>
                        connectWhatsAppMutation.mutate(
                          { force_refresh: false },
                          {
                            onSuccess: () => toast.success('Fluxo de pareamento iniciado.'),
                            onError: (error: AxiosError<{ detail?: string }>) =>
                              toast.error(error.response?.data?.detail ?? 'Nao foi possivel iniciar o pareamento.'),
                          },
                        )
                      }
                      disabled={connectWhatsAppMutation.isPending}
                    >
                      <MessageCircle className="size-4" />
                      {connectWhatsAppMutation.isPending ? 'Conectando...' : 'Conectar'}
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() =>
                        connectWhatsAppMutation.mutate(
                          { force_refresh: true },
                          {
                            onSuccess: () => toast.success('QR atualizado.'),
                            onError: (error: AxiosError<{ detail?: string }>) =>
                              toast.error(error.response?.data?.detail ?? 'Nao foi possivel atualizar o QR.'),
                          },
                        )
                      }
                      disabled={connectWhatsAppMutation.isPending}
                    >
                      <RefreshCw className="size-4" />
                      Atualizar QR
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() =>
                        disconnectWhatsAppMutation.mutate(undefined, {
                          onSuccess: () => toast.success('Sessao WhatsApp encerrada.'),
                          onError: (error: AxiosError<{ detail?: string }>) =>
                            toast.error(error.response?.data?.detail ?? 'Nao foi possivel desconectar a sessao.'),
                        })
                      }
                      disabled={disconnectWhatsAppMutation.isPending}
                    >
                      <Power className="size-4" />
                      {disconnectWhatsAppMutation.isPending ? 'Desconectando...' : 'Desconectar'}
                    </Button>
                  </div>
                </>
              ) : null}
            </CardContent>
          </Card>

          <Card size="sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Building2 className="size-4" />
                Dados ainda pendentes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {pendingFields.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          <Card size="sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <MapPinned className="size-4" />
                Leitura atual da engine
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                {engineNotes.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default ConfiguracoesLoja
