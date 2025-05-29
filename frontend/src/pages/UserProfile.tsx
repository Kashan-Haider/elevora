import { useEffect, useState } from 'react';
import { useProjectStore } from '../../store/ProjectStore';
// import { Project } from '../types/audit';

export default function UserProfile() {
  const [user, setUser] = useState<any>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [error, setError] = useState('');
  const {
    selectedProject,
    setProject
  } = useProjectStore();

  useEffect(() => {
    const fetchUserAndProjects = async () => {
      const token = localStorage.getItem('access_token') || '';

      try {
        // Get user details
        const userRes = await fetch('http://localhost:8000/current-user', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!userRes.ok) throw new Error('Failed to load user');
        const userData = await userRes.json();
        setUser(userData.user);

        // Get projects
        const res = await fetch(`http://localhost:8000/get-all-projects?user_id=${userData.user.id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error('Failed to load projects');
        const projectData = await res.json();
        setProjects(projectData);

        // Set the latest project as default
        if (projectData.length > 0 && !selectedProject) {
          const latest = projectData[projectData.length - 1];
          setProject(latest);
        }
      } catch (err) {
        setError((err as Error).message);
      }
    };

    fetchUserAndProjects();
  }, [setProject, selectedProject]);

  return (
    <div className="min-h-screen bg-primary text-primaryText flex items-center justify-center px-4">
      <div className="max-w-3xl w-full bg-surface p-8 rounded-2xl shadow-xl border border-border">
        <h1 className="text-3xl font-semibold mb-4 text-primaryAccent">User Profile</h1>

        {error && <p className="text-error text-sm mb-4">{error}</p>}

        {user && (
          <div className="mb-6">
            <p><span className="text-secondaryText">Username:</span> {user.username}</p>
            <p><span className="text-secondaryText">Email:</span> {user.email}</p>
          </div>
        )}

        <div className="mb-6">
          <label className="block text-secondaryText mb-1">Select Project</label>
          <select
            onChange={(e) => {
              const project = projects.find((p) => p.id === e.target.value);
              if (project) setProject(project);
            }}
            value={selectedProject?.id || ''}
            className="w-full p-3 rounded-lg bg-secondary text-primaryText border border-border focus:outline-none focus:ring-2 focus:ring-primaryAccent"
          >
            <option value="" disabled>Select a project</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>

        {selectedProject?.name && (
          <p className="text-sm text-muted mt-2">
            Current project: <span className="text-primaryAccent font-medium">{selectedProject.name}</span>
          </p>
        )}
      </div>
    </div>
  );
}