import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useProjectStore } from "../../store/ProjectStore"; // Adjust this import path as needed

export default function AuditSite() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  // Get selectedProject from Zustand store
  const selectedProject = useProjectStore((state) => state.selectedProject);

  // Defensive check: domain might be undefined if no project selected
  const domain = selectedProject?.domain;
  const project_id = selectedProject?.id

  const handleAudit = async () => {
    if (!domain) {
      setError("No project selected or domain unavailable.");
      return;
    }

    setIsLoading(true);
    setError("");
    const token = localStorage.getItem("access_token") || "";

    try {
      const res = await fetch("http://localhost:8000/audit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          url: domain,
          project_id:project_id,
          max_pages: 2,
          max_urls_per_domain: 2,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to start audit");
      }

      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-primary text-primaryText flex items-center justify-center px-4">
      <div className="max-w-xl w-full bg-surface p-8 rounded-2xl shadow-xl border border-border text-center">
        <h1 className="text-3xl font-semibold mb-2 text-primaryAccent">Audit Your Site</h1>
        <p className="text-secondaryText mb-6">Launch an automated SEO audit for your project with one click.</p>

        {error && <p className="text-error text-sm mb-4">{error}</p>}

        <button
          onClick={handleAudit}
          disabled={isLoading || !domain}
          className="w-full py-3 bg-primaryAccent hover:bg-accent-hover text-primaryText font-semibold rounded-lg transition disabled:opacity-50"
          title={!domain ? "Select a project to enable audit" : ""}
        >
          {isLoading ? "Auditing..." : "Start Audit"}
        </button>
      </div>
    </div>
  );
}
