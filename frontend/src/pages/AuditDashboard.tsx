import React, { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import {
  Award,
  AlertCircle,
  Globe,
  FileText,
  CheckCircle,
  ArrowUpRight,
  Calendar,
  AlertTriangle,
  Code,
  Link,
  Flag,
  ChevronDown,
  LayoutDashboard,
  AlertOctagon,
  TrendingUp,
  Shield,
  Eye,
  BookOpen,
  ExternalLink,
} from "lucide-react";
import { useProjectStore } from "../../store/ProjectStore";
import { MetricCard } from "../components/auditDashboard/MetricCard";
import { ScoreGauge } from "../components/auditDashboard/ScoreGuage";
import { PageCard } from "../components/auditDashboard/PageCard";
import { StatusIcon } from "../components/auditDashboard/StatusIcon";
import { TechnicalStatusGrid } from "../components/auditDashboard/TechnicalStatusGrid";
import {
  formatBytes,
  getScoreColor,
  getSeverityColor,
} from "../utils/formatters";
import type { AuditData, Page, ProjectDetails } from "../types/audit";
import { ScoreIndicator } from "../components/auditDashboard/ScoreIndicator";

const AuditDashboard: React.FC = () => {
  const [auditData, setAuditData] = useState<AuditData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [accessToken, setAccessToken] = useState<string>("");
  const [activeTab, setActiveTab] = useState<
    "overview" | "issues" | "pages" | "technical"
  >("overview");
  const [dropdownOpen, setDropdownOpen] = useState<boolean>(false);
  const [projectDropdownOpen, setProjectDropdownOpen] =
    useState<boolean>(false);
  const [selectedPage, setSelectedPage] = useState<Page | null>(null);

  const navigate = useNavigate();
  const [projects, setProjects] = useState<ProjectDetails[]>([]);
  const { selectedProject, setProject } = useProjectStore();

  useEffect(() => {
    const token = localStorage.getItem("access_token") || "";
    setAccessToken(token);
  }, []);

  useEffect(() => {
    const fetchUserAndProjects = async () => {
      const token = localStorage.getItem("access_token") || "";

      try {
        const userRes = await fetch("http://localhost:8000/current-user", {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!userRes.ok) throw new Error("Failed to load user");
        const userData = await userRes.json();

        const res = await fetch(
          `http://localhost:8000/get-all-projects?user_id=${userData.user.id}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        if (!res.ok) throw new Error("Failed to load projects");
        const projectData = await res.json();
        setProjects(projectData);

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

  useEffect(() => {
    const checkUserProjects = async () => {
      if (!accessToken) return;

      try {
        const res = await fetch("http://localhost:8000/has-project", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (!res.ok) {
          throw new Error("Failed to check user projects");
        }

        const has_project: boolean = await res.json();
        if (!has_project) {
          navigate("/get-started");
        }
      } catch (error) {
        console.error("Error checking user projects:", error);
        setError("Failed to verify user access");
      }
    };

    if (accessToken) {
      checkUserProjects();
    }
  }, [accessToken, navigate]);

  const fetchAuditData = useCallback(async (): Promise<void> => {
    if (!selectedProject?.id || !accessToken) {
      setError("No project selected or missing authentication");
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const baseUrl = "http://localhost:8000";

      const response = await fetch(
        `${baseUrl}/get-audit-data?project_id=${selectedProject.id}`,
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch audit data: ${response.status}`);
      }

      const data: AuditData = await response.json();
      setAuditData(data);

      if (data.pages && data.pages.length > 0) {
        setSelectedPage(data.pages[0]);
      }
    } catch (error) {
      console.error("Error fetching audit data:", error);
      setError(
        `Failed to load audit data: ${
          error instanceof Error ? error.message : "Unknown error"
        }`
      );
    } finally {
      setLoading(false);
    }
  }, [selectedProject?.id, accessToken]);

  useEffect(() => {
    if (selectedProject?.id && accessToken) {
      fetchAuditData();
    }
  }, [fetchAuditData]);

  const calculateAverageScore = (pages: Page[]): number => {
    if (pages.length === 0) return 0;
    const totalScore = pages.reduce(
      (sum, page) => sum + page.scores.overall,
      0
    );
    return Math.round(totalScore / pages.length);
  };

  const calculateSEOScore = (pages: Page[]): number => {
    if (pages.length === 0) return 0;
    const totalScore = pages.reduce((sum, page) => sum + page.scores.seo, 0);
    return Math.round(totalScore / pages.length);
  };

  const getTotalIssues = (pages: Page[]): number => {
    return pages.reduce((sum, page) => sum + page.page_info.issues_count, 0);
  };

  const getCriticalIssues = (pages: Page[]): number => {
    return pages.reduce(
      (sum, page) => sum + page.audit_details.summary.critical_issues,
      0
    );
  };

  const handleProjectChange = (project: ProjectDetails) => {
    setProject(project);
    setProjectDropdownOpen(false);
  };

  const handleTabChange = (
    tab: "overview" | "issues" | "pages" | "technical"
  ) => {
    setActiveTab(tab);
    setDropdownOpen(false);
  };

  const formatTabName = (tab: string) => {
    return tab.charAt(0).toUpperCase() + tab.slice(1);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-primary p-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primaryAccent"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-primary p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-secondary rounded-lg p-8 text-center">
            <AlertCircle className="h-12 w-12 text-rose-500 mx-auto mb-4" />
            <h3 className="text-2xl font-medium mb-2 text-white">
              Error Loading Dashboard
            </h3>
            <p className="text-secondaryText mb-6">{error}</p>
            <button
              onClick={fetchAuditData}
              className="bg-primaryAccent text-white px-5 py-2 rounded-lg hover:bg-primaryAccent/90 transition-colors"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!selectedProject) {
    return (
      <div className="min-h-screen bg-secondary p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-secondary rounded-lg p-8 text-center">
            <Globe className="h-12 w-12 text-secondaryText mx-auto mb-4" />
            <h3 className="text-2xl font-medium mb-2">No Project Selected</h3>
            <p className="text-secondaryText mb-6">
              Please select a project to view the SEO audit dashboard.
            </p>
            <button
              onClick={() => navigate("/projects")}
              className="bg-primaryAccent text-white px-5 py-2 rounded-lg hover:bg-primaryAccent/90 transition-colors"
            >
              Select Project
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!auditData || !auditData.pages || auditData.pages.length === 0) {
    return (
      <div className="min-h-screen bg-primary p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-secondary rounded-lg p-8 text-center">
            <AlertCircle className="h-12 w-12 text-amber-500 mx-auto mb-4" />
            <h3 className="text-2xl font-medium mb-2">
              No Audit Data Available
            </h3>
            <p className="text-secondaryText mb-6">
              Start by running an SEO audit on your project pages.
            </p>
            <button
              onClick={() => navigate("/audit")}
              className="bg-primaryAccent text-white px-5 py-2 rounded-lg hover:bg-primaryAccent/90 transition-colors"
            >
              Run Audit
            </button>
          </div>
        </div>
      </div>
    );
  }

  const averageScore = calculateAverageScore(auditData.pages);
  const seoScore = calculateSEOScore(auditData.pages);
  const totalIssues = getTotalIssues(auditData.pages);
  const criticalIssues = getCriticalIssues(auditData.pages);

  return (
    <div className="min-h-screen bg-primary pb-12">
      {/* Header Section */}
      <div className="bg-secondary">
        <div className="max-w-7xl mx-auto p-6">
          <div className="md:flex md:items-center md:justify-between">
            <div className="min-w-0 flex-1">
              <h1 className="text-2xl font-bold text-primaryText sm:text-3xl sm:tracking-tight">
                SEO Audit Dashboard
              </h1>
              <p className="mt-1 text-sm text-secondaryText">
                Comprehensive technical SEO analysis and performance monitoring
              </p>
            </div>
            <div className="mt-4 flex md:ml-4 md:mt-0 items-center">
              {/* Project Dropdown */}
              <div className="relative mr-3">
                <button
                  onClick={() => setProjectDropdownOpen(!projectDropdownOpen)}
                  className="inline-flex items-center gap-x-1 rounded-md bg-secondary px-3 py-2 text-sm font-semibold text-primaryText ring-1 ring-inset ring-border hover:bg-surface"
                >
                  <span className="truncate max-w-[150px]">
                    {selectedProject.name}
                  </span>
                  <ChevronDown
                    className={`h-4 w-4 transition-transform ${
                      projectDropdownOpen ? "rotate-180" : ""
                    }`}
                    aria-hidden="true"
                  />
                </button>
                {projectDropdownOpen && (
                  <div className="absolute right-0 z-10 mt-2 w-56 origin-top-right rounded-md bg-secondary shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                    <div className="py-1 max-h-[350px] overflow-auto">
                      {projects.map((project) => (
                        <button
                          key={project.id}
                          onClick={() => handleProjectChange(project)}
                          className={`block w-full text-left px-4 py-2 text-sm ${
                            selectedProject.id === project.id
                              ? "bg-primaryAccent/10 text-primaryAccent"
                              : "text-primaryText hover:bg-surface"
                          }`}
                        >
                          {project.name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={() => navigate("/audit")}
                className="inline-flex items-center rounded-md bg-primaryAccent px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primaryAccent/90 focus:outline-none transition-colors"
              >
                <ArrowUpRight className="-ml-0.5 mr-1.5 h-4 w-4" />
                Run New Audit
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="my-5">
        <div className="max-w-7xl mx-auto px-6 py-2">
          <div className="flex justify-between items-center">
            <div className="relative inline-block text-left">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="inline-flex items-center gap-x-1 rounded-md bg-secondary px-3 py-2 text-sm font-semibold text-primaryText ring-1 ring-inset ring-border hover:bg-surface"
              >
                <div className="flex items-center">
                  {activeTab === "overview" && (
                    <LayoutDashboard className="h-5 w-5 mr-2" />
                  )}
                  {activeTab === "issues" && (
                    <AlertOctagon className="h-5 w-5 mr-2" />
                  )}
                  {activeTab === "pages" && <Globe className="h-5 w-5 mr-2" />}
                  {activeTab === "technical" && (
                    <Code className="h-5 w-5 mr-2" />
                  )}
                  <span>{formatTabName(activeTab)}</span>
                  {activeTab === "issues" && totalIssues > 0 && (
                    <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-rose-500/20 text-rose-500">
                      {totalIssues}
                    </span>
                  )}
                </div>
                <ChevronDown
                  className={`h-4 w-4 transition-transform ${
                    dropdownOpen ? "rotate-180" : ""
                  }`}
                  aria-hidden="true"
                />
              </button>
              {dropdownOpen && (
                <div className="absolute left-0 z-10 mt-2 w-56 origin-top-left rounded-md bg-secondary shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
                  <div className="py-1">
                    <button
                      onClick={() => handleTabChange("overview")}
                      className={`flex w-full items-center px-4 py-2 text-sm ${
                        activeTab === "overview"
                          ? "bg-primaryAccent/10 text-primaryAccent"
                          : "text-primaryText hover:bg-surface"
                      }`}
                    >
                      <LayoutDashboard className="h-4 w-4 mr-2" />
                      Overview
                    </button>
                    <button
                      onClick={() => handleTabChange("issues")}
                      className={`flex w-full items-center px-4 py-2 text-sm ${
                        activeTab === "issues"
                          ? "bg-primaryAccent/10 text-primaryAccent"
                          : "text-primaryText hover:bg-surface"
                      }`}
                    >
                      <AlertOctagon className="h-4 w-4 mr-2" />
                      Issues & Recommendations
                      {totalIssues > 0 && (
                        <span className="ml-2 px-2 py-0.5 text-xs rounded-full bg-rose-500/20 text-rose-500">
                          {totalIssues}
                        </span>
                      )}
                    </button>
                    <button
                      onClick={() => handleTabChange("pages")}
                      className={`flex w-full items-center px-4 py-2 text-sm ${
                        activeTab === "pages"
                          ? "bg-primaryAccent/10 text-primaryAccent"
                          : "text-primaryText hover:bg-surface"
                      }`}
                    >
                      <Globe className="h-4 w-4 mr-2" />
                      Pages Analysis
                    </button>
                    <button
                      onClick={() => handleTabChange("technical")}
                      className={`flex w-full items-center px-4 py-2 text-sm ${
                        activeTab === "technical"
                          ? "bg-primaryAccent/10 text-primaryAccent"
                          : "text-primaryText hover:bg-surface"
                      }`}
                    >
                      <Code className="h-4 w-4 mr-2" />
                      Technical Details
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="hidden md:flex items-center space-x-4">
              <div className="flex items-center text-sm text-secondaryText">
                <Calendar className="h-4 w-4 mr-1" />
                Last audit:{" "}
                {new Date(
                  auditData.pages[0]?.page_info.last_audited
                ).toLocaleDateString()}
              </div>
              <div className="flex items-center text-sm text-secondaryText">
                <CheckCircle className="h-4 w-4 mr-1" />
                {auditData.pages.length} pages analyzed
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pt-6">
        {/* Overview Tab */}
        {activeTab === "overview" && (
          <>
            {/* Top Stats and Score */}
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 mb-8">
              {/* Score Gauge */}
              <div className="lg:col-span-1 bg-secondary rounded-lg border border-border p-6 flex flex-col items-center justify-center shadow-sm hover:shadow-md transition-shadow">
                <h3 className="text-lg font-semibold text-primaryText mb-4">
                  Overall Score
                </h3>
                <ScoreGauge value={averageScore} size="lg" label="SEO HEALTH" />
                <div className="mt-4 text-center">
                  <p className="text-sm text-secondaryText">
                    SEO Score:{" "}
                    <span className={`font-medium ${getScoreColor(seoScore)}`}>
                      {seoScore}/100
                    </span>
                  </p>
                </div>
              </div>

              {/* Stats Cards */}
              <div className="lg:col-span-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  title="Pages Analyzed"
                  value={auditData.pages.length}
                  description={`${auditData.project.total_pages} total pages`}
                  icon={<Globe className="h-5 w-5" />}
                />
                <MetricCard
                  title="Total Issues"
                  value={totalIssues}
                  description={`${criticalIssues} critical issues`}
                  icon={<AlertTriangle className="h-5 w-5" />}
                  color={
                    criticalIssues > 0
                      ? "error"
                      : totalIssues > 0
                      ? "warning"
                      : "success"
                  }
                />
                <MetricCard
                  title="Average Score"
                  value={`${averageScore}/100`}
                  description="Technical SEO health"
                  icon={<Award className="h-5 w-5" />}
                  color={
                    averageScore >= 80
                      ? "success"
                      : averageScore >= 60
                      ? "warning"
                      : "error"
                  }
                />
                <MetricCard
                  title="Total Checks"
                  value={auditData.pages.reduce(
                    (sum, page) =>
                      sum + page.audit_details.summary.total_checks,
                    0
                  )}
                  description="Comprehensive analysis"
                  icon={<CheckCircle className="h-5 w-5" />}
                />
              </div>
            </div>

            {/* Project Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-secondary rounded-lg p-5 border border-border shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-secondaryText">
                      Passed Tests
                    </p>
                    <p className="text-2xl font-bold text-emerald-500">
                      {auditData.pages.reduce(
                        (sum, page) => sum + page.audit_details.summary.passed,
                        0
                      )}
                    </p>
                  </div>
                  <CheckCircle className="h-8 w-8 text-emerald-500" />
                </div>
              </div>

              <div className="bg-secondary rounded-lg p-5 border border-border shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-secondaryText">
                      Warnings
                    </p>
                    <p className="text-2xl font-bold text-amber-500">
                      {auditData.pages.reduce(
                        (sum, page) =>
                          sum + page.audit_details.summary.warnings,
                        0
                      )}
                    </p>
                  </div>
                  <AlertTriangle className="h-8 w-8 text-amber-500" />
                </div>
              </div>

              <div className="bg-secondary rounded-lg p-5 border border-border shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-secondaryText">
                      Critical Issues
                    </p>
                    <p className="text-2xl font-bold text-rose-500">
                      {criticalIssues}
                    </p>
                  </div>
                  <AlertCircle className="h-8 w-8 text-rose-500" />
                </div>
              </div>

              <div className="bg-secondary rounded-lg p-5 border border-border shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-secondaryText">
                      Recommendations
                    </p>
                    <p className="text-2xl font-bold text-primaryAccent">
                      {auditData.pages.reduce(
                        (sum, page) =>
                          sum +
                          page.audit_details.summary.total_recommendations,
                        0
                      )}
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-primaryAccent" />
                </div>
              </div>
            </div>

            {/* Pages Performance Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* Pages List */}
              <div className="bg-secondary rounded-lg border border-border">
                <div className="p-6 border-b border-border">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-primaryText">
                      Pages Performance
                    </h3>
                    <div className="flex items-center text-sm text-secondaryText">
                      <Eye className="h-4 w-4 mr-1" />
                      {auditData.pages.length} pages
                    </div>
                  </div>
                </div>
                <div className="p-0">
                  <div className="max-h-96 overflow-y-auto custom-scrollbar">
                    {auditData.pages.map((page) => (
                      <PageCard
                        key={page.page_info.id}
                        page={page}
                        onClick={() => setSelectedPage(page)}
                        isSelected={
                          selectedPage?.page_info.id === page.page_info.id
                        }
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Selected Page Details */}
              {selectedPage && (
                <div className="bg-secondary rounded-lg border border-border">
                  <div className="p-6 border-b border-border">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-primaryText">
                        Page Analysis
                      </h3>
                      <a
                        href={selectedPage.page_info.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primaryAccent hover:text-primaryAccent/80 transition-colors"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                    <p className="text-sm text-secondaryText mt-1 truncate">
                      {selectedPage.page_info.url}
                    </p>
                  </div>
                  <div className="p-6 space-y-6">
                    {/* Score Section */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center">
                        <ScoreIndicator
                          score={selectedPage.scores.overall}
                          label="Overall Score"
                        />
                      </div>
                      <div className="text-center">
                        <ScoreIndicator
                          score={selectedPage.scores.seo}
                          label="SEO Score"
                        />
                      </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-secondaryText">
                            Word Count
                          </span>
                          <span className="text-sm font-medium text-primaryText">
                            {selectedPage.content_analysis.word_count.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-secondaryText">
                            Page Size
                          </span>
                          <span className="text-sm font-medium text-primaryText">
                            {formatBytes(
                              selectedPage.page_info.page_size_bytes
                            )}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-secondaryText">
                            Total Links
                          </span>
                          <span className="text-sm font-medium text-primaryText">
                            {selectedPage.links_analysis.total}
                          </span>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-secondaryText">
                            Images
                          </span>
                          <span className="text-sm font-medium text-primaryText">
                            {selectedPage.images_analysis.total}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-secondaryText">
                            Alt Text
                          </span>
                          <span className="text-sm font-medium text-primaryText">
                            {selectedPage.images_analysis.alt_percentage.toFixed(
                              1
                            )}
                            %
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-secondaryText">
                            Issues
                          </span>
                          <span className="text-sm font-medium text-rose-500">
                            {selectedPage.page_info.issues_count}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Technical Status */}
                    <div className="space-y-3">
                      <h4 className="text-sm font-medium text-primaryText">
                        Technical Status
                      </h4>
                      <TechnicalStatusGrid
                        technicalSEO={selectedPage.technical_seo}
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Content Analysis Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Content Quality */}
              <div className="bg-secondary rounded-lg border border-border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-primaryText">
                    Content Quality
                  </h3>
                  <BookOpen className="h-5 w-5 text-primaryAccent" />
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-secondaryText">
                      Avg Word Count
                    </span>
                    <span className="text-sm font-medium text-primaryText">
                      {Math.round(
                        auditData.pages.reduce(
                          (sum, page) => sum + page.content_analysis.word_count,
                          0
                        ) / auditData.pages.length
                      ).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-secondaryText">
                      Avg Text/HTML Ratio
                    </span>
                    <span className="text-sm font-medium text-primaryText">
                      {(
                        auditData.pages.reduce(
                          (sum, page) =>
                            sum + page.content_analysis.text_html_ratio,
                          0
                        ) / auditData.pages.length
                      ).toFixed(1)}
                      %
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-secondaryText">
                      Total Paragraphs
                    </span>
                    <span className="text-sm font-medium text-primaryText">
                      {auditData.pages.reduce(
                        (sum, page) =>
                          sum + page.content_analysis.paragraphs_count,
                        0
                      )}
                    </span>
                  </div>
                </div>
              </div>

              {/* Links Analysis */}
              <div className="bg-secondary rounded-lg border border-border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-primaryText">
                    Links Analysis
                  </h3>
                  <Link className="h-5 w-5 text-primaryAccent" />
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-secondaryText">
                      Total Links
                    </span>
                    <span className="text-sm font-medium text-primaryText">
                      {auditData.pages.reduce(
                        (sum, page) => sum + page.links_analysis.total,
                        0
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-secondaryText">
                      Internal Links
                    </span>
                    <span className="text-sm font-medium text-primaryText">
                      {auditData.pages.reduce(
                        (sum, page) => sum + page.links_analysis.internal,
                        0
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-secondaryText">
                      External Links
                    </span>
                    <span className="text-sm font-medium text-primaryText">
                      {auditData.pages.reduce(
                        (sum, page) => sum + page.links_analysis.external,
                        0
                      )}
                    </span>
                  </div>
                </div>
              </div>

              {/* Technical Overview */}
              <div className="bg-secondary rounded-lg border border-border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-primaryText">
                    Technical Health
                  </h3>
                  <Shield className="h-5 w-5 text-primaryAccent" />
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-secondaryText">
                      HTTPS Enabled
                    </span>
                    <span className="text-sm font-medium text-emerald-500">
                      {
                        auditData.pages.filter(
                          (page) => page.technical_seo.has_https
                        ).length
                      }
                      /{auditData.pages.length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-secondaryText">
                      Mobile Friendly
                    </span>
                    <span className="text-sm font-medium text-emerald-500">
                      {
                        auditData.pages.filter(
                          (page) => page.technical_seo.has_mobile_friendly
                        ).length
                      }
                      /{auditData.pages.length}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-secondaryText">
                      Structured Data
                    </span>
                    <span className="text-sm font-medium text-primaryText">
                      {auditData.pages.reduce(
                        (sum, page) =>
                          sum + page.technical_seo.structured_data_count,
                        0
                      )}{" "}
                      schemas
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Issues Tab */}
        {activeTab === "issues" && (
          <div className="space-y-6">
            {/* Issues Summary */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-secondary rounded-lg p-4 border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-secondaryText">Critical</p>
                    <p className="text-2xl font-bold text-rose-500">
                      {criticalIssues}
                    </p>
                  </div>
                  <AlertOctagon className="h-8 w-8 text-rose-500" />
                </div>
              </div>
              <div className="bg-secondary rounded-lg p-4 border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-secondaryText">High Priority</p>
                    <p className="text-2xl font-bold text-orange-500">
                      {auditData.pages.reduce(
                        (sum, page) =>
                          sum +
                          page.audit_details.issues.filter(
                            (issue) => issue.severity === "high"
                          ).length,
                        0
                      )}
                    </p>
                  </div>
                  <AlertTriangle className="h-8 w-8 text-orange-500" />
                </div>
              </div>
              <div className="bg-secondary rounded-lg p-4 border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-secondaryText">
                      Medium Priority
                    </p>
                    <p className="text-2xl font-bold text-amber-500">
                      {auditData.pages.reduce(
                        (sum, page) =>
                          sum +
                          page.audit_details.issues.filter(
                            (issue) => issue.severity === "medium"
                          ).length,
                        0
                      )}
                    </p>
                  </div>
                  <Flag className="h-8 w-8 text-amber-500" />
                </div>
              </div>
              <div className="bg-secondary rounded-lg p-4 border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-secondaryText">Low Priority</p>
                    <p className="text-2xl font-bold text-emerald-500">
                      {auditData.pages.reduce(
                        (sum, page) =>
                          sum +
                          page.audit_details.issues.filter(
                            (issue) => issue.severity === "low"
                          ).length,
                        0
                      )}
                    </p>
                  </div>
                  <CheckCircle className="h-8 w-8 text-emerald-500" />
                </div>
              </div>
            </div>

            {/* Issues List by Page */}
            {auditData.pages.map((page) => (
              <div
                key={page.page_info.id}
                className="bg-secondary rounded-lg border border-border"
              >
                <div className="p-6 border-b border-border">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-primaryText">
                        {page.page_info.title || "Untitled Page"}
                      </h3>
                      <p className="text-sm text-secondaryText">
                        {page.page_info.url}
                      </p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(
                          page.scores.overall
                        )} bg-opacity-10`}
                      >
                        Score: {page.scores.overall}/100
                      </span>
                      <span className="px-2 py-1 rounded-full text-xs font-medium text-rose-500 bg-rose-500/10">
                        {page.page_info.issues_count} issues
                      </span>
                    </div>
                  </div>
                </div>
                <div className="p-6">
                  {page.audit_details.issues.length > 0 ? (
                    <div className="space-y-4">
                      {page.audit_details.issues.map((issue, issueIndex) => (
                        <div
                          key={`${issue.id}-${issueIndex}`}
                          className="border border-border rounded-lg p-4"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center space-x-2">
                              <StatusIcon status={issue.status} />
                              <h4 className="font-medium text-primaryText">
                                {issue.metric_name}
                              </h4>
                              {issue.severity && (
                                <span
                                  className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(
                                    issue.severity
                                  )} bg-opacity-10`}
                                >
                                  {issue.severity?.toUpperCase()}
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-secondaryText">
                              {issue.category} / {issue.subcategory}
                            </div>
                          </div>
                          <p className="text-sm text-secondaryText mb-3">
                            {issue.message}
                          </p>
                          {issue.recommendations &&
                            issue.recommendations.length > 0 && (
                              <div className="mt-3 p-3 bg-primaryAccent/5 rounded-lg">
                                <h5 className="font-medium text-primaryText text-sm mb-2">
                                  Recommendations:
                                </h5>
                                <ul className="list-disc list-inside space-y-1">
                                  {issue.recommendations.map(
                                    (rec, recIndex) => (
                                      <li
                                        key={recIndex}
                                        className="text-sm text-secondaryText"
                                      >
                                        {rec}
                                      </li>
                                    )
                                  )}
                                </ul>
                              </div>
                            )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <CheckCircle className="h-12 w-12 text-emerald-500 mx-auto mb-3" />
                      <p className="text-primaryText font-medium">
                        No issues found!
                      </p>
                      <p className="text-secondaryText text-sm">
                        This page passed all SEO checks.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pages Tab */}
        {activeTab === "pages" && (
          <div className="space-y-6">
            {/* Pages Grid */}
            <div className="grid grid-cols-1 gap-6">
              {auditData.pages.map((page) => (
                <div
                  key={page.page_info.id}
                  className="bg-secondary rounded-lg border border-border overflow-hidden"
                >
                  <div className="p-6 border-b border-border">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <div
                            className={`w-4 h-4 rounded-full ${getScoreColor(
                              page.scores.overall
                            ).replace("text-", "bg-")}`}
                          ></div>
                          <h3 className="text-lg font-semibold text-primaryText truncate">
                            {page.page_info.title || "Untitled Page"}
                          </h3>
                        </div>
                        <p className="text-sm text-secondaryText mt-1 truncate">
                          {page.page_info.url}
                        </p>
                      </div>
                      <div className="flex items-center space-x-3">
                        <div className="text-center">
                          <div
                            className={`text-2xl font-bold ${getScoreColor(
                              page.scores.overall
                            )}`}
                          >
                            {page.scores.overall}
                          </div>
                          <div className="text-xs text-secondaryText">
                            OVERALL
                          </div>
                        </div>
                        <div className="text-center">
                          <div
                            className={`text-2xl font-bold ${getScoreColor(
                              page.scores.seo
                            )}`}
                          >
                            {page.scores.seo}
                          </div>
                          <div className="text-xs text-secondaryText">SEO</div>
                        </div>
                        <a
                          href={page.page_info.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primaryAccent hover:text-primaryAccent/80 transition-colors"
                        >
                          <ExternalLink className="h-5 w-5" />
                        </a>
                      </div>
                    </div>
                  </div>

                  <div className="p-6">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      {/* Content Analysis */}
                      <div className="space-y-4">
                        <h4 className="font-semibold text-primaryText flex items-center">
                          <FileText className="h-4 w-4 mr-2" />
                          Content Analysis
                        </h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              Word Count
                            </span>
                            <span className="text-sm font-medium text-primaryText">
                              {page.content_analysis.word_count.toLocaleString()}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              Text/HTML Ratio
                            </span>
                            <span className="text-sm font-medium text-primaryText">
                              {page.content_analysis.text_html_ratio.toFixed(1)}
                              %
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              Paragraphs
                            </span>
                            <span className="text-sm font-medium text-primaryText">
                              {page.content_analysis.paragraphs_count}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              Page Size
                            </span>
                            <span className="text-sm font-medium text-primaryText">
                              {formatBytes(page.page_info.page_size_bytes)}
                            </span>
                          </div>
                        </div>

                        {/* Headings Distribution */}
                        <div className="mt-4">
                          <h5 className="text-sm font-medium text-primaryText mb-2">
                            Headings Structure
                          </h5>
                          <div className="grid grid-cols-3 gap-2">
                            {Object.entries(page.content_analysis.headings)
                              .filter(
                                ([key]) =>
                                  key.startsWith("h") &&
                                  typeof page.content_analysis.headings[
                                    key as keyof typeof page.content_analysis.headings
                                  ] === "number"
                              )
                              .map(([level, count]) => (
                                <div
                                  key={level}
                                  className="text-center p-2 bg-surface rounded"
                                >
                                  <div className="text-sm font-medium text-primaryText">
                                    {count}
                                  </div>
                                  <div className="text-xs text-secondaryText uppercase">
                                    {level}
                                  </div>
                                </div>
                              ))}
                          </div>
                        </div>
                      </div>

                      {/* Links & Images */}
                      <div className="space-y-4">
                        <h4 className="font-semibold text-primaryText flex items-center">
                          <Link className="h-4 w-4 mr-2" />
                          Links & Images
                        </h4>
                        <div className="space-y-3">
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              Total Links
                            </span>
                            <span className="text-sm font-medium text-primaryText">
                              {page.links_analysis.total}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              Internal
                            </span>
                            <span className="text-sm font-medium text-primaryText">
                              {page.links_analysis.internal}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              External
                            </span>
                            <span className="text-sm font-medium text-primaryText">
                              {page.links_analysis.external}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              Total Images
                            </span>
                            <span className="text-sm font-medium text-primaryText">
                              {page.images_analysis.total}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              With Alt Text
                            </span>
                            <span className="text-sm font-medium text-emerald-500">
                              {page.images_analysis.with_alt} (
                              {page.images_analysis.alt_percentage.toFixed(1)}%)
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-sm text-secondaryText">
                              Missing Alt
                            </span>
                            <span className="text-sm font-medium text-rose-500">
                              {page.images_analysis.without_alt}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Technical SEO */}
                      <div className="space-y-4">
                        <h4 className="font-semibold text-primaryText flex items-center">
                          <Shield className="h-4 w-4 mr-2" />
                          Technical SEO
                        </h4>
                        <TechnicalStatusGrid
                          technicalSEO={page.technical_seo}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Technical Tab */}
        {activeTab === "technical" && selectedPage && (
          <div className="space-y-8">
            {/* Metadata Checks */}
            <section className="bg-secondary rounded-lg border border-border p-6">
              <h3 className="text-lg font-semibold text-primaryText mb-4">
                Meta & Tags
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedPage.audit_details.metadata.canonical?.map((item) => (
                  <div key={item.id} className="flex items-center space-x-2">
                    <StatusIcon status={item.status} />
                    <span className="text-sm text-primaryText">
                      {item.metric_name}
                    </span>
                  </div>
                ))}
                {selectedPage.audit_details.metadata.meta_description?.map(
                  (item) => (
                    <div key={item.id} className="flex items-center space-x-2">
                      <StatusIcon status={item.status} />
                      <span className="text-sm text-primaryText">
                        {item.metric_name}
                      </span>
                    </div>
                  )
                )}
                {selectedPage.audit_details.metadata.title?.map((item) => (
                  <div key={item.id} className="flex items-center space-x-2">
                    <StatusIcon status={item.status} />
                    <span className="text-sm text-primaryText">
                      {item.metric_name}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            {/* Content Checks */}
            <section className="bg-secondary rounded-lg border border-border p-6">
              <h3 className="text-lg font-semibold text-primaryText mb-4">
                Content Analysis
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedPage.audit_details.content.headings?.map((item) =>
                  item.metric_name ? (
                    <div key={item.id} className="flex items-center space-x-2">
                      <StatusIcon status={item.status} />
                      <span className="text-sm text-primaryText">
                        {item.metric_name}
                      </span>
                    </div>
                  ) : (
                    <></>
                  )
                )}
                <div className="flex items-center space-x-2">
                  {selectedPage.audit_details.content.text_html_ratio
                    .metric_name ? (
                    <div>
                      <StatusIcon
                        status={
                          selectedPage.audit_details.content.text_html_ratio
                            .status
                        }
                      />
                      <span className="text-sm text-primaryText">
                        {
                          selectedPage.audit_details.content.text_html_ratio
                            .metric_name
                        }
                      </span>
                    </div>
                  ) : (
                    <></>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  {selectedPage.audit_details.content.word_count.metric_name ? (
                    <div>
                      <StatusIcon
                        status={
                          selectedPage.audit_details.content.word_count.status
                        }
                      />
                      <span className="text-sm text-primaryText">
                        {
                          selectedPage.audit_details.content.word_count
                            .metric_name
                        }
                      </span>
                    </div>
                  ) : (
                    <></>
                  )}
                </div>
              </div>
            </section>

            {/* Technical Checks */}
            <section className="bg-secondary rounded-lg border border-border p-6">
              <h3 className="text-lg font-semibold text-primaryText mb-4">
                Technical SEO Checks
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedPage.audit_details.technical.mobile_friendly.map(
                  (item) => (
                    <div key={item.id} className="flex items-center space-x-2">
                      <StatusIcon status={item.status} />
                      <span className="text-sm text-primaryText">
                        {item.metric_name}
                      </span>
                    </div>
                  )
                )}
                {selectedPage.audit_details.technical.page_speed_indicators?.map(
                  (item) => (
                    <div key={item.id} className="flex items-center space-x-2">
                      <StatusIcon status={item.status} />
                      <span className="text-sm text-primaryText">
                        {item.metric_name}
                      </span>
                    </div>
                  )
                )}
                {selectedPage.audit_details.technical.structured_data?.map(
                  (item) => (
                    <div key={item.id} className="flex items-center space-x-2">
                      <StatusIcon status={item.status} />
                      <span className="text-sm text-primaryText">
                        {item.metric_name}
                      </span>
                    </div>
                  )
                )}
                {selectedPage.audit_details.technical.security?.map((item) => (
                  <div key={item.id} className="flex items-center space-x-2">
                    <StatusIcon status={item.status} />
                    <span className="text-sm text-primaryText">
                      {item.metric_name}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            {/* Links Checks */}
            {selectedPage.audit_details.links.internal_links && selectedPage.audit_details.links.external_links ? (
              <div>
                <section className="bg-secondary rounded-lg border border-border p-6">
                  <h3 className="text-lg font-semibold text-primaryText mb-4">
                    Link Checks
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {selectedPage.audit_details.links.internal_links.json_value?.map(
                      (link: any, i: number) => (
                        <div key={i} className="text-sm text-secondaryText">
                          • {link.href} (
                          {link.has_text ? "with text" : "no text"})
                        </div>
                      )
                    )}
                    {selectedPage.audit_details.links.external_links.json_value?.map(
                      (link: any, i: number) => (
                        <div key={i} className="text-sm text-secondaryText">
                          • {link.href} ({link.nofollow ? "nofollow" : "follow"}
                          )
                        </div>
                      )
                    )}
                  </div>
                </section>
              </div>
            ) : (
              <></>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditDashboard;
