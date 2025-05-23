import React, { useEffect, useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line,
} from 'recharts';
import { ArrowUp, ArrowDown, AlertCircle, CheckCircle, Info, Calendar, Globe, List } from 'lucide-react';

const ENDPOINT = 'http://localhost:8000/audit'; // your backend endpoint

// Interfaces remain the same
interface CategoryScore {
  category: string;
  percentage: number;
}

interface PageScore {
  url: string;
  percentage: number;
}

interface TimeSeries {
  timestamp: number;
  score: number;
}

interface Recommendation {
  count: number;
  recommendation: string;
}

interface IssuesByCategory {
  [category: string]: {
    [element: string]: Recommendation[];
  };
}

interface AuditData {
  category_scores: CategoryScore[];
  page_scores: PageScore[];
  time_series: TimeSeries;
  issues_by_category: IssuesByCategory;
}

// Mock data for development
const mockData = {
  category_scores: [
    { category: "Performance", percentage: 85 },
    { category: "SEO", percentage: 72 },
    { category: "Accessibility", percentage: 64 },
    { category: "Best Practices", percentage: 91 },
    { category: "Content", percentage: 78 }
  ],
  page_scores: [
    { url: "https://en.wikipedia.org/wiki/Muhammad_Ali_Jinnah", percentage: 86 },
    { url: "https://en.wikipedia.org/wiki/Pakistan_Movement", percentage: 74 },
    { url: "https://en.wikipedia.org/wiki/Partition_of_India", percentage: 68 }
  ],
  time_series: { timestamp: 1714918308, score: 76 },
  issues_by_category: {
    "performance": {
      "images": [
        { count: 3, recommendation: "Optimize image size and format" },
        { count: 2, recommendation: "Implement lazy loading for below-the-fold images" }
      ],
      "scripts": [
        { count: 4, recommendation: "Defer non-critical JavaScript" }
      ]
    },
    "seo": {
      "meta": [
        { count: 1, recommendation: "Missing meta description" },
        { count: 2, recommendation: "Improve title tags with primary keywords" }
      ],
      "content": [
        { count: 3, recommendation: "Add alt text to images" }
      ]
    },
    "accessibility": {
      "contrast": [
        { count: 5, recommendation: "Improve text contrast ratios" }
      ],
      "structure": [
        { count: 2, recommendation: "Use proper heading hierarchy" },
        { count: 1, recommendation: "Add ARIA labels to interactive elements" }
      ]
    }
  }
};

export default function AuditDashboard() {
  const [data, setData] = useState<AuditData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  useEffect(() => {
    // Simulate API call with mock data for demonstration
    // setTimeout(() => {
    //   setData(mockData);
    //   setLoading(false);
    //   setActiveCategory(Object.keys(mockData.issues_by_category)[0]);
    // }, 1000);
    
    // Uncomment below for actual API call
    
    const requestBody = {
      url: 'https://www.workspace.co.uk/content-hub/business-insight/20-top-uk-based-technology-blogs',
      max_urls_per_domain: 2,
      max_pages: 3,
    };
  
    fetch(ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then((json: { message: AuditData }) => {
        setData(json.message);
        setActiveCategory(Object.keys(json.message.issues_by_category)[0]);
        setLoading(false);
      })
      .catch((err: Error) => {
        console.error(err);
        setError(err);
        setLoading(false);
      });
    
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
        <p className="mt-4 text-gray-600 font-medium">Loading audit data...</p>
      </div>
    </div>
  );
  
  if (error) return (
    <div className="flex items-center justify-center h-screen bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-800 text-center mb-2">Error Loading Data</h2>
        <p className="text-gray-600 text-center">{error.message}</p>
        <button className="mt-6 w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-md transition duration-200">
          Retry
        </button>
      </div>
    </div>
  );

  if (!data) return null;

  const { category_scores, page_scores, issues_by_category } = data;

  // Format time series data
  const timestamp = new Date(data.time_series.timestamp * 1000);
  const formattedDate = timestamp.toLocaleDateString('en-US', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  });
  
  // Convert percentage to letter grade
  const getGrade = (score:number) => {
    if (score >= 90) return { grade: 'A', color: 'text-green-500' };
    if (score >= 80) return { grade: 'B', color: 'text-blue-500' };
    if (score >= 70) return { grade: 'C', color: 'text-yellow-500' };
    if (score >= 60) return { grade: 'D', color: 'text-orange-500' };
    return { grade: 'F', color: 'text-red-500' };
  };

  // Overall score is average of category scores
  const overallScore = Math.round(
    category_scores.reduce((sum, item) => sum + item.percentage, 0) / category_scores.length
  );
  const { grade, color } = getGrade(overallScore);

  // For pie chart
  const pieData = category_scores.map(({ category, percentage }) => ({ 
    name: category, 
    value: percentage,
    fill: getCategoryColor(category)
  }));

  // For bar chart
  const barData = page_scores.map(({ url, percentage }) => ({ 
    name: (() => {
        try {
          const pathname = new URL(url).pathname;
          const lastSegment = pathname.split('/').pop();
          return lastSegment ? lastSegment.replace(/_/g, ' ') : '';
        } catch (error) {
          console.error('Invalid URL:', url);
          return '';
        }
      })(),      
    score: percentage 
  }));

  // Generate time series data (normally would be from API)
  const lineData = [
    { time: "Jan", score: 52 },
    { time: "Feb", score: 58 },
    { time: "Mar", score: 61 },
    { time: "Apr", score: 67 },
    { time: formattedDate, score: data.time_series.score }
  ];

  function getCategoryColor(category: string): string {
    const colors: Record<string, string> = {
      "Performance": "#4ade80",      // green-400
      "SEO": "#60a5fa",              // blue-400
      "Accessibility": "#f97316",    // orange-500
      "Best Practices": "#8b5cf6",   // violet-500
      "Content": "#f59e0b",          // amber-500
      "default": "#94a3b8"           // slate-400
    };
  
    return colors[category] || colors["default"];
  }

  function getCategoryIcon(category:any) {
    switch(category.toLowerCase()) {
      case 'performance':
        return <ArrowUp className="h-5 w-5" />;
      case 'seo':
        return <Globe className="h-5 w-5" />;
      case 'accessibility':
        return <CheckCircle className="h-5 w-5" />;
      case 'best practices':
        return <CheckCircle className="h-5 w-5" />;
      case 'content':
        return <List className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  }

  // Count total issues
  const totalIssues = Object.values(issues_by_category).reduce((sum, categoryIssues) => {
    return sum + Object.values(categoryIssues).reduce((catSum, recommendations) => {
      return catSum + recommendations.reduce((recSum, rec) => recSum + rec.count, 0);
    }, 0);
  }, 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Dashboard Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">SEO Audit Dashboard</h1>
              <p className="text-gray-500">Last updated: {formattedDate}</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-gray-100 rounded-lg px-4 py-2 flex items-center">
                <Calendar className="h-5 w-5 text-gray-500 mr-2" />
                <span className="text-gray-700 font-medium">{formattedDate}</span>
              </div>
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition duration-200">
                Run New Audit
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Overall Score Card */}
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="px-6 py-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-gray-500 font-medium">Overall Score</h3>
                <span className={`text-lg font-bold ${color}`}>{grade}</span>
              </div>
              <div className="flex items-end justify-between">
                <div className="text-3xl font-bold text-gray-900">{overallScore}<span className="text-xl text-gray-500">%</span></div>
                <div className="flex items-center text-green-500">
                  <ArrowUp className="h-4 w-4 mr-1" />
                  <span className="text-sm font-medium">+8% from last audit</span>
                </div>
              </div>
              <div className="mt-4 bg-gray-200 h-2 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-400 to-blue-600" 
                  style={{ width: `${overallScore}%` }}
                ></div>
              </div>
            </div>
          </div>

          {/* Total Pages Card */}
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="px-6 py-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-gray-500 font-medium">Pages Audited</h3>
                <Globe className="h-5 w-5 text-blue-500" />
              </div>
              <div className="flex items-end justify-between">
                <div className="text-3xl font-bold text-gray-900">{page_scores.length}</div>
                <div className="text-sm text-gray-500">Pages</div>
              </div>
              <div className="mt-4">
                <div className="flex items-center text-sm text-gray-600">
                  <span className="font-medium">Primary URL:</span>
                  <span className="ml-1 truncate text-gray-500" style={{ maxWidth: "180px" }}>
                    {page_scores[0]?.url}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Issues Found Card */}
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="px-6 py-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-gray-500 font-medium">Issues Found</h3>
                <AlertCircle className="h-5 w-5 text-orange-500" />
              </div>
              <div className="flex items-end justify-between">
                <div className="text-3xl font-bold text-gray-900">{totalIssues}</div>
                <div className="flex items-center text-orange-500">
                  <ArrowDown className="h-4 w-4 mr-1" />
                  <span className="text-sm font-medium">-12% from last audit</span>
                </div>
              </div>
              <div className="mt-4">
                <div className="grid grid-cols-3 gap-2">
                  {Object.keys(issues_by_category).slice(0, 3).map(category => (
                    <button
                      key={category}
                      onClick={() => setActiveCategory(category)}
                      className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                        activeCategory === category 
                          ? 'bg-blue-100 text-blue-700' 
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {category}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Top Category Card */}
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="px-6 py-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-gray-500 font-medium">Best Category</h3>
                <CheckCircle className="h-5 w-5 text-green-500" />
              </div>
              
              {category_scores.length > 0 && (() => {
                const topCategory = [...category_scores].sort((a, b) => b.percentage - a.percentage)[0];
                return (
                  <>
                    <div className="flex items-end justify-between">
                      <div className="text-xl font-bold text-gray-900 capitalize">{topCategory.category}</div>
                      <div className="text-2xl font-bold text-green-500">{topCategory.percentage}%</div>
                    </div>
                    <div className="mt-4 bg-gray-200 h-2 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500" 
                        style={{ width: `${topCategory.percentage}%` }}
                      ></div>
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Category Scores Pie Chart */}
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="px-6 py-5 border-b border-gray-100">
              <div className="flex items-center">
                <Info className="h-5 w-5 text-blue-500 mr-2" />
                <h2 className="text-lg font-semibold text-gray-800">Category Score Distribution</h2>
              </div>
            </div>
            <div className="p-6">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={pieData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    innerRadius={60}
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `${value}%`} />
                  <Legend layout="vertical" verticalAlign="middle" align="right" />
                </PieChart>
              </ResponsiveContainer>
              
              <div className="mt-6 grid grid-cols-2 gap-4">
                {category_scores.map((item) => (
                  <div key={item.category} className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-2" 
                      style={{ backgroundColor: getCategoryColor(item.category) }}
                    ></div>
                    <span className="text-sm text-gray-700">{item.category}: </span>
                    <span className="text-sm font-semibold ml-1">{item.percentage}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Time Series Chart */}
          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="px-6 py-5 border-b border-gray-100">
              <div className="flex items-center">
                <ArrowUp className="h-5 w-5 text-blue-500 mr-2" />
                <h2 className="text-lg font-semibold text-gray-800">Audit Score Trend</h2>
              </div>
            </div>
            <div className="p-6">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={lineData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="time" stroke="#718096" />
                  <YAxis domain={[0, 100]} stroke="#718096" />
                  <Tooltip 
                    formatter={(value) => [`${value}%`, "Score"]}
                    contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }} 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="score" 
                    stroke="#3b82f6" 
                    strokeWidth={3}
                    dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                    activeDot={{ fill: '#1d4ed8', strokeWidth: 0, r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
              
              <div className="mt-4 flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  <span className="font-medium">Starting score:</span> 52%
                </div>
                <div className="text-sm text-green-500 font-medium flex items-center">
                  <ArrowUp className="h-4 w-4 mr-1" />
                  Improved by {data.time_series.score - 52}% since first audit
                </div>
                <div className="text-sm text-gray-500">
                  <span className="font-medium">Current score:</span> {data.time_series.score}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Page Scores Bar Chart */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden mb-8">
          <div className="px-6 py-5 border-b border-gray-100">
            <div className="flex items-center">
              <Globe className="h-5 w-5 text-blue-500 mr-2" />
              <h2 className="text-lg font-semibold text-gray-800">Page Performance Comparison</h2>
            </div>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                <XAxis 
                  dataKey="name" 
                  stroke="#718096"
                  angle={-45}
                  textAnchor="end"
                  tick={{ fontSize: 12 }}
                  height={70}
                />
                <YAxis stroke="#718096" domain={[0, 100]} />
                <Tooltip 
                  formatter={(value) => [`${value}%`, "Score"]}
                  contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }} 
                />
                <Bar 
                  dataKey="score" 
                  fill="#3b82f6" 
                  radius={[4, 4, 0, 0]}
                  barSize={40}
                >
                  {barData.map((entry, index) => {
                    const { color } = getGrade(entry.score);
                    const colorMap:any = {
                      'text-green-500': '#22c55e',
                      'text-blue-500': '#3b82f6', 
                      'text-yellow-500': '#eab308',
                      'text-orange-500': '#f97316',
                      'text-red-500': '#ef4444'
                    };
                    return <Cell key={`cell-${index}`} fill={colorMap[color] || '#3b82f6'} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              {barData.map((item, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                  <div className="truncate max-w-xs">
                    <span className="text-sm font-medium">{item.name}</span>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-bold ${getGrade(item.score).color}`}>
                    {item.score}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Issues and Recommendations */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <div className="px-6 py-5 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-800">Issues & Recommendations</h2>
          </div>
          
          {/* Category Tabs */}
          <div className="border-b border-gray-200">
            <div className="px-6 overflow-x-auto">
              <div className="flex space-x-4">
                {Object.keys(issues_by_category).map((category) => (
                  <button
                    key={category}
                    onClick={() => setActiveCategory(category)}
                    className={`py-3 font-medium text-sm border-b-2 transition-colors duration-200 capitalize whitespace-nowrap ${
                      activeCategory === category
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center">
                      {getCategoryIcon(category)}
                      <span className="ml-2">{category}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          {/* Issue Details */}
          {activeCategory && (
            <div className="px-6 py-6">
              <div className="space-y-6">
                {Object.entries(issues_by_category[activeCategory]).map(([element, recommendations]) => (
                  <div key={element} className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                      <h4 className="font-medium text-gray-800 capitalize">{element}</h4>
                    </div>
                    <ul className="divide-y divide-gray-200">
                      {recommendations.map((item, idx) => (
                        <li key={idx} className="p-4">
                          <div className="flex items-start">
                            <div className="flex-shrink-0 mt-0.5">
                              <div className="bg-orange-100 text-orange-600 text-xs font-bold px-2 py-1 rounded-md">
                                {item.count}x
                              </div>
                            </div>
                            <div className="ml-3">
                              <p className="text-gray-700">{item.recommendation}</p>
                              <p className="mt-1 text-sm text-gray-500">
                                {
                                  {
                                    'Optimize image size and format': 'Large images increase page load time. Compress and convert to WebP format.',
                                    'Implement lazy loading for below-the-fold images': 'Only load images when they enter the viewport to improve initial load time.',
                                    'Defer non-critical JavaScript': 'Move non-essential scripts to load after critical content.',
                                    'Missing meta description': 'Add descriptive meta descriptions to improve click-through rates from search results.',
                                    'Improve title tags with primary keywords': 'Include target keywords near the beginning of your title tags.',
                                    'Add alt text to images': 'Descriptive alt text helps search engines understand image content and improves accessibility.',
                                    'Improve text contrast ratios': 'Ensure text is readable against its background for all users.',
                                    'Use proper heading hierarchy': 'Follow H1-H6 structure to improve page semantics and accessibility.',
                                    'Add ARIA labels to interactive elements': 'Make interactive elements accessible to screen readers.'
                                  }[item.recommendation] || 'Fix this issue to improve overall performance.'
                                }
                              </p>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Dashboard Footer */}
      <footer className="bg-white border-t border-gray-200 mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <p className="text-gray-500 text-sm">SEO Audit Dashboard • Generated on {formattedDate}</p>
            <div className="flex items-center space-x-4">
              <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                Export Report (PDF)
              </button>
              <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                Schedule Next Audit
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}