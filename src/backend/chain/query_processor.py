"""
Query Processing Module for RAG Pipeline

This module provides three levels of query preprocessing to improve retrieval quality:
1. BasicQueryProcessor: Simple text cleaning and normalization
2. EnhancedQueryProcessor: Adds keyword expansion and domain-specific improvements  
3. AdvancedQueryProcessor: Includes LLM-based query rewriting and decomposition

Each processor can be used independently or in combination with different reranking strategies.
"""

import re
import logging
from typing import List, Dict, Tuple
from abc import ABC, abstractmethod
import google.generativeai as genai


class BaseQueryProcessor(ABC):
    """Abstract base class for query processors"""
    
    @abstractmethod
    def process_query(self, query: str) -> str:
        """Process the input query and return the enhanced version"""
        pass
    
    @abstractmethod
    def get_version_info(self) -> Dict[str, str]:
        """Return information about this processor version"""
        pass


class BasicQueryProcessor(BaseQueryProcessor):
    """
    Version 1: Basic Query Processing
    
    Features:
    - Text cleaning and normalization
    - Basic spell correction for common terms
    - Simple query validation
    
    Use Case: When you want minimal processing overhead with basic improvements.
    """
    
    def __init__(self):
        # Domain-specific spell corrections for sustainability/circular economy
        self.spell_corrections = {
            'circularity': ['circualrity', 'circularity', 'circularty'],
            'sustainability': ['sustainabilty', 'sustanability', 'sustainibility'],
            'economy': ['econmy', 'economie', 'economi'],
            'waste': ['waist', 'wast'],
            'carbon': ['carbone', 'carbons'],
            'climate': ['climat', 'climte'],
            'recycling': ['recyling', 'recycing'],
            'emissions': ['emmisions', 'emisions'],
        }
        
        logging.info("BasicQueryProcessor initialized")
    
    def process_query(self, query: str) -> str:
        """
        Apply basic text cleaning and normalization.
        
        Args:
            query (str): Raw user query
            
        Returns:
            str: Cleaned and normalized query
        """
        # Step 1: Basic cleaning
        processed = query.strip().lower()
        
        # Step 2: Remove extra whitespace
        processed = re.sub(r'\s+', ' ', processed)
        
        # Step 3: Simple spell correction for domain terms
        for correct_term, variations in self.spell_corrections.items():
            for variation in variations:
                processed = re.sub(r'\b' + re.escape(variation) + r'\b', correct_term, processed, flags=re.IGNORECASE)
        
        # Step 4: Capitalize for better embedding matching
        processed = processed.capitalize()
        
        logging.debug(f"BasicQueryProcessor: '{query}' → '{processed}'")
        return processed
    
    def get_version_info(self) -> Dict[str, str]:
        return {
            "version": "1.0 - Basic",
            "features": "Text cleaning, normalization, basic spell correction",
            "overhead": "Minimal (~1ms)",
            "use_case": "Fast processing with basic improvements"
        }


class EnhancedQueryProcessor(BaseQueryProcessor):
    """
    Version 2: Enhanced Query Processing
    
    Features:
    - All BasicQueryProcessor features
    - Domain-specific keyword expansion
    - Synonym addition for better retrieval
    - Query type detection (factual, comparison, conceptual)
    
    Use Case: When you want better retrieval quality with moderate processing overhead.
    """
    
    def __init__(self):
        self.basic_processor = BasicQueryProcessor()
        
        # Domain-specific expansions for circular economy
        self.keyword_expansions = {
            'circularity gap': ['circular economy gap', 'circularity rate', 'material circularity', 'resource circularity'],
            'waste': ['waste management', 'waste reduction', 'waste streams', 'material waste'],
            'recycling': ['material recovery', 'resource recovery', 'waste recycling', 'circular materials'],
            'emissions': ['carbon emissions', 'greenhouse gas', 'CO2', 'carbon footprint'],
            'sustainability': ['sustainable development', 'environmental impact', 'ecological footprint'],
            'economy': ['economic impact', 'economic model', 'business model', 'economic system'],
            'resources': ['natural resources', 'material resources', 'raw materials', 'resource consumption'],
            'climate': ['climate change', 'global warming', 'environmental change', 'climate impact']
        }
        
        # Question type patterns
        self.question_patterns = {
            'factual': [r'\bwhat is\b', r'\bhow much\b', r'\bhow many\b', r'\bwhen did\b'],
            'comparison': [r'\bcompare\b', r'\bdifference\b', r'\bversus\b', r'\bvs\b', r'\bbetter\b', r'\bworse\b'],
            'conceptual': [r'\bwhy\b', r'\bhow does\b', r'\bexplain\b', r'\bwhat causes\b', r'\bwhat are the impacts\b'],
            'temporal': [r'\btrend\b', r'\bover time\b', r'\bchange\b', r'\bevolution\b', r'\bprogress\b']
        }
        
        logging.info("EnhancedQueryProcessor initialized")
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of question being asked"""
        query_lower = query.lower()
        
        for question_type, patterns in self.question_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return question_type
        
        return 'general'
    
    def _expand_keywords(self, query: str) -> str:
        """Expand domain-specific keywords with relevant synonyms"""
        expanded_terms = []
        
        for key_term, expansions in self.keyword_expansions.items():
            if key_term in query.lower():
                # Add the most relevant expansion (first one)
                expanded_terms.append(expansions[0])
        
        if expanded_terms:
            # Add expansions to the original query
            return f"{query} {' '.join(expanded_terms)}"
        
        return query
    
    def process_query(self, query: str) -> str:
        """
        Apply enhanced processing including keyword expansion and type detection.
        
        Args:
            query (str): Raw user query
            
        Returns:
            str: Enhanced query with expansions and improvements
        """
        # Step 1: Basic processing
        processed = self.basic_processor.process_query(query)
        
        # Step 2: Detect query type for future use
        query_type = self._detect_query_type(processed)
        
        # Step 3: Expand keywords
        processed = self._expand_keywords(processed)
        
        # Step 4: Add context for sustainability domain
        if query_type == 'factual' and len(processed.split()) < 5:
            processed = f"sustainability circular economy {processed}"
        
        logging.debug(f"EnhancedQueryProcessor: '{query}' → '{processed}' (type: {query_type})")
        return processed
    
    def get_version_info(self) -> Dict[str, str]:
        return {
            "version": "2.0 - Enhanced", 
            "features": "Basic features + keyword expansion, synonym addition, query type detection",
            "overhead": "Low (~5ms)",
            "use_case": "Better retrieval quality with moderate processing"
        }


class AdvancedQueryProcessor(BaseQueryProcessor):
    """
    Version 3: Advanced Query Processing
    
    Features:
    - All EnhancedQueryProcessor features
    - LLM-based query rewriting for better semantic matching
    - Complex query decomposition into sub-queries
    - Context-aware query enhancement
    
    Use Case: When you want maximum retrieval quality and can accept higher processing overhead.
    """
    
    def __init__(self, api_key: str = None):
        self.enhanced_processor = EnhancedQueryProcessor()
        
        # Initialize LLM for query rewriting
        if api_key:
            genai.configure(api_key=api_key)
            self.llm = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.llm = None
            logging.warning("AdvancedQueryProcessor: No API key provided, LLM features disabled")
        
        # Query rewriting prompt
        self.rewrite_prompt = """
You are a query optimization expert for a circular economy and sustainability document database.

Your task: Rewrite the user query to improve document retrieval while preserving the original intent.

Guidelines:
- Add relevant domain-specific terms (circular economy, sustainability, waste, emissions, etc.)
- Expand abbreviations and acronyms
- Include synonyms that might appear in academic/business documents
- Keep the core question clear and focused
- Limit to 2-3 sentences maximum

Original Query: {query}

Rewritten Query:"""
        
        logging.info("AdvancedQueryProcessor initialized")
    
    def _rewrite_query_with_llm(self, query: str) -> str:
        """Use LLM to rewrite query for better retrieval"""
        if not self.llm:
            return query
        
        try:
            prompt = self.rewrite_prompt.format(query=query)
            response = self.llm.generate_content(prompt)
            rewritten = response.text.strip()
            
            # Validate rewritten query isn't too long
            if len(rewritten.split()) > 50:
                logging.warning("LLM query rewrite too long, using enhanced version instead")
                return self.enhanced_processor.process_query(query)
            
            return rewritten
            
        except Exception as e:
            logging.error(f"Error in LLM query rewriting: {e}")
            # Fallback to enhanced processing
            return self.enhanced_processor.process_query(query)
    
    def _decompose_complex_query(self, query: str) -> List[str]:
        """
        Decompose complex queries into simpler sub-queries.
        For now, this is rule-based. Could be enhanced with LLM in the future.
        """
        # Detect compound questions
        compound_patterns = [
            r'\band\b',
            r'\bor\b', 
            r'\balso\b',
            r'\badditionally\b',
            r'\bfurthermore\b'
        ]
        
        is_compound = any(re.search(pattern, query.lower()) for pattern in compound_patterns)
        
        if is_compound and len(query.split()) > 15:
            # Simple decomposition by splitting on conjunctions
            sub_queries = re.split(r'\s+(?:and|or|also)\s+', query, flags=re.IGNORECASE)
            return [q.strip() for q in sub_queries if len(q.strip()) > 10]
        
        return [query]
    
    def process_query(self, query: str) -> str:
        """
        Apply advanced processing including LLM rewriting and decomposition.
        
        Args:
            query (str): Raw user query
            
        Returns:
            str: Advanced processed query optimized for retrieval
        """
        # Step 1: Enhanced processing first
        enhanced_query = self.enhanced_processor.process_query(query)
        
        # Step 2: Check for complex queries that need decomposition
        sub_queries = self._decompose_complex_query(enhanced_query)
        
        if len(sub_queries) > 1:
            # For compound queries, process the main one with LLM
            main_query = sub_queries[0]
            processed = self._rewrite_query_with_llm(main_query)
            logging.debug(f"AdvancedQueryProcessor: Decomposed into {len(sub_queries)} parts, processed main query")
        else:
            # Step 3: LLM-based query rewriting
            processed = self._rewrite_query_with_llm(enhanced_query)
        
        logging.debug(f"AdvancedQueryProcessor: '{query}' → '{processed}'")
        return processed
    
    def get_version_info(self) -> Dict[str, str]:
        return {
            "version": "3.0 - Advanced",
            "features": "Enhanced features + LLM query rewriting, complex query decomposition",
            "overhead": "Higher (~500ms)",
            "use_case": "Maximum retrieval quality for complex queries"
        }


class QueryProcessorFactory:
    """
    Factory class to create query processors.
    
    Usage:
        # Basic version
        processor = QueryProcessorFactory.create_processor("basic")
        
        # Enhanced version  
        processor = QueryProcessorFactory.create_processor("enhanced")
        
        # Advanced version (requires API key)
        processor = QueryProcessorFactory.create_processor("advanced", api_key="your_key")
    """
    
    @staticmethod
    def create_processor(version: str, api_key: str = None) -> BaseQueryProcessor:
        """
        Create a query processor of the specified version.
        
        Args:
            version (str): "basic", "enhanced", or "advanced"
            api_key (str, optional): Required for advanced processor
            
        Returns:
            BaseQueryProcessor: The requested processor instance
            
        Raises:
            ValueError: If version is invalid or API key is missing for advanced version
        """
        version = version.lower()
        
        if version == "basic":
            return BasicQueryProcessor()
        elif version == "enhanced":
            return EnhancedQueryProcessor()
        elif version == "advanced":
            if not api_key:
                raise ValueError("API key is required for AdvancedQueryProcessor")
            return AdvancedQueryProcessor(api_key=api_key)
        else:
            raise ValueError(f"Unknown processor version: {version}. Use 'basic', 'enhanced', or 'advanced'")
    
    @staticmethod
    def list_versions() -> Dict[str, Dict[str, str]]:
        """List all available processor versions with their info"""
        return {
            "basic": BasicQueryProcessor().get_version_info(),
            "enhanced": EnhancedQueryProcessor().get_version_info(),
            "advanced": AdvancedQueryProcessor().get_version_info()
        }


# Example usage and testing
if __name__ == "__main__":
    # Test queries
    test_queries = [
        "What is the circularity gap?",
        "How has waste managment changed over time?", 
        "Compare emissions between different economic models and explain the sustainability impact",
        "circualrity trends"
    ]
    
    print("=== Query Processing Comparison ===\n")
    
    for query in test_queries:
        print(f"Original: {query}")
        
        # Test basic processor
        basic = BasicQueryProcessor()
        basic_result = basic.process_query(query)
        print(f"Basic:    {basic_result}")
        
        # Test enhanced processor  
        enhanced = EnhancedQueryProcessor()
        enhanced_result = enhanced.process_query(query)
        print(f"Enhanced: {enhanced_result}")
        
        print("-" * 50)
