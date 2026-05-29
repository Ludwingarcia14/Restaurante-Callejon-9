import { useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useUsuarioStore } from './store'
import { cliente } from './api/cliente';
import { AUTH } from './api/endpoints';

import LoginPage from './pages/auth/LoginPage';
import RegistroPage from './pages/auth/RegistroPage';
import SucursalPage from './pages/pedido/SucursalPage';
import TipoOrdenPage from './pages/pedido/TipoOrdenPage';
import MenuPage from './pages/menu/MenuPage';
import CarritoPage from './pages/pedido/CarritoPage';
import SeguimientoPage from './pages/seguimiento/SeguimientoPage';
import PerfilPage from './pages/perfil/PerfilPage';
import EncuestaPage from './pages/perfil/EncuestaPage';

import Layout from './components/Layout';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 2,
            retry: 1,
            }
    }
})

function RutaPrivada({ children }) {
    const {usuario, cargando} = useUsuarioStore();

    if (cargando) return <div className="loading">Cargando...</div>
    return usuario ? children : <Navigate to="/login" replace/>;
}

export default function App() {
    const { setUsuario, limpiarUsuario } = useUsuarioStore()
    useEffect(() => {
        cliente.get(AUTH.me)
        .then((res) => setUsuario(res.data.usuario))
        .catch(() => limpiarUsuario())
        }, [])

    return (
        <QueryClientProvider client={queryClient}>
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/registro" element={<RegistroPage />} />
                    <Route path="/" element={<RutaPrivada><Layout /></RutaPrivada>}>
                        <Route index element={<Navigate to="/sucursal" replace />} />
                        <Route path="/sucursal" element={<SucursalPage />} />
                        <Route path="/tipo-orden" element={<TipoOrdenPage />} />
                        <Route path="/menu" element={<MenuPage />} />
                        <Route path="/carrito" element={<CarritoPage />} />
                        <Route path="/seguimiento/:pedidoId" element={<SeguimientoPage />}/>
                        <Route path="/perfil" element={<PerfilPage />} />
                        <Route path="/encuesta/:pedidoId" element={<EncuestaPage />} />

                    </Route>
                </Routes>
            </BrowserRouter>
        </QueryClientProvider>
    )
}