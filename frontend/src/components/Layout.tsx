import Sidebar from './Sidebar'; // Your existing Sidebar component
import { Outlet } from 'react-router-dom'; // Import Outlet for nested routes

function Layout() {
  return (
    <div className="flex min-h-screen bg-gray-100 font-inter">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-grow overflow-y-auto">
        {/* Outlet renders the matched nested route component (your pages) */}
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;