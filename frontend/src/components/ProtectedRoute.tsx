import { useEffect, useState } from "react";
import { Navigate, Outlet, useNavigate } from "react-router-dom";

const ProtectedRoute = () => {
  const [loading, setLoading] = useState(true);
  const [authorized, setAuthorized] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const validate = async () => {
      const accessToken = localStorage.getItem("access_token") || "";
      const refreshToken = localStorage.getItem("refresh_token") || "";

      try {
        const verifyRes = await fetch(`http://localhost:8000/verify-token/${accessToken}`);
        if (verifyRes.status === 403 && refreshToken) {
          const refreshRes = await fetch("http://localhost:8000/refresh", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });
          if (!refreshRes.ok) throw new Error("Refresh token invalid");
          const data = await refreshRes.json();
          localStorage.setItem("access_token", data.access_token);
          setAuthorized(true);
        } else if (!verifyRes.ok) {
          throw new Error("Access token invalid");
        } else {
          setAuthorized(true);
        }
      } catch (err) {
        localStorage.clear();
        setAuthorized(false);
        navigate("/login");
      } finally {
        setLoading(false);
      }
    };

    validate();
  }, [navigate]);

  if (loading) return <div>Loading...</div>;
  return authorized ? <Outlet /> : <Navigate to="/login" />;
};

export default ProtectedRoute;
