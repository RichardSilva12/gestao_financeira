import { useAuthState } from "react-firebase-hooks/auth";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import Dashboard from '../pages/Dashboard/index';
import { Login } from "../pages/Login/index";
import { Register } from "../pages/Register/index";
import { auth } from "../services/firebaseConfig";

export function AppRoutes() {
  const [user, loading] = useAuthState(auth);

  if (loading) {
    return <p>Carregando...</p>;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={user ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} />
        <Route path="/dashboard" element={user ? <Dashboard user={user} /> : <Navigate to="/login" />} />
        <Route path="/login" element={!user ? <Login /> : <Navigate to="/dashboard" />} />
        <Route path="/register" element={!user ? <Register /> : <Navigate to="/dashboard" />} />
      </Routes>

    </BrowserRouter>
  );
}
