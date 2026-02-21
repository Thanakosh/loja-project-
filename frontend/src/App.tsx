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
import Produtos from './pages/Produtos'
import Relatorios from './pages/Relatorios'
import Vendas from './pages/Vendas'

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<PrivateRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate replace to="/dashboard" />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/pdv" element={<PDV />} />
          <Route path="/vendas" element={<Vendas />} />
          <Route path="/produtos" element={<Produtos />} />
          <Route path="/estoque" element={<Estoque />} />
          <Route path="/orcamentos" element={<Orcamentos />} />
          <Route path="/fornecedores" element={<Fornecedores />} />
          <Route path="/notas-fiscais" element={<NotasFiscais />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/relatorios" element={<Relatorios />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  )
}

export default App
