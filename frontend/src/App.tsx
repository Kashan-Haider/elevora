import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import GetStarted from "./pages/GetStarted";
import ProtectedRoute from "./components/ProtectedRoute";
import AuditSite from "./pages/AuditSite";
import UserProfile from "./pages/UserProfile";
import Layout from "./components/Layout"; // ← Add this
import AuditDashboard from "./pages/AuditDashboard";
import CreateProject from "./pages/CreateProject";

const App = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      {/* Protected Routes */}
      <Route element={<ProtectedRoute />}>
          <Route path="/get-started" element={<GetStarted />} />
        <Route element={<Layout />}>
          <Route path="/" element={<AuditDashboard />} />
          <Route path="/audit-site" element={<AuditSite />} />
          <Route path="/user-profile" element={<UserProfile />} />
          <Route path="/create-project" element={<CreateProject />} />
        </Route>
      </Route>
    </Routes>
  );
};

export default App;
