export type Paper = {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  published: string;
  updated: string;
  primary_category: string;
  categories: string[];
  url: string;
  pdf_url: string;
};

export type Recommendation = {
  paper: Paper;
  relevance_score: number;
  priority: 'high' | 'medium' | 'low';
  matched_keywords: string[];
  matched_exclusions: string[];
  reason: string;
  summary: string;
  evidence: string[];
  risks: string[];
  matched_topics: string[];
  mismatch_topics: string[];
  confidence?: 'high' | 'medium' | 'low';
  paper_type?: string;
  recommended_action?: 'read_now' | 'skim' | 'save_for_later' | 'ignore';
  reading_status: string;
};

export type KnowledgeEntry = {
  paper: Paper;
  note: string;
  tags: string[];
  key_takeaways: string[];
  created_at: string;
  updated_at: string;
};

export type MetaPayload = {
  categories: Record<string, string>;
  reading_statuses: Record<string, string>;
  knowledge_base: Record<string, KnowledgeEntry>;
  default_model: string;
  ai_review_configured: boolean;
};

export type SearchPayload = {
  generated_at: string;
  config: Record<string, unknown>;
  recommendations: Recommendation[];
};

export type SearchRequest = {
  language: string;
  research_interest: string;
  positive_keywords: string;
  negative_keywords: string;
  categories: string[];
  days_back: number;
  max_results: number;
  query: string;
  use_ai_review: boolean;
  llm_max_items: number;
};
