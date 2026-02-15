import { Navigate, Outlet } from 'react-router-dom';
import { isAuthenticated } from '../utils/auth';

export const PrivateRoute = () => {
    if (!isAuthenticated()) {
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
};
