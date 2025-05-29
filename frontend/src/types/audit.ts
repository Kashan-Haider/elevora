export interface HeadingData {
  text: string;
  length: number;
}

export interface Headings {
  h1: number;
  h2: number;
  h3: number;
  h4: number;
  h5: number;
  h6: number;
  data: {
    h1: HeadingData[];
    h2: HeadingData[];
    h3: HeadingData[];
    h4: HeadingData[];
    h5: HeadingData[];
    h6: HeadingData[];
  };
}

export interface ContentAnalysis {
  word_count: number;
  text_html_ratio: number;
  paragraphs_count: number;
  headings: Headings;
}

export interface LinksAnalysis {
  total: number;
  internal: number;
  external: number;
  internal_with_text_percentage: number;
  external_with_nofollow_percentage: number;
}

export interface ImagesAnalysis {
  total: number;
  with_alt: number;
  without_alt: number;
  alt_percentage: number;
}

export interface TechnicalSEO {
  has_https: boolean;
  has_viewport_meta: boolean;
  has_mobile_friendly: boolean;
  has_favicon: boolean;
  has_doctype: boolean;
  has_structured_data: boolean;
  structured_data_count: number;
  canonical_matches_url: boolean;
}

export interface AuditDetailItem {
  id: string;
  category: string;
  subcategory: string;
  metric_name: string;
  metric_value: number | null;
  text_value: string | null;
  boolean_value: boolean | null;
  json_value: any;
  status: string;
  severity: string | null;
  score: number | null;
  max_score: number | null;
  recommendations: string[];
  details: { recommendations: string[]; status?: string } | null;
  message: string;
  created_at: string;
}

export interface KeywordInfo {
  count: number;
  density: number;
}

export interface LinkDetail {
  href: string;
  text: string;
  text_length: number;
  title: string;
  nofollow: boolean;
  has_text: boolean;
}

export interface AuditDetails {
  summary: {
    total_checks: number;
    critical_issues: number;
    warnings: number;
    passed: number;
    total_recommendations: number;
    overall_score: number;
    seo_score: number;
    health_status: string;
  };
  metadata: {
    canonical: AuditDetailItem[];
    meta_description: AuditDetailItem[];
    open_graph: AuditDetailItem[];
    other_meta_tags: AuditDetailItem[];
    title: AuditDetailItem[];
    twitter_cards: AuditDetailItem[];
  };
  content: {
    content_quality: AuditDetailItem[];
    headings: AuditDetailItem[];
    keyword_analysis: AuditDetailItem & { json_value: { [key: string]: KeywordInfo } };
    keyword_optimization: AuditDetailItem[];
    text_html_ratio: AuditDetailItem;
    word_count: AuditDetailItem;
  };
  technical: {
    mobile_friendly: AuditDetailItem[];
    mobile_optimization: AuditDetailItem;
    page_speed_indicators: AuditDetailItem[];
    performance: AuditDetailItem;
    security: AuditDetailItem[];
    structured_data: AuditDetailItem[];
  };
  links: {
    canonical: AuditDetailItem[];
    external_links: AuditDetailItem & { json_value: LinkDetail[] };
    internal_links: AuditDetailItem & { json_value: LinkDetail[] };
  };
  international?: {
    language_setup: AuditDetailItem[];
  };
  performance?: {};
  accessibility?: {};
  issues: AuditDetailItem[];
  recommendations: {
    category: string;
    subcategory: string;
    recommendation: string;
    priority: string;
  }[];
  all_details: AuditDetailItem[];
}

export interface PageInfo {
  id: string;
  url: string;
  title: string;
  meta_description: string | null;
  last_audited: string;
  word_count: number;
  page_size_bytes: number;
  total_links: number;
  total_images: number;
  issues_count: number;
  opportunities_count: number;
}

export interface Scores {
  overall: number;
  seo: number;
}

export interface Page {
  page_info: PageInfo;
  scores: Scores;
  content_analysis: ContentAnalysis;
  links_analysis: LinksAnalysis;
  images_analysis: ImagesAnalysis;
  technical_seo: TechnicalSEO;
  audit_details: AuditDetails;
}

export interface Project {
  id: string;
  name: string;
  total_pages: number;
}

export interface ProjectDetails {
  id: string;
  name: string;
  domain: string;
  created_at: string;
  user_id: string;
}

export interface AuditData {
  project: Project;
  pages: Page[];
}