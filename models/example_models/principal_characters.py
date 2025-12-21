"""
Principal Characters Model - 3NF Normalized Structure
One-to-Many relationship: One Principal can have Many Characters
"""

class PrincipalCharacter:
    def __init__(self, character_id, principal_id, character_name):
        """
        Initialize a Principal Character object (3NF normalized)
        
        Args:
            character_id (int): Unique identifier for the character record
            principal_id (int): Foreign key to principals table
            character_name (str): Name of the character played
        """
        self.character_id = character_id
        self.principal_id = principal_id
        self.character_name = character_name
    
    def __repr__(self):
        return f"<PrincipalCharacter(id={self.character_id}, principal={self.principal_id}, name='{self.character_name}')>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'character_id': self.character_id,
            'principal_id': self.principal_id,
            'character_name': self.character_name
        }
