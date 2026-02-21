import { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'

import { useTheme } from '../contexts/ThemeContext'
import { removeToken } from '../utils/auth'

const Layout = () => {
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const location = useLocation()
    const navigate = useNavigate()
    const { isDark, toggleTheme } = useTheme()

    const handleLogout = () => {
        removeToken()
        navigate('/login')
    }

    const menuItems = [
        { name: 'Dashboard', path: '/dashboard', icon: '📊' },
        { name: 'PDV', path: '/pdv', icon: '🛒' },
        { name: 'Vendas', path: '/vendas', icon: '🧾' },
        { name: 'Produtos', path: '/produtos', icon: '📦' },
        { name: 'Estoque', path: '/estoque', icon: '🏭' },
        { name: 'Orçamentos', path: '/orcamentos', icon: '💰' },
        { name: 'Fornecedores', path: '/fornecedores', icon: '🚚' },
        { name: 'Clientes', path: '/clientes', icon: '👥' },
        { name: 'Relatórios', path: '/relatorios', icon: '📈' },
    ]

    return (
        <div className="flex h-screen bg-gray-100 dark:bg-gray-900 overflow-hidden">
            {/* Mobile Sidebar Overlay */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`
                fixed inset-y-0 left-0 z-30 w-64 bg-white dark:bg-gray-800 shadow-lg transform transition-transform duration-300 ease-in-out
                ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
                lg:relative lg:translate-x-0
            `}>
                <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-gray-700">
                    <span className="text-xl font-bold text-gray-800 dark:text-white">Loja Elétrica</span>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="lg:hidden text-gray-500 dark:text-gray-400 focus:outline-none text-2xl"
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
                                    ? 'bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 font-medium'
                                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'}
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
                <header className="h-16 bg-white dark:bg-gray-800 shadow-sm flex items-center justify-between px-4 lg:px-6 z-10">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden text-gray-500 dark:text-gray-400 focus:outline-none text-2xl mr-4"
                    >
                        ☰
                    </button>

                    <div className="flex-1 lg:hidden">
                        <span className="text-lg font-semibold text-gray-800 dark:text-white">Loja Elétrica</span>
                    </div>

                    <div className="ml-auto flex items-center gap-3">
                        {/* Theme Toggle */}
                        <button
                            onClick={toggleTheme}
                            title={isDark ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
                            className="relative w-12 h-6 rounded-full transition-colors duration-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800"
                            style={{ backgroundColor: isDark ? '#3b82f6' : '#d1d5db' }}
                        >
                            <span
                                className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform duration-300 flex items-center justify-center text-xs"
                                style={{ transform: isDark ? 'translateX(24px)' : 'translateX(0)' }}
                            >
                                {isDark ? '🌙' : '☀️'}
                            </span>
                        </button>

                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 dark:bg-red-900/30 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors focus:outline-none"
                        >
                            Sair
                        </button>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 dark:bg-gray-900 p-4 lg:p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    )
}

export default Layout
