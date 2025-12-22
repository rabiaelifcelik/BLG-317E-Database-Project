"""
Principals Model - 3NF Normalized
Characters field removed and moved to separate principal_characters table
One-to-Many relationship: One Principal can have Many Characters
"""

class Principals:
    def __init__(self, principal_id, title_id, ordering, name_id, category, job):
        """
        Initialize a Principal object (3NF normalized - characters removed)
        
        Args:
            principal_id (int): Unique identifier for the principal record
            title_id (str): Foreign key to titles (tconst)
            ordering (int): Billing order in credits
            name_id (str): Foreign key to people (nconst)
            category (str): Role category (actor, director, etc.)
            job (str): Specific job title
        
        Note: Characters are now stored in principal_characters table (3NF)
        """
        self.principal_id = principal_id
        self.title_id = title_id
        self.ordering = ordering
        self.name_id = name_id
        self.category = category
        self.job = job
        # characters is now in separate table: principal_characters
    
    def __repr__(self):
        return f"<Principal(id={self.principal_id}, category='{self.category}', title='{self.title_id}')>"
