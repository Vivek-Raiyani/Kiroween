"""
SEO analysis service for video optimization.
"""
import re
from typing import Dict, List, Tuple, Any
from collections import Counter


class SEOAnalyzer:
    """Service for analyzing and optimizing video SEO."""
    
    # SEO scoring weights
    TITLE_WEIGHT = 0.30
    DESCRIPTION_WEIGHT = 0.25
    TAGS_WEIGHT = 0.20
    KEYWORDS_WEIGHT = 0.25
    
    # Optimal ranges
    OPTIMAL_TITLE_LENGTH = (50, 70)
    OPTIMAL_DESCRIPTION_LENGTH = (200, 5000)
    OPTIMAL_TAG_COUNT = (5, 15)
    
    # Common stop words to filter out
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'you', 'your', 'this', 'but', 'they',
        'have', 'had', 'what', 'when', 'where', 'who', 'which', 'why', 'how'
    }
    
    @classmethod
    def analyze_video(
        cls,
        title: str,
        description: str,
        tags: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze video metadata and generate SEO score.
        
        Args:
            title: Video title
            description: Video description
            tags: List of video tags
            
        Returns:
            Dictionary containing:
                - seo_score: Overall score (0-100)
                - title_score: Title optimization score
                - description_score: Description optimization score
                - tags_score: Tags optimization score
                - keywords_score: Keyword usage score
                - recommendations: List of improvement suggestions
        """
        title_score = cls._score_title(title)
        description_score = cls._score_description(description)
        tags_score = cls._score_tags(tags)
        keywords_score = cls._score_keywords(title, description, tags)
        
        # Calculate weighted overall score
        seo_score = int(
            title_score * cls.TITLE_WEIGHT +
            description_score * cls.DESCRIPTION_WEIGHT +
            tags_score * cls.TAGS_WEIGHT +
            keywords_score * cls.KEYWORDS_WEIGHT
        )
        
        # Generate recommendations
        recommendations = cls._generate_recommendations(
            title, description, tags,
            title_score, description_score, tags_score, keywords_score
        )
        
        return {
            'seo_score': seo_score,
            'title_score': title_score,
            'description_score': description_score,
            'tags_score': tags_score,
            'keywords_score': keywords_score,
            'recommendations': recommendations
        }
    
    @classmethod
    def suggest_keywords(cls, title: str, description: str) -> List[str]:
        """
        Suggest keyword improvements based on content analysis.
        
        Args:
            title: Video title
            description: Video description
            
        Returns:
            List of suggested keywords
        """
        # Extract keywords from title and description
        title_keywords = cls.extract_keywords(title)
        description_keywords = cls.extract_keywords(description)
        
        # Combine and prioritize
        all_keywords = title_keywords + description_keywords
        keyword_counts = Counter(all_keywords)
        
        # Get top keywords that appear multiple times
        suggested = [
            word for word, count in keyword_counts.most_common(10)
            if count > 1 or word in title_keywords
        ]
        
        return suggested[:10]
    
    @classmethod
    def check_title_length(cls, title: str) -> Tuple[bool, str]:
        """
        Check if title length is optimal for SEO.
        
        Args:
            title: Video title
            
        Returns:
            Tuple of (is_optimal, message)
        """
        length = len(title)
        min_len, max_len = cls.OPTIMAL_TITLE_LENGTH
        
        if length < min_len:
            return False, f"Title is too short ({length} chars). Aim for {min_len}-{max_len} characters."
        elif length > max_len:
            return False, f"Title is too long ({length} chars). Aim for {min_len}-{max_len} characters."
        else:
            return True, f"Title length is optimal ({length} chars)."
    
    @classmethod
    def check_description_structure(cls, description: str) -> Dict[str, Any]:
        """
        Check if description follows SEO best practices.
        
        Args:
            description: Video description
            
        Returns:
            Dictionary with structure analysis:
                - has_links: Whether description contains links
                - has_timestamps: Whether description contains timestamps
                - has_hashtags: Whether description contains hashtags
                - length_ok: Whether length is optimal
                - paragraph_count: Number of paragraphs
                - recommendations: List of suggestions
        """
        length = len(description)
        min_len, max_len = cls.OPTIMAL_DESCRIPTION_LENGTH
        
        # Check for various elements
        has_links = bool(re.search(r'https?://', description))
        has_timestamps = bool(re.search(r'\d{1,2}:\d{2}', description))
        has_hashtags = bool(re.search(r'#\w+', description))
        
        # Count paragraphs (separated by double newlines or single newlines)
        paragraphs = [p.strip() for p in description.split('\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        length_ok = min_len <= length <= max_len
        
        recommendations = []
        if not length_ok:
            if length < min_len:
                recommendations.append(f"Description is too short ({length} chars). Add more detail.")
            else:
                recommendations.append(f"Description is very long ({length} chars). Consider condensing.")
        
        if not has_links:
            recommendations.append("Add relevant links (social media, website, resources).")
        
        if not has_timestamps and length > 500:
            recommendations.append("Consider adding timestamps for longer videos.")
        
        if not has_hashtags:
            recommendations.append("Add 2-3 relevant hashtags for discoverability.")
        
        if paragraph_count < 2:
            recommendations.append("Break description into multiple paragraphs for readability.")
        
        return {
            'has_links': has_links,
            'has_timestamps': has_timestamps,
            'has_hashtags': has_hashtags,
            'length_ok': length_ok,
            'length': length,
            'paragraph_count': paragraph_count,
            'recommendations': recommendations
        }
    
    @classmethod
    def extract_keywords(cls, text: str) -> List[str]:
        """
        Extract meaningful keywords from text.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of extracted keywords
        """
        # Convert to lowercase and extract words
        text = text.lower()
        words = re.findall(r'\b[a-z]{3,}\b', text)
        
        # Filter out stop words
        keywords = [
            word for word in words
            if word not in cls.STOP_WORDS
        ]
        
        return keywords
    
    @classmethod
    def _score_title(cls, title: str) -> int:
        """Score title optimization (0-100)."""
        if not title:
            return 0
        
        score = 0
        length = len(title)
        min_len, max_len = cls.OPTIMAL_TITLE_LENGTH
        
        # Length score (40 points)
        if min_len <= length <= max_len:
            score += 40
        elif length < min_len:
            score += int(40 * (length / min_len))
        else:
            # Penalty for being too long
            excess = length - max_len
            score += max(0, 40 - (excess * 2))
        
        # Keyword presence (30 points)
        keywords = cls.extract_keywords(title)
        if keywords:
            score += min(30, len(keywords) * 10)
        
        # Capitalization (15 points) - check if title case or sentence case
        if title[0].isupper():
            score += 15
        
        # No excessive punctuation (15 points)
        punctuation_count = len(re.findall(r'[!?]{2,}', title))
        if punctuation_count == 0:
            score += 15
        
        return min(100, score)
    
    @classmethod
    def _score_description(cls, description: str) -> int:
        """Score description optimization (0-100)."""
        if not description:
            return 0
        
        score = 0
        length = len(description)
        min_len, max_len = cls.OPTIMAL_DESCRIPTION_LENGTH
        
        # Length score (30 points)
        if min_len <= length <= max_len:
            score += 30
        elif length < min_len:
            score += int(30 * (length / min_len))
        else:
            score += 30  # Long descriptions are okay
        
        # Has links (20 points)
        if re.search(r'https?://', description):
            score += 20
        
        # Has keywords (25 points)
        keywords = cls.extract_keywords(description)
        if keywords:
            score += min(25, len(keywords) * 2)
        
        # Has hashtags (15 points)
        hashtags = re.findall(r'#\w+', description)
        if hashtags:
            score += min(15, len(hashtags) * 5)
        
        # Paragraph structure (10 points)
        paragraphs = [p.strip() for p in description.split('\n') if p.strip()]
        if len(paragraphs) >= 2:
            score += 10
        
        return min(100, score)
    
    @classmethod
    def _score_tags(cls, tags: List[str]) -> int:
        """Score tags optimization (0-100)."""
        if not tags:
            return 0
        
        score = 0
        tag_count = len(tags)
        min_tags, max_tags = cls.OPTIMAL_TAG_COUNT
        
        # Tag count score (50 points)
        if min_tags <= tag_count <= max_tags:
            score += 50
        elif tag_count < min_tags:
            score += int(50 * (tag_count / min_tags))
        else:
            # Slight penalty for too many tags
            score += max(30, 50 - (tag_count - max_tags) * 2)
        
        # Tag quality (50 points)
        # Check for multi-word tags (more specific)
        multi_word_tags = [t for t in tags if ' ' in t.strip()]
        score += min(25, len(multi_word_tags) * 5)
        
        # Check for varied tag lengths (diversity)
        tag_lengths = [len(t) for t in tags]
        if tag_lengths:
            length_variance = max(tag_lengths) - min(tag_lengths)
            if length_variance > 5:
                score += 25
        
        return min(100, score)
    
    @classmethod
    def _score_keywords(cls, title: str, description: str, tags: List[str]) -> int:
        """Score keyword consistency across title, description, and tags (0-100)."""
        title_keywords = set(cls.extract_keywords(title))
        description_keywords = set(cls.extract_keywords(description))
        tag_keywords = set()
        for tag in tags:
            tag_keywords.update(cls.extract_keywords(tag))
        
        if not title_keywords:
            return 0
        
        score = 0
        
        # Keywords from title appear in description (40 points)
        title_in_desc = title_keywords.intersection(description_keywords)
        if title_keywords:
            overlap_ratio = len(title_in_desc) / len(title_keywords)
            score += int(40 * overlap_ratio)
        
        # Keywords from title appear in tags (40 points)
        title_in_tags = title_keywords.intersection(tag_keywords)
        if title_keywords:
            overlap_ratio = len(title_in_tags) / len(title_keywords)
            score += int(40 * overlap_ratio)
        
        # Bonus for having keywords across all three (20 points)
        all_three = title_keywords.intersection(description_keywords).intersection(tag_keywords)
        if all_three:
            score += min(20, len(all_three) * 10)
        
        return min(100, score)
    
    @classmethod
    def _generate_recommendations(
        cls,
        title: str,
        description: str,
        tags: List[str],
        title_score: int,
        description_score: int,
        tags_score: int,
        keywords_score: int
    ) -> List[str]:
        """Generate actionable SEO recommendations."""
        recommendations = []
        
        # Title recommendations
        if title_score < 70:
            is_optimal, msg = cls.check_title_length(title)
            if not is_optimal:
                recommendations.append(msg)
            
            if not cls.extract_keywords(title):
                recommendations.append("Add relevant keywords to your title.")
        
        # Description recommendations
        if description_score < 70:
            desc_check = cls.check_description_structure(description)
            recommendations.extend(desc_check['recommendations'])
        
        # Tags recommendations
        if tags_score < 70:
            tag_count = len(tags)
            min_tags, max_tags = cls.OPTIMAL_TAG_COUNT
            if tag_count < min_tags:
                recommendations.append(f"Add more tags (currently {tag_count}, aim for {min_tags}-{max_tags}).")
            elif tag_count > max_tags:
                recommendations.append(f"Consider reducing tags (currently {tag_count}, aim for {min_tags}-{max_tags}).")
        
        # Keyword consistency recommendations
        if keywords_score < 70:
            recommendations.append("Ensure keywords from title appear in description and tags.")
            
            # Suggest specific keywords
            suggested = cls.suggest_keywords(title, description)
            if suggested:
                recommendations.append(f"Consider using these keywords: {', '.join(suggested[:5])}")
        
        return recommendations
