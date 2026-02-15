import { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';

const Layout = () => {
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const location = useLocation();
    const navigate = useNavigate();

    const handleLogout = () => {
        // TODO: Implement removeToken logic here
        console.log('Logging out...');
        navigate('/login');
    };

    const menuItems = [
        { name: 'Dashboard', path: '/dashboard', icon: '📊' },
        { name: 'PDV', path: '/pdv', icon: '🛒' },
        { name: 'Produtos', path: '/produtos', icon: '📦' },
        { name: 'Estoque', path: '/estoque', icon: '🏭' },
        { name: 'Orçamentos', path: '/orcamentos', icon: '💰' },
        { name: 'Fornecedores', path: '/fornecedores', icon: '🚚' },
        { name: 'Clientes', path: '/clientes', icon: '👥' },
        { name: 'Relatórios', path: '/relatorios', icon: '📈' },
    ];

    return (
        <div className="flex h-screen bg-gray-100 overflow-hidden">
            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`
        fixed inset-y-0 left-0 z-30 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:relative lg:translate-x-0
      `}>
                <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
                    <span className="text-xl font-bold text-gray-800">Loja Elétrica</span>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="lg:hidden text-gray-500 focus:outline-none text-2xl"
                    >
                        ✕
                    </button>
                </div>
                <nav className="p-4 space-y-2 overflow-y-auto h-[calc(100vh-4rem)]">
                    {menuItems.map((item) => (
                        <Link
                            key={item.path}
                            to={item.path}
                            onClick={() => setSidebarOpen(false)}
                            className={`
                flex items-center px-4 py-3 rounded-lg transition-colors duration-200
                ${location.pathname === item.path
                                    ? 'bg-blue-50 text-blue-700 font-medium'
                                    : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'}
              `}
                        >
                            <span className="mr-3 text-xl">{item.icon}</span>
                            <span>{item.name}</span>
                        </Link>
                    ))}
                </nav>
            </aside>

            {/* Main Content Wrapper */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <header className="h-16 bg-white shadow-sm flex items-center justify-between px-4 lg:px-6 z-10">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden text-gray-500 focus:outline-none text-2xl mr-4"
                    >
                        ☰
                    </button>

                    <div className="flex-1 lg:hidden">
                        <span className="text-lg font-semibold text-gray-800">Loja Elétrica</span>
                    </div>

                    <div className="ml-auto">
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        >
                            Sair
                        </button>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-4 lg:p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    );
};

export default Layout;
