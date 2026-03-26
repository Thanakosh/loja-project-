import { lazy, Suspense, type ReactNode } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'

import { PrivateRoute } from './components/PrivateRoute'
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
            <Route path="/pdv" element={withRouteSuspense(<PDV />)} />
            <Route path="/caixa" element={withRouteSuspense(<CaixaDiario />)} />
            <Route path="/vendas" element={withRouteSuspense(<Vendas />)} />
            <Route path="/produtos" element={withRouteSuspense(<Produtos />)} />
            <Route path="/estoque" element={withRouteSuspense(<Estoque />)} />
            <Route path="/orcamentos" element={withRouteSuspense(<Orcamentos />)} />
            <Route path="/fornecedores" element={withRouteSuspense(<Fornecedores />)} />
            <Route path="/notas-fiscais" element={withRouteSuspense(<NotasFiscais />)} />
            <Route path="/clientes" element={withRouteSuspense(<Clientes />)} />
            <Route path="/contas-receber" element={withRouteSuspense(<ContasReceber />)} />
            <Route path="/relatorios" element={withRouteSuspense(<Relatorios />)} />
            <Route path="/importar-nota" element={withRouteSuspense(<ImportarNota />)} />
            <Route path="/usuarios" element={withRouteSuspense(<Usuarios />)} />
            <Route path="/configuracoes/loja" element={withRouteSuspense(<ConfiguracoesLoja />)} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate replace to="/" />} />
      </Routes>
    </>
  )
}

export default App
