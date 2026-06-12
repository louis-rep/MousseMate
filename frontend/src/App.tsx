import { useState } from "react";
import { NavLink, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./hooks/useAuth";
import Feed from "./pages/Feed";
import Login from "./pages/Login";
import MapPage from "./pages/Map";
import Mates from "./pages/Mates";
import Profile from "./pages/Profile";
import Register from "./pages/Register";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `text-sm font-medium px-3 py-1 rounded transition-colors ${
    isActive ? "bg-white text-amber-700" : "text-amber-100 hover:text-white hover:bg-amber-500"
  }`;

function Nav() {
  const { isAuthenticated, userId, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  if (!isAuthenticated) return null;

  const navLinks = (
    <>
      <NavLink to="/" end className={navLinkClass} onClick={() => setMenuOpen(false)}>Feed</NavLink>
      {userId !== null && (
        <NavLink to={`/profile/${userId}`} className={navLinkClass} onClick={() => setMenuOpen(false)}>My Profile</NavLink>
      )}
      <NavLink to="/mates" className={navLinkClass} onClick={() => setMenuOpen(false)}>Mates</NavLink>
      <NavLink to="/map" className={navLinkClass} onClick={() => setMenuOpen(false)}>Map</NavLink>
    </>
  );

  return (
    <nav className="bg-amber-600 shadow-md">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-4">
        <NavLink to="/" className="text-white font-bold text-xl tracking-tight hover:opacity-80 transition-opacity shrink-0">
          🍺 MousseMate
        </NavLink>

        {/* Desktop links */}
        <div className="hidden sm:flex items-center gap-2 flex-1">
          {navLinks}
          <button
            onClick={handleLogout}
            className="ml-auto text-sm font-medium px-3 py-1 rounded text-amber-100 hover:text-white hover:bg-amber-500 transition-colors"
          >
            Sign out
          </button>
        </div>

        {/* Mobile hamburger */}
        <button
          className="sm:hidden ml-auto text-white p-1 rounded hover:bg-amber-500 transition-colors"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Toggle menu"
        >
          {menuOpen ? (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className="sm:hidden bg-amber-700 px-4 pb-4 flex flex-col gap-2">
          {navLinks}
          <button
            onClick={() => { handleLogout(); setMenuOpen(false); }}
            className="text-sm font-medium px-3 py-1 rounded text-amber-100 hover:text-white hover:bg-amber-500 transition-colors text-left"
          >
            Sign out
          </button>
        </div>
      )}
    </nav>
  );
}

function PaddedLayout() {
  return (
    <div className="min-h-screen bg-amber-50">
      <Nav />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}

// Map page: no page chrome, the map fills everything below the navbar
function FullBleedLayout() {
  return (
    <div className="h-dvh bg-amber-50 flex flex-col">
      <Nav />
      <main className="flex-1 min-h-0">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<FullBleedLayout />}>
        <Route
          path="/map"
          element={
            <ProtectedRoute>
              <MapPage />
            </ProtectedRoute>
          }
        />
      </Route>
      <Route element={<PaddedLayout />}>
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Feed />
            </ProtectedRoute>
          }
        />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/profile/:userId"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/mates"
          element={
            <ProtectedRoute>
              <Mates />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}
