import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { useLogin } from '../hooks/useAuth'
import logoImg from '../assets/logo.png'

const Login = () => {
  const navigate = useNavigate()
  const { login, isLoading, error } = useLogin()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    try {
      await login(username, password)
      navigate('/dashboard', { replace: true })
    } catch {
      // Erro já tratado no hook
    }
  }

  return (
    <section className="flex min-h-screen items-center justify-center bg-gray-900 px-4 py-10">
      <div className="w-full max-w-md rounded-xl bg-gray-800 p-6 shadow-lg sm:p-8 border border-gray-700">
        <div className="mb-6 flex justify-center">
          <img src={logoImg} alt="Logo Eletroluz" className="h-32 object-contain" />
        </div>
        <h1 className="text-center text-2xl font-semibold text-gray-100">Entrar</h1>
        <p className="mt-2 text-center text-sm text-gray-400">Acesse sua conta para continuar.</p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300" htmlFor="username">
              Usuário ou e-mail
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 outline-none ring-emerald-500 transition focus:ring placeholder:text-gray-400"
              placeholder="Digite seu usuario ou e-mail"
              required
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-300" htmlFor="password">
              Senha
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-md border border-gray-600 bg-gray-700 px-3 py-2 text-gray-100 outline-none ring-emerald-500 transition focus:ring placeholder:text-gray-400"
              placeholder="••••••••"
              required
            />
          </div>

          {error ? <p className="rounded-md bg-red-900/40 p-3 text-sm font-medium text-red-400 border border-red-700">{error}</p> : null}

          <button
            type="submit"
            disabled={isLoading || !username || !password}
            className="w-full rounded-md bg-emerald-600 px-4 py-2 font-medium text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isLoading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
      </div>
    </section>
  )
}

export default Login
