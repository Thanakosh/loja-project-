
import { Navigate, Route, Routes } from 'react-router-dom'

import { PrivateRoute } from './components/PrivateRoute'
import Layout from './components/Layout'
import Clientes from './pages/Clientes'
import Dashboard from './pages/Dashboard'
import Estoque from './pages/Estoque'
import Fornecedores from './pages/Fornecedores'
import Login from './pages/Login'
import Orcamentos from './pages/Orcamentos'
import PDV from './pages/PDV'
import Produtos from './pages/Produtos'
import Relatorios from './pages/Relatorios'

const App = () => {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route element={<PrivateRoute />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate replace to="/dashboard" />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/pdv" element={<PDV />} />
          <Route path="/produtos" element={<Produtos />} />
          <Route path="/estoque" element={<Estoque />} />
          <Route path="/orcamentos" element={<Orcamentos />} />
          <Route path="/fornecedores" element={<Fornecedores />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/relatorios" element={<Relatorios />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  )
}

export default App
