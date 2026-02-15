
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';

// Placeholder components for pages
const Dashboard = () => <div className="p-4 bg-white rounded-lg shadow">Dashboard Content</div>;
const PDV = () => <div className="p-4 bg-white rounded-lg shadow">PDV Content</div>;
const Produtos = () => <div className="p-4 bg-white rounded-lg shadow">Produtos Content</div>;
const Estoque = () => <div className="p-4 bg-white rounded-lg shadow">Estoque Content</div>;
const Orcamentos = () => <div className="p-4 bg-white rounded-lg shadow">Orçamentos Content</div>;
const Fornecedores = () => <div className="p-4 bg-white rounded-lg shadow">Fornecedores Content</div>;
const Clientes = () => <div className="p-4 bg-white rounded-lg shadow">Clientes Content</div>;
const Relatorios = () => <div className="p-4 bg-white rounded-lg shadow">Relatórios Content</div>;
const Login = () => <div className="min-h-screen flex items-center justify-center bg-gray-100">Login Page</div>;

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        {/* Protected Routes Wrapper */}
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/pdv" element={<PDV />} />
          <Route path="/produtos" element={<Produtos />} />
          <Route path="/estoque" element={<Estoque />} />
          <Route path="/orcamentos" element={<Orcamentos />} />
          <Route path="/fornecedores" element={<Fornecedores />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/relatorios" element={<Relatorios />} />
        </Route>

        {/* Catch all redirect to dashboard */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
