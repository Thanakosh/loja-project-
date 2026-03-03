import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import { PrivateRoute } from './components/PrivateRoute'
import Clientes from './pages/Clientes'
import Dashboard from './pages/Dashboard'
import Estoque from './pages/Estoque'
import Fornecedores from './pages/Fornecedores'
import Login from './pages/Login'
import NotasFiscais from './pages/NotasFiscais'
import Orcamentos from './pages/Orcamentos'
import PDV from './pages/PDV'
import CaixaDiario from './pages/CaixaDiario'
import Produtos from './pages/Produtos'
import Relatorios from './pages/Relatorios'
import Vendas from './pages/Vendas'
import ContasReceber from './pages/ContasReceber'
import ImportarNota from './pages/ImportarNota'
import Usuarios from './pages/Usuarios'
import { Toaster } from 'react-hot-toast'

const App = () => {
  return (
    <>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<PrivateRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Navigate replace to="/dashboard" />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/pdv" element={<PDV />} />
            <Route path="/caixa" element={<CaixaDiario />} />
            <Route path="/vendas" element={<Vendas />} />
            <Route path="/produtos" element={<Produtos />} />
            <Route path="/estoque" element={<Estoque />} />
            <Route path="/orcamentos" element={<Orcamentos />} />
            <Route path="/fornecedores" element={<Fornecedores />} />
            <Route path="/notas-fiscais" element={<NotasFiscais />} />
            <Route path="/clientes" element={<Clientes />} />
            <Route path="/contas-receber" element={<ContasReceber />} />
            <Route path="/relatorios" element={<Relatorios />} />
            <Route path="/importar-nota" element={<ImportarNota />} />
            <Route path="/usuarios" element={<Usuarios />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate replace to="/" />} />
      </Routes>
    </>
  )
}

export default App
