import { NavLink } from "react-router-dom";
import { useState } from "react";
import {
  HomeIcon,
  PlusIcon,
  UserIcon,
  MagnifyingGlassIcon,
  ClipboardDocumentListIcon,
  BoltIcon,
  ChartBarIcon
} from "@heroicons/react/24/outline";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/solid";

export default function Sidebar() {
  const [open, setOpen] = useState(false);

  const navItems = [
    { name: "Dashboard", path: "/", icon: HomeIcon },
    { name: "User Profile", path: "/user-profile", icon: UserIcon },
    { name: "Create New Project", path: "/create-project", icon: PlusIcon },
    { name: "Audit Site", path: "/audit-site", icon: ClipboardDocumentListIcon },
    { name: "Generate Keywords", path: "/generate-keywords", icon: MagnifyingGlassIcon },
    { name: "Competitor Analysis", path: "/competitor-analysis", icon: ChartBarIcon },
    { name: "Content Suggestions", path: "/content-suggestions", icon: BoltIcon },
  ];

  return (
    <div className="min-h-screen flex">
      {/* Mobile Menu Toggle */}
      <div className="lg:hidden p-4 fixed z-50">
        <button
          onClick={() => setOpen(!open)}
          className="text-primaryText hover:text-primaryAccent"
        >
          {open ? <XMarkIcon className="w-6 h-6" /> : <Bars3Icon className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <aside
        className={`bg-surface text-primaryText w-64 p-6 fixed top-0 left-0 h-full z-40 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        } lg:relative lg:translate-x-0 lg:block`}
      >
        <h2 className="text-2xl font-bold text-primaryAccent mb-8">Elevora</h2>
        <nav className="space-y-4">
          {navItems.map(({ name, path, icon: Icon }) => (
            <NavLink
              key={name}
              to={path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                  isActive
                    ? "bg-primaryAccent text-primary"
                    : "text-secondaryText hover:bg-secondary hover:text-primaryText"
                }`
              }
              onClick={() => setOpen(false)}
            >
              <Icon className="w-5 h-5" />
              {name}
            </NavLink>
          ))}
        </nav>
      </aside>
    </div>
  );
}
