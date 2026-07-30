class Player:
    """
    Represents an active player in the league.
    """
    def __init__(self, name="", votes_to=0):
        self.name = name
        self.votes_to = votes_to
        self.wins = 0
        self.avatar = ""

class Round:
    """
    Represents a round in the league.
    """
    def __init__(self, title, round_number, description, submissions):
        self.title = title
        self.round_number = round_number
        self.description = description
        self.submissions = submissions
        self.winner = self.determine_winner(submissions)
    
    def determine_winner(self, submissions):
        if not submissions:
            return []
            
        winners = []
        max_votes = submissions[0].votes
        
        for submission in submissions:
            if submission.votes == max_votes:
                winners.append(submission.player_name)
            else:
                break
                
        return winners

class Voter:
    """
    Represents a voter who casts votes in the league.
    """
    def __init__(self, name, votes, comment=""):
        self.name = name
        self.votes = votes
        self.comment = comment

class Song:
    """
    Represents a song submitted to a round.
    """
    def __init__(self, name, votes=0, player_name=None, artist=None, album=None, user_comment = None, voters=None):
        self.name = name
        self.artist = artist
        self.album = album
        self.player_name = player_name
        self.user_comment = user_comment
        self.votes = votes
        self.voters = voters if voters is not None else []

def convert_username_to_name(username, username_map = None):
    """
    Convert a username to a player name.
    
    Args:
        username (str): The username to convert
        players (list/dict): Collection or lookup of usernames to player names
        
    Returns:
        str: The corresponding player name, or the username if not found
    """
    if not username_map:
        return username
    
    return username_map.get(username, username)