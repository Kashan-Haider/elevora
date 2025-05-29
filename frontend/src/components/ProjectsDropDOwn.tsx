import { useEffect, useState } from 'react';
import { useProjectStore } from '../../store/ProjectStore';
import { Project } from '../types/audit';

export default function ProjectDropdown() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState("");
  const {
    selectedProjectId,
    selectedProjectName,
    setProject
  } = useProjectStore();

  useEffect(() => {
    const fetchProjects = async () => {
      const userId = localStorage.getItem("user_id");
      const token = localStorage.getItem("access_token") || "";
      if (!userId) return;

      try {
        const res = await fetch(`http://localhost:8000/get-all-projects?user_id=${userId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("Failed to load projects");
        const data = await res.json();
        setProjects(data);
        console.log(data)
      } catch (err) {
        setError((err as Error).message);
      }
    };

    fetchProjects();
  }, []);

  return (
    <div className="w-full max-w-sm mb-6">
      <label className="block text-secondaryText mb-1">Select Project</label>
      <select
        onChange={(e) => {
          const project:Project | undefined = projects.find((p: Project) => p.id === e.target.value);
          if (project) setProject(project.id , project.name);
        }}
        value={selectedProjectId || ''}
        className="w-full p-3 rounded-lg bg-secondary text-primaryText border border-border focus:outline-none focus:ring-2 focus:ring-primaryAccent"
      >
        <option value="" disabled>Select a project</option>
        {projects.map((project: any) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>

      {selectedProjectName && (
        <p className="text-sm text-muted mt-2">
          Current project: <span className="text-primaryAccent font-medium">{selectedProjectName}</span>
        </p>
      )}

      {error && <p className="text-error text-sm mt-2">{error}</p>}
    </div>
  );
}
