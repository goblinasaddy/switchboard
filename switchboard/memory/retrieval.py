import time
from switchboard.types.memory import MemoryEntry, MemoryQuery

class MemoryRanker:
    """
    Ranks memory entries based on metadata tag overlap density, recency, and access counts.
    """

    def rank(self, entries: list[MemoryEntry], query: MemoryQuery) -> list[MemoryEntry]:
        """
        Sort and rank candidate memory entries.
        
        Args:
            entries: List of candidate MemoryEntry objects.
            query: MemoryQuery payload containing scoring parameters.
            
        Returns:
            Ranked list of MemoryEntry objects capped by query limit.
        """
        scored_entries: list[tuple[float, MemoryEntry]] = []
        now = time.time()
        
        for entry in entries:
            score = 0.0
            
            # 1. Tag Match Density Score (each matching tag adds 10 points)
            if query.tags and entry.tags:
                matching_tags_count = sum(1 for t in query.tags if t in entry.tags)
                score += matching_tags_count * 10.0
                
            # 2. Recency Boost (adds up to 2.0 points for very fresh entries)
            elapsed = max(0.0, now - entry.created_at)
            recency_boost = 2.0 / (1.0 + (elapsed / 3600.0))  # Decays over hours
            score += recency_boost
            
            # 3. Popularity Boost (frequently retrieved memories get up to 5 points boost)
            popularity_boost = min(5.0, entry.access_count * 0.2)
            score += popularity_boost
            
            scored_entries.append((score, entry))
            
        # Sort descending by score
        scored_entries.sort(key=lambda item: item[0], reverse=True)
        
        # Apply limit cap
        ranked = [item[1] for item in scored_entries]
        return ranked[:query.limit]
