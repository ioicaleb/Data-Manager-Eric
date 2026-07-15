class Player_Defunct:
    """
    Represents a defunct player (player who has left the league).
    
    This class is used to track players who have left the league but may still
    have songs in the system for historical purposes.
    """
    def __init__(self):
        self.name = ""
        self.songs = []

class Player:
    """
    Represents an active player in the league.
    
    Attributes:
        name (str): The player's name
        votes_to (int): The number of votes this player has given to others
        wins (int): The number of rounds this player has won
    """
    def __init__(self, name="", votes_to=0):
        self.name = name
        self.votes_to = votes_to
        self.wins = 0

class Round:
    """
    Represents a round in the league.
    
    A round consists of multiple song submissions, with a winner determined
    based on the number of votes each submission received.
    
    Attributes:
        title (str): The title of the round
        round_number (int): The round number
        description (str): A description of the round
        submissions (list): List of Song objects submitted for this round
        winner (list): List of player names who won this round
    """
    def __init__(self, title, round_number, description, submissions):
        self.title = title
        self.round_number = round_number
        self.description = description
        self.submissions = submissions
        self.winner = self.determine_winner(submissions)
    
    def determine_winner(self, submissions):
        """
        Determine the winner(s) of the round based on votes.
        
        The winner is determined by finding all submissions with the maximum
        number of votes. If multiple submissions have the same maximum votes,
        all are considered winners.
        
        Args:
            submissions (list): List of Song objects for this round
            
        Returns:
            list: List of player names who won this round
        """
        if not submissions:
            return []
            
        winners = []
        max_votes = submissions[0].votes
        
        # Find all submissions with maximum votes
        for submission in submissions:
            if submission.votes == max_votes:
                winners.append(submission.player_name)
            else:
                break
                
        return winners

class Voter:
    """
    Represents a voter who casts votes in the league.
    
    Attributes:
        name (str): The voter's name
        votes (int): The number of votes this voter has cast
        comment (str): Any additional comment from the voter
    """
    def __init__(self, name, votes, comment=""):
        self.name = name
        self.votes = votes
        self.comment = comment

class Song:
    """
    Represents a song submitted to a round.
    
    Attributes:
        name (str): The name of the song
        artist (str): The artist of the song
        album (str): The album the song is from
        player_name (str): The name of the player who submitted the song
        votes (int): The total number of votes the song received
        voters (list): List of Voter objects who voted for this song
    """
    def __init__(self, name, votes=0, player_name=None, artist=None, album=None, voters=[]):
        self.name = name
        self.artist = artist
        self.album = album
        self.player_name = player_name
        self.votes = votes
        self.voters = voters

def convert_username_to_name(username, active_players, defunct_players=None, name=""):
    """
    Convert a username to a player name.
    
    This function attempts to find the corresponding player name for a given
    username, checking both active and defunct players.
    
    Args:
        username (str): The username to convert
        active_players (list): List of tuples (username, player_name) for active players
        defunct_players (list, optional): List of defunct player objects
        name (str): The name of the song to search for in defunct players
        
    Returns:
        str: The corresponding player name, or "[Left the League]" if not found
    """
    # Check active players first
    for player in active_players:
        if username == player[0]:
            return player[1]
    
    # If defunct players and song name are provided, check defunct players
    if defunct_players and name:
        for player in defunct_players:
            # Check if the song name exists in this player's songs
            if next((s for s in player["songs"] if name == s), None):
                return player["name"]
    
    # Return default if no match found
    return "[Left the League]"