import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function GetStarted() {
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
  
    // Domain validation
    try {
      const url = new URL(domain);
      if (!["http:", "https:"].includes(url.protocol)) {
        throw new Error("Invalid URL protocol.");
      }
    } catch {
      setError("Please enter a valid domain (e.g. https://example.com)");
      return;
    }
  
    const token = localStorage.getItem("access_token");
  
    try {
      const res = await fetch("http://localhost:8000/create-project", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name, domain }),
      });
  
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to create project");
      }
  
      try {
        await fetch("https://your-api.com/audit", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            url: domain,
            max_pages: 2,
            max_urls_per_domain: 2,
          }),
        });
      } catch (err) {
        console.log("audit failed with error, " + err);
      }
  
      navigate("/user-profile");
    } catch (err) {
      setError((err as Error).message);
    }
  };
  

  return (
    <div className="min-h-screen bg-primary text-primaryText flex items-center justify-center px-4">
      <div className="max-w-xl w-full bg-surface p-8 rounded-2xl shadow-xl border border-border">
        <h1 className="text-3xl font-semibold mb-2 text-primaryAccent">Let's Get Started</h1>
        <p className="text-secondaryText mb-6">Create your first project to begin auditing and optimizing your SEO.</p>

        {error && <p className="text-error text-sm mb-4">{error}</p>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-secondaryText mb-1">Project Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full p-3 rounded-lg bg-secondary text-primaryText border border-border focus:outline-none focus:ring-2 focus:ring-primaryAccent"
              placeholder="e.g. My Blog Project"
              required
            />
          </div>

          <div>
            <label className="block text-secondaryText mb-1">Project Domain</label>
            <input
              type="url"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="w-full p-3 rounded-lg bg-secondary text-primaryText border border-border focus:outline-none focus:ring-2 focus:ring-primaryAccent"
              placeholder="e.g. https://example.com"
              required
            />
          </div>

          <button
            type="submit"
            className="w-full py-3 bg-primaryAccent hover:bg-accent-hover text-primaryText font-semibold rounded-lg transition"
          >
            Create Project
          </button>
        </form>
      </div>
    </div>
  );
}
