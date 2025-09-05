"""
Dynamic knowledge loader that learns from data instead of using hardcoded patterns.
"""

import json
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger
from collections import defaultdict, Counter


class DynamicKnowledgeLoader:
    """Dynamically load and learn domain knowledge from various sources."""
    
    def __init__(self):
        """Initialize the dynamic knowledge loader."""
        self.knowledge_cache = {}
        self.learned_patterns = defaultdict(dict)
        
    def load_from_samples(
        self, 
        data_samples: Union[List[Dict], pd.DataFrame],
        domain: str = "custom"
    ) -> Dict[str, Any]:
        """
        Learn patterns and knowledge from user-provided samples.
        
        Args:
            data_samples: Sample data to learn from
            domain: Domain category (healthcare, finance, custom)
            
        Returns:
            Learned knowledge structure
        """
        if isinstance(data_samples, list):
            df = pd.DataFrame(data_samples)
        else:
            df = data_samples
            
        knowledge = {
            "patterns": self._analyze_patterns(df),
            "distributions": self._calculate_distributions(df),
            "relationships": self._discover_relationships(df),
            "domain_specific": self._extract_domain_knowledge(df, domain)
        }
        
        # Cache the learned knowledge
        self.knowledge_cache[domain] = knowledge
        logger.info(f"Learned knowledge from {len(df)} samples for domain: {domain}")
        
        return knowledge
        
    def load_from_database(
        self,
        connection_string: str,
        query: str,
        domain: str = "custom"
    ) -> Dict[str, Any]:
        """
        Learn patterns directly from database.
        
        Args:
            connection_string: Database connection string
            query: SQL query to fetch data
            domain: Domain category
            
        Returns:
            Learned knowledge structure
        """
        # In production, this would connect to the database
        # For now, we'll create a placeholder
        logger.info(f"Loading knowledge from database for domain: {domain}")
        
        # Placeholder for database loading
        # Would use SQLAlchemy or similar to fetch data
        # df = pd.read_sql(query, connection_string)
        # return self.load_from_samples(df, domain)
        
        return {
            "status": "database_loading_placeholder",
            "domain": domain,
            "query": query
        }
        
    def load_from_api(
        self,
        api_endpoint: str,
        headers: Optional[Dict] = None,
        domain: str = "custom"
    ) -> Dict[str, Any]:
        """
        Learn patterns from API responses.
        
        Args:
            api_endpoint: API URL to fetch data
            headers: Optional headers for authentication
            domain: Domain category
            
        Returns:
            Learned knowledge structure
        """
        import requests
        
        try:
            response = requests.get(api_endpoint, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Convert to DataFrame if it's a list of records
            if isinstance(data, list):
                df = pd.DataFrame(data)
                return self.load_from_samples(df, domain)
            else:
                return {
                    "api_response": data,
                    "domain": domain
                }
        except Exception as e:
            logger.error(f"Failed to load from API: {str(e)}")
            return {"error": str(e)}
            
    def get_healthcare_knowledge(self, samples: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Get healthcare domain knowledge, either learned or generated.
        
        Args:
            samples: Optional sample data to learn from
            
        Returns:
            Healthcare-specific knowledge
        """
        if samples is not None:
            return self.load_from_samples(samples, "healthcare")
            
        # If no samples, return dynamic structure (not hardcoded values)
        return {
            "common_conditions": self._generate_dynamic_conditions(),
            "medication_patterns": self._generate_dynamic_medications(),
            "age_condition_correlation": self._generate_age_correlations(),
            "geographic_patterns": self._generate_geographic_patterns()
        }
        
    def get_finance_knowledge(self, samples: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Get finance domain knowledge, either learned or generated.
        
        Args:
            samples: Optional sample data to learn from
            
        Returns:
            Finance-specific knowledge
        """
        if samples is not None:
            return self.load_from_samples(samples, "finance")
            
        # If no samples, return dynamic structure (not hardcoded values)
        return {
            "spending_patterns": self._generate_spending_patterns(),
            "fraud_patterns": self._generate_fraud_patterns(),
            "credit_patterns": self._generate_credit_patterns(),
            "transaction_patterns": self._generate_transaction_patterns()
        }
        
    def _analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in the data."""
        patterns = {}
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                patterns[col] = {
                    "type": "numeric",
                    "range": [float(df[col].min()), float(df[col].max())],
                    "distribution": self._detect_distribution(df[col])
                }
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                patterns[col] = {
                    "type": "temporal",
                    "frequency": self._detect_temporal_frequency(df[col])
                }
            else:
                patterns[col] = {
                    "type": "categorical",
                    "unique_values": df[col].nunique(),
                    "top_values": df[col].value_counts().head(10).to_dict()
                }
                
        return patterns
        
    def _calculate_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate statistical distributions from data."""
        distributions = {}
        
        # Numeric distributions
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            distributions[col] = {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "median": float(df[col].median()),
                "quantiles": df[col].quantile([0.25, 0.5, 0.75]).to_dict()
            }
            
        # Categorical distributions
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            value_counts = df[col].value_counts()
            distributions[col] = {
                "frequencies": (value_counts / len(df)).to_dict(),
                "mode": value_counts.index[0] if not value_counts.empty else None
            }
            
        return distributions
        
    def _discover_relationships(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Discover relationships between columns."""
        relationships = {
            "correlations": {},
            "dependencies": {},
            "hierarchies": []
        }
        
        # Numeric correlations
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            corr_matrix = numeric_df.corr()
            significant_corr = {}
            
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.5:
                        pair = f"{corr_matrix.columns[i]}_{corr_matrix.columns[j]}"
                        significant_corr[pair] = float(corr_value)
                        
            relationships["correlations"] = significant_corr
            
        # Detect functional dependencies
        for col1 in df.columns:
            for col2 in df.columns:
                if col1 != col2:
                    if df.groupby(col1)[col2].nunique().max() == 1:
                        if col1 not in relationships["dependencies"]:
                            relationships["dependencies"][col1] = []
                        relationships["dependencies"][col1].append(col2)
                        
        return relationships
        
    def _extract_domain_knowledge(self, df: pd.DataFrame, domain: str) -> Dict[str, Any]:
        """Extract domain-specific knowledge from data."""
        domain_knowledge = {}
        
        if domain == "healthcare":
            # Look for healthcare-specific patterns
            for col in df.columns:
                col_lower = col.lower()
                if 'diagnosis' in col_lower or 'icd' in col_lower:
                    domain_knowledge["diagnosis_codes"] = df[col].value_counts().to_dict()
                elif 'medication' in col_lower or 'drug' in col_lower:
                    domain_knowledge["medications"] = df[col].value_counts().to_dict()
                elif 'procedure' in col_lower or 'cpt' in col_lower:
                    domain_knowledge["procedures"] = df[col].value_counts().to_dict()
                    
        elif domain == "finance":
            # Look for finance-specific patterns
            for col in df.columns:
                col_lower = col.lower()
                if 'transaction' in col_lower or 'amount' in col_lower:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        domain_knowledge["transaction_amounts"] = {
                            "min": float(df[col].min()),
                            "max": float(df[col].max()),
                            "typical_range": [
                                float(df[col].quantile(0.25)),
                                float(df[col].quantile(0.75))
                            ]
                        }
                elif 'category' in col_lower or 'merchant' in col_lower:
                    domain_knowledge["categories"] = df[col].value_counts().to_dict()
                    
        return domain_knowledge
        
    def _detect_distribution(self, series: pd.Series) -> str:
        """Detect the type of distribution in numeric data."""
        from scipy import stats
        
        # Simple distribution detection
        skewness = series.skew()
        kurtosis = series.kurtosis()
        
        if abs(skewness) < 0.5 and abs(kurtosis) < 0.5:
            return "normal"
        elif skewness > 1:
            return "right_skewed"
        elif skewness < -1:
            return "left_skewed"
        else:
            return "unknown"
            
    def _detect_temporal_frequency(self, series: pd.Series) -> str:
        """Detect temporal frequency in datetime data."""
        if len(series) < 2:
            return "single"
            
        sorted_series = series.sort_values()
        time_diffs = sorted_series.diff().dropna()
        
        if time_diffs.empty:
            return "unknown"
            
        # Check for common frequencies
        mean_diff = time_diffs.mean()
        
        if mean_diff.days > 300:
            return "yearly"
        elif mean_diff.days > 25:
            return "monthly"
        elif mean_diff.days > 5:
            return "weekly"
        elif mean_diff.days >= 1:
            return "daily"
        elif mean_diff.seconds > 3000:
            return "hourly"
        else:
            return "high_frequency"
            
    # Dynamic generation methods (replace hardcoded data)
    
    def _generate_dynamic_conditions(self) -> List[Dict[str, Any]]:
        """Generate dynamic condition patterns instead of hardcoded."""
        # This would be populated from actual data or external sources
        return []  # Empty by default, filled when data is provided
        
    def _generate_dynamic_medications(self) -> Dict[str, List]:
        """Generate dynamic medication patterns instead of hardcoded."""
        return {}  # Empty by default, filled when data is provided
        
    def _generate_age_correlations(self) -> Dict[str, List]:
        """Generate age-based correlations dynamically."""
        return {}  # Empty by default, filled when data is provided
        
    def _generate_geographic_patterns(self) -> Dict[str, Dict]:
        """Generate geographic patterns dynamically."""
        return {}  # Empty by default, filled when data is provided
        
    def _generate_spending_patterns(self) -> Dict[str, Any]:
        """Generate spending patterns dynamically."""
        return {"age_groups": {}, "seasonal": {}}  # Empty structure
        
    def _generate_fraud_patterns(self) -> Dict[str, Any]:
        """Generate fraud patterns dynamically."""
        return {
            "high_risk_categories": [],
            "time_patterns": {},
            "amount_patterns": {}
        }
        
    def _generate_credit_patterns(self) -> Dict[str, Any]:
        """Generate credit patterns dynamically."""
        return {"score_ranges": {}}  # Empty structure
        
    def _generate_transaction_patterns(self) -> Dict[str, Any]:
        """Generate transaction patterns dynamically."""
        return {
            "daily_patterns": {},
            "weekly_patterns": {},
            "monthly_patterns": {}
        }
        
    def merge_knowledge(self, *knowledge_sources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple knowledge sources.
        
        Args:
            *knowledge_sources: Variable number of knowledge dictionaries
            
        Returns:
            Merged knowledge structure
        """
        merged = {}
        
        for source in knowledge_sources:
            for key, value in source.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, dict) and isinstance(merged[key], dict):
                    merged[key].update(value)
                elif isinstance(value, list) and isinstance(merged[key], list):
                    merged[key].extend(value)
                else:
                    merged[key] = value
                    
        return merged
        
    def save_knowledge(self, knowledge: Dict[str, Any], filepath: str) -> None:
        """Save learned knowledge to file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(knowledge, f, indent=2, default=str)
            
        logger.info(f"Saved knowledge to {filepath}")
        
    def load_knowledge(self, filepath: str) -> Dict[str, Any]:
        """Load previously saved knowledge."""
        with open(filepath, 'r') as f:
            knowledge = json.load(f)
            
        logger.info(f"Loaded knowledge from {filepath}")
        return knowledge