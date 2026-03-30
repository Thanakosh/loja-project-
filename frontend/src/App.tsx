import { lazy, Suspense, type ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { AdminRoute } from './components/AdminRoute'
import { PrivateRoute } from './components/PrivateRoute'
import { TabRoute } from './components/TabRoute'
import type { AppTabId } from './config/appTabs'
import { Toaster } from 'react-hot-toast'

const Layout = lazy(() => import('./components/Layout'))
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const PDV = lazy(() => import('./pages/PDV'))
const CaixaDiario = lazy(() => import('./pages/CaixaDiario'))
const Vendas = lazy(() => import('./pages/Vendas'))
const Produtos = lazy(() => import('./pages/Produtos'))
const Estoque = lazy(() => import('./pages/Estoque'))
const Orcamentos = lazy(() => import('./pages/Orcamentos'))
const Fornecedores = lazy(() => import('./pages/Fornecedores'))
const NotasFiscais = lazy(() => import('./pages/NotasFiscais'))
const Clientes = lazy(() => import('./pages/Clientes'))
const ContasReceber = lazy(() => import('./pages/ContasReceber'))
const Relatorios = lazy(() => import('./pages/Relatorios'))
const ImportarNota = lazy(() => import('./pages/ImportarNota'))
const Usuarios = lazy(() => import('./pages/Usuarios'))
const ConfiguracoesLoja = lazy(() => import('./pages/ConfiguracoesLoja'))

const RouteFallback = () => (
  <div className="flex min-h-[40vh] items-center justify-center px-6 text-sm text-gray-500 dark:text-gray-400">
    Carregando...
  </div>
)

const withRouteSuspense = (element: ReactNode) => (
  <Suspense fallback={<RouteFallback />}>{element}</Suspense>
)

const withTabAccess = (tabId: AppTabId, element: ReactNode) =>
  withRouteSuspense(<TabRoute tabId={tabId}>{element}</TabRoute>)

const withAdminAccess = (element: ReactNode) =>
  withRouteSuspense(<AdminRoute>{element}</AdminRoute>)

const App = () => {
  return (
    <>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={withRouteSuspense(<Login />)} />

        <Route element={<PrivateRoute />}>
          <Route element={withRouteSuspense(<Layout />)}>
            <Route path="/" element={<Navigate replace to="/dashboard" />} />
            <Route path="/dashboard" element={withRouteSuspense(<Dashboard />)} />
            <Route path="/pdv" element={withTabAccess('pdv', <PDV />)} />
            <Route path="/caixa" element={withTabAccess('caixa', <CaixaDiario />)} />
            <Route path="/vendas" element={withTabAccess('vendas', <Vendas />)} />
            <Route path="/produtos" element={withTabAccess('produtos', <Produtos />)} />
            <Route path="/estoque" element={withTabAccess('estoque', <Estoque />)} />
            <Route path="/orcamentos" element={withTabAccess('orcamentos', <Orcamentos />)} />
            <Route path="/fornecedores" element={withTabAccess('fornecedores', <Fornecedores />)} />
            <Route path="/notas-fiscais" element={withTabAccess('notas_fiscais', <NotasFiscais />)} />
            <Route path="/clientes" element={withTabAccess('clientes', <Clientes />)} />
            <Route path="/contas-receber" element={withTabAccess('contas_receber', <ContasReceber />)} />
            <Route path="/relatorios" element={withTabAccess('relatorios', <Relatorios />)} />
            <Route path="/importar-nota" element={withTabAccess('importar_nota', <ImportarNota />)} />
            <Route path="/usuarios" element={withAdminAccess(<Usuarios />)} />
            <Route path="/configuracoes/loja" element={withTabAccess('configuracoes', <ConfiguracoesLoja />)} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate replace to="/" />} />
      </Routes>
    </>
  )
}

export default App
